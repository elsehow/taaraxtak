import logging
import requests
import numpy as np
import pandas as pd
from os import path
from bs4 import BeautifulSoup


# types
from psycopg2.extensions import cursor
from typing import Optional

from src.w3techs.types import ProviderMarketshare
from src.w3techs.types import PopWeightedGini

#
# Scrape utilities
#


def get_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find("table", {"class": "bars"})


def get_provider_name(row):
    provider = row.find('a', recursive=False, href=True)
    if provider:
        return {
            'name': provider.contents[0],
            'url': provider['href'],
        }


def get_provider_names(rows):
    provider_names = []
    for row in rows:
        n = get_provider_name(row)
        if n:
            provider_names.append(n)
    return provider_names


def p2f(percentage_str):
    return float(percentage_str.strip('%'))/100


def get_marketshares(rows):
    provider_marketshares = []
    for row in rows:
        try:
            perc = row.contents[0]
            if perc.endswith('%'):
                provider_marketshares.append(p2f(perc))
        except (TypeError): # TODO - what is this error protecting against?
            logging.warning(f'Cannot extract marketshare from row.')
            pass
    return provider_marketshares


def get_marketshares_ssl(table):
    marketshares = []
    marketshare_rows = table.find_all("div", {"class": "bar2"})
    for row in marketshare_rows:
        perc = row.find_parent('tr').findChildren('td')[1].contents[0]
        marketshares.append(p2f(perc))
    return marketshares


def extract_table(html: str, double_table: bool = False) -> pd.DataFrame:
    # get request to w3techs; parse html
    table = get_table(html)

    #
    # get names of providers from parsed html
    #
    provider_name_rows = table.findChildren('th', recursive=True)

    # put them in a dataframe
    providers = pd.DataFrame(get_provider_names(provider_name_rows))

    #
    # get percentage marketshares of providers from parse html
    #
    marketshare_rows = table.findChildren('td', recursive=True)

    # combine them into a dataframe
    if double_table:
        providers['marketshare'] = get_marketshares_ssl(table)
    else:
        providers['marketshare'] = get_marketshares(marketshare_rows)
    return providers


def scrape_w3techs_table(w3techs: dict) -> pd.DataFrame:
    # read our config
    w3techs_url = w3techs['url']
    try:
        is_double_table = w3techs['double_table']
    except (KeyError):
        is_double_table = False
    # fetch the HTML
    html = requests.get(w3techs_url).text
    # parse the HTML
    return extract_table(html, double_table=is_double_table)

#
# Data marshalling utilities
#


def relative_path_to(*args):
    dirname = path.dirname(__file__)
    return path.join(dirname, *args)


provider_countries = pd.read_csv(
    relative_path_to('analysis', 'providers_labeled.csv')
).set_index('name').drop(['notes', 'url'], axis=1)
provider_countries = provider_countries['country (alpha2)'].to_dict()


def get_country(provider_name: str) -> str:
    '''
    Returns alpha2 code (str of length 2).
    '''
    try:
        alpha2 = provider_countries[provider_name]
        if len(alpha2) == 2:
            return alpha2
        return None
    except (TypeError):
        logging.info(f'Country code for {provider_name} is not a string: {alpha2}')
        return None
    except (KeyError):
        logging.info(f'Cannot find country for {provider_name}')
        return None


def extract_from_row(market: str, time: pd.Timestamp, df_row: pd.Series) -> ProviderMarketshare:
    '''
    Takes a row of a scraped dataframe and returns ProviderMarketshare.
    `market` and `time` are the first parameters because we partially apply them.
    '''
    name, url, marketshare = df_row.values
    jurisdiction = get_country(name)
    # NOTE - This type does ALL the validation.
    # Once data is in this type, it *should* be trustworthy.
    # See /design-notes.md for more detail on this pattern.
    return ProviderMarketshare(
        str(name), str(url), jurisdiction, market, float(marketshare), time
    )


#
# Population-weighted gini tools
# TODO Break into a different file?
#
prop_net_users = pd.read_csv(relative_path_to('analysis', 'prop_net_users.csv')).set_index('alpha2')


def to_df(db_rows) -> pd.DataFrame:
    # TODO put this in TYPES somehow?
    db_rows = pd.DataFrame(db_rows, columns=['name', 'url', 'jurisdiction_alpha2', 'market', 'marketshare', 'time'])
    return db_rows


def fetch_rows(cur: cursor, market: str, date: pd.Timestamp) -> pd.DataFrame:
    # TODO why this window? a magic number.
    cur.execute(f'''
        SELECT * from provider_marketshare
        WHERE market = '{market}'
        AND time BETWEEN timestamp '{date}' - interval '24 hour' AND  '{date}'
    ''')
    return to_df(cur.fetchall())


def fetch_by_jurisdiction(cur: cursor, market: str, date: pd.Timestamp) -> pd.DataFrame:
    '''
    Get a DataFrame mapping alpha2 codes to (mean) marketshares on a given date.
    '''
    rows = fetch_rows(cur, market, date)
    rows['marketshare'] = rows['marketshare'].astype(float)
    # in case we have the same name and jurisidiction repeated, we take the median marketshare
    rows = rows.groupby(['name', 'jurisdiction_alpha2']).median()
    # then group by each jurisdiction and take the sum of its marketshare
    rows = rows.groupby('jurisdiction_alpha2').sum()
    return rows


def gini(array: np.array) -> float:
    """
    Calculate the Gini coefficient of a numpy array.
    from https://github.com/oliviaguest/gini/
    """
    # based on bottom eq:
    # http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    # from:
    # http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1, array.shape[0]+1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))


def weighted_gini(marketshares: pd.Series, population_shares: pd.Series) -> float:
    '''
    Produce a gini in which marketshares are weighted by share of the population.
    '''
    weighted = marketshares / population_shares
    vs = weighted.fillna(0).values
    return gini(vs)


def population_weighted_gini(cur: cursor, market: str, time: pd.Timestamp) -> Optional[PopWeightedGini]:
    by_juris = fetch_by_jurisdiction(cur, market, time)
    # if there are no values, None
    if len(by_juris) == 0:
        return None

    # TODO break out JUST this and test it with some mock data?
    # get current % of Internet using population
    relevant_year = str(time.year)
    pop_share_df = prop_net_users[relevant_year]
    # weight marketshare
    merged = pd.DataFrame(pop_share_df).merge(by_juris,
                                              left_index=True,
                                              right_on='jurisdiction_alpha2',
                                              how='left')
    # we include countries that do  NOT appear in our scraped data.
    # the intention here is to get the gini among ALL countries,
    # including those that provide no internet services.
    g = weighted_gini(
        merged['marketshare'],
        merged[relevant_year],
    )
    return PopWeightedGini(market, g, time)
