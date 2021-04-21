import logging
import requests
import pandas as pd
from funcy import partial
from bs4 import BeautifulSoup

from src.w3techs.types import ProviderMarketshare

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
