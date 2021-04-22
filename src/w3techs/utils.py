import logging
import requests
import numpy as np
import pandas as pd
from funcy import partial
from datetime import datetime
from bs4 import BeautifulSoup

# types
from psycopg2.extensions import cursor
from psycopg2.extensions import connection
from typing import Optional

from src.w3techs.types import ProviderMarketshare
from src.w3techs.types import PopWeightedGini
#
# Scrape utilities
#

def get_table (url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find("table", {"class": "bars"})

def get_provider_name (row):
    provider = row.find('a', recursive=False, href=True)
    if provider:
        return {
            'name': provider.contents[0],
            'url': provider['href'],
        }

def get_provider_names (rows):
    provider_names = []
    for row in rows:
        n = get_provider_name(row)
        if n:
            provider_names.append(n)
    return provider_names

def p2f (percentage_str):
    return float(percentage_str.strip('%'))/100

def get_marketshares (rows):
    provider_marketshares = []
    for row in rows:
        try:
            perc = row.contents[0]
            if perc.endswith('%'):
                provider_marketshares.append(p2f(perc))
        except:
            pass
    return provider_marketshares

def get_marketshares_ssl (table):
    marketshares = []
    marketshare_rows = table.find_all("div", {"class": "bar2"})
    for row in marketshare_rows:
        perc = row.find_parent('tr').findChildren('td')[1].contents[0]
        marketshares.append(p2f(perc))
    return marketshares

def scrape_w3techs_table (w3techs: dict) -> pd.DataFrame:

    w3techs_url = w3techs['url']
    try:
        double_table = w3techs['double_table']
    except:
        double_table = False

    # get request to w3techs; parse html
    table = get_table(w3techs_url)

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

#
# Data marshalling utilities
#

# TODO make relative path
provider_countries = pd.read_csv('src/w3techs/analysis/providers_labeled.csv').set_index('name').drop(['notes', 'url'], axis=1)
provider_countries = provider_countries['country (alpha2)'].to_dict()

def get_country (provider_name: str) -> str:
    '''
    Returns alpha2 code (str of length 2).
    '''
    try:
        alpha2 = provider_countries[provider_name]
        if len(alpha2)==2:
            return alpha2
        return None
    except:
        logging.info(f'Cannot find country for {provider_name}')
        return None

def extract_from_row (market: str, time: pd.Timestamp, df_row: pd.Series) -> ProviderMarketshare:
    '''
    Takes a row of a scraped dataframe and returns ProviderMarketshare.
    `market` and `time` are the first parameters because we partially apply them.
    '''
    name, url, marketshare = df_row.values
    jurisdiction = get_country(name)
    # NOTE - This type does validation. Data in this type should be trusted.
    return ProviderMarketshare(
        str(name), str(url), jurisdiction, market, marketshare, time
    )



# TODO separate everything below into a different file?
#
# Population-weighted gini tools
#

def process_worldbank (fn):
    df = pd.read_csv(fn,
                          skiprows=4
                         )
    # add a 2021 column
    df['2021'] = np.nan
    # remove unclassified data
    df = df[df['Country Code'] !='INX']
    return df


# TODO not sure how i feel about all this stuff in global scope...


# compute each country's share (%) of the world's Internet users.
#
# first, % Internet penetration in each country
# TODO relative paths
net_proportion = process_worldbank('src/w3techs/analysis/API_IT.NET.USER.ZS_DS2_en_csv_v2_2055777.csv')
# then, get population counts in ech country,
# assuming populations remain the same if we have no data
populations = process_worldbank('src/w3techs/analysis/API_SP.POP.TOTL_DS2_en_csv_v2_1976634.csv').fillna(method='ffill', axis=1)
# verify that the country codes of the two dataframes align
assert( np.all(populations['Country Code'] ==
               net_proportion['Country Code']) )
# years in our dataset
years = ['2015', '2016', '2017', '2018', '2019', '2020', '2021']
# compute internet users in each country.
internet_users = (net_proportion[years].astype(float) * populations[years].astype(float))/100
# assume internet users remained the same before readings and after readings
internet_users=\
internet_users\
    .fillna(method='ffill', axis=1)\
    .fillna(method='bfill', axis=1)\
    .astype(float)
# align axes
internet_users['Country Code'] = populations['Country Code']

# country codes utils
country_codes = pd.read_csv('src/w3techs/analysis/countries_codes_and_coordinates.csv')[['Alpha-2 code', 'Alpha-3 code']]
strip_quotes =  lambda x: x.replace('"', '').strip()
alpha2s = country_codes['Alpha-2 code'].apply(strip_quotes)
alpha3s = country_codes['Alpha-3 code'].apply(strip_quotes)
country_codes = dict(zip(alpha3s, alpha2s))

def get_alpha2 (alpha3):
    try:
        return country_codes[alpha3]
    except:
        # TODO - when are we not getting the alpha2 back? is that bad?
        return ''

def proportions_of_internet_users (year: str) -> pd.DataFrame:
    '''
    Get each country's proportion (or share) of the world's total Internet users.
    '''
    this_year = internet_users[[year, 'Country Code']]
    total_users = this_year[this_year['Country Code'] =='WLD'][year].values[0]
    df = pd.DataFrame({
        'alpha2': this_year['Country Code'].apply(get_alpha2),
        'alpha3': this_year['Country Code'],
        'population-share': this_year[year] / total_users,
    })
    # filter items for which we have no alpha2 code
    # TODO filter using an alpha2 validation method in types?
    df = df[df['alpha2'] != '']
    return df

def to_df (db_rows) -> pd.DataFrame:
    # TODO put this in TYPES somehow?
    db_rows = pd.DataFrame(db_rows, columns=['name', 'url', 'jurisdiction_alpha2', 'market', 'marketshare', 'time'])
    return db_rows

def fetch_rows (cur: cursor, market: str, date: pd.Timestamp) -> pd.DataFrame:
    # TODO why the 12 hour window? too magic a number. does it relate to scrape
    # interval perhaps?
    cur.execute(f'''
        SELECT * from provider_marketshare
        WHERE market = '{market}'
        AND time BETWEEN timestamp '{date}' - interval '12 hour' AND  '{date}'
    ''')
    return to_df(cur.fetchall())


def fetch_by_jurisdiction (cur: cursor, market:str, date: pd.Timestamp) -> pd.DataFrame:
    '''
    Get a DataFrame mapping alpha2 codes to (mean) marketshares on a given date.
    '''
    rows = fetch_rows(cur, market, date)
    rows['marketshare'] = rows['marketshare'].astype(float)
    # in case we have the same name and jurisidiction repeated, we take the median makretshare
    rows = rows.groupby(['name', 'jurisdiction_alpha2']).median()
    # then group by each jurisdiction and take the sum of its marketshare
    rows = rows.groupby('jurisdiction_alpha2').sum()
    return rows

def gini(array):
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
    index = np.arange(1,array.shape[0]+1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))

def population_weighted_gini (cur: cursor, market: str, time: pd.Timestamp) -> Optional[PopWeightedGini]:
    by_juris = fetch_by_jurisdiction(cur, market, time)
    # if there are no values, None
    if len(by_juris)==0:
        return None
    # get current % of Internet using population
    pop_share_df = proportions_of_internet_users(str(time.year))
    # weight marketshare
    merged = pop_share_df.merge(by_juris,
                                left_on='alpha2',
                                right_on='jurisdiction_alpha2',
                                how='left')
    merged['weighted'] = merged['marketshare'] / merged['population-share']
    merged = merged.fillna(0)
    # compute gini on weighted marketshare
    g = gini(merged['weighted'].values)
    return PopWeightedGini(market, g, time)
