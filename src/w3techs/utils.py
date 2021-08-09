import requests
import numpy as np
import pandas as pd
from os import path
from bs4 import BeautifulSoup
import src.shared.utils as shared_utils
import src.shared.types as shared_types

# types
from psycopg2.extensions import cursor
from typing import Optional
from typing import List
from bs4.element import NavigableString
from bs4.element import Tag
from bs4.element import ResultSet

from src.w3techs.types import ProviderMarketshare
from src.w3techs.types import PopWeightedGini

#
# Scrape utilities
#


def get_table(html: str) -> Tag:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find("table", {"class": "bars"})


def get_provider_name(row):
    provider = row.find('a', recursive=False, href=True)
    if provider:
        return {
            'name': provider.contents[0],
            'url': provider['href'],
        }


def get_provider_names(rows: ResultSet) -> List[str]:
    provider_names = []
    for row in rows:
        n = get_provider_name(row)
        if n:
            provider_names.append(n)
    return provider_names


def p2f(percentage_str: str) -> float:
    return float(percentage_str.strip('%'))/100


def get_marketshares(marketshare_rows: Tag) -> List[float]:
    provider_marketshares = []
    for row in marketshare_rows:
        content = row.contents[0]
        # if the contents are a string that ends with %
        if (type(content) == NavigableString) and (content.endswith('%')):
            # it's a percentage; turn it into a float
            percentage = p2f(content)
            provider_marketshares.append(percentage)
    return provider_marketshares


def get_marketshares_ssl(table: Tag) -> List[float]:
    marketshares = []
    marketshare_rows = table.find_all("div", {"class": "bar2"})
    for row in marketshare_rows:
        perc = row.find_parent('tr').findChildren('td')[1].contents[0]
        percentage = p2f(perc)
        marketshares.append(percentage)
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
        marketshares = get_marketshares_ssl(table)
    else:
        marketshares = get_marketshares(marketshare_rows)

    providers['marketshare'] = marketshares
    return providers


def scrape_w3techs_table(w3techs: dict) -> pd.DataFrame:
    # read w3techs object described in local config
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


def extract_from_row(market: str, time: pd.Timestamp, df_row: pd.Series) -> ProviderMarketshare:
    '''
    Takes a row of a scraped dataframe and returns ProviderMarketshare.
    `market` and `time` are the first parameters because we partially apply them.
    '''
    name, url, marketshare = df_row.values
    maybe_jurisdiction = shared_utils.get_country(name)
    if maybe_jurisdiction is None:
        juris = None
    else:
        juris = shared_types.Alpha2(maybe_jurisdiction)
    # NOTE - This type does ALL the validation.
    # Once data is in this type, it *should* be trustworthy.
    # See /design-notes.md for more detail on this pattern.
    return ProviderMarketshare(
        str(name), str(url), juris, market, float(marketshare), time
    )


#
# Population-weighted gini tools
#
dirname = path.dirname(__file__)
pth = path.join(dirname, 'analysis', 'prop_net_users.csv')
prop_net_users = pd.read_csv(pth).set_index('alpha2')


def to_df(db_rows) -> pd.DataFrame:
    # TODO put this in TYPES somehow?
    db_rows = pd.DataFrame(db_rows, columns=['name', 'url', 'jurisdiction_alpha2', 'measurement_scope', 'market', 'marketshare', 'time'])
    return db_rows


def fetch_rows(cur: cursor, measurement_scope: str, market: str,  date: pd.Timestamp) -> pd.DataFrame:
    # TODO why this window? a magic number.
    cur.execute(f'''
        SELECT * from provider_marketshare
        WHERE measurement_scope = '{measurement_scope}'
        AND market = '{market}'
        AND time BETWEEN timestamp '{date}' - interval '24 hour' AND  '{date}'
    ''')
    return to_df(cur.fetchall())


def fetch_by_jurisdiction(cur: cursor, measurement_scope: str, market: str,  date: pd.Timestamp) -> pd.DataFrame:
    '''
    Get a DataFrame mapping alpha2 codes to (mean) marketshares on a given date.
    '''
    rows = fetch_rows(cur, measurement_scope, market, date)
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


def population_weighted_gini(cur: cursor, measurement_scope: str, market: str, time: pd.Timestamp) -> Optional[PopWeightedGini]:
    by_juris = fetch_by_jurisdiction(cur, measurement_scope, market, time)
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
    return PopWeightedGini(measurement_scope, market, g, time)
