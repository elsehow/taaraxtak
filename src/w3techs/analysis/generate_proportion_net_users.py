# taaraxtak
# nick merril
# 2021
#
# W3Techs
import numpy as np
import pandas as pd

from typing import Dict

# Compute each country's share (%) of the world's Internet users.
#
# Produces a CSV with columns alpha2 (index) and years.
#
# Each cell is a country's proportion of the total Internet users in the world
# during that year.


def process_worldbank(fn):
    df = pd.read_csv(fn, skiprows=4)
    # add a 2021 column
    df['2021'] = np.nan
    # remove unclassified data
    df = df[df['Country Code'] != 'INX']
    return df


# years in our dataset
years = ['2015', '2016', '2017', '2018', '2019', '2020', '2021']


def compute_internet_users():
    # first, % Internet penetration in each country
    net_proportion = process_worldbank('API_IT.NET.USER.ZS_DS2_en_csv_v2_2055777.csv')
    # then, get population counts in ech country,
    # assuming populations remain the same into the future if we have no data
    populations = process_worldbank('API_SP.POP.TOTL_DS2_en_csv_v2_1976634.csv').fillna(method='ffill', axis=1)
    # verify that the country codes of the two dataframes align
    assert(np.all(populations['Country Code'] == net_proportion['Country Code']))
    # compute internet users in each country.
    internet_users = (net_proportion[years].astype(float) * populations[years].astype(float))/100
    # assume internet users remained the same before readings and after readings
    internet_users =\
        internet_users\
        .fillna(method='ffill', axis=1)\
        .fillna(method='bfill', axis=1)\
        .astype(float)
    # Add back in Alpha 3 axis
    internet_users['Country Code'] = populations['Country Code']
    return internet_users


def country_codes_dict() -> Dict[str, str]:
    # country codes utils
    ccs = pd.read_csv('countries_codes_and_coordinates.csv')[['Alpha-2 code', 'Alpha-3 code']]

    def strip_quotes(x):
        return x.replace('"', '').strip()

    alpha2s = ccs['Alpha-2 code'].apply(strip_quotes)
    alpha3s = ccs['Alpha-3 code'].apply(strip_quotes)
    return dict(zip(alpha3s, alpha2s))


internet_users = compute_internet_users()


def proportions_of_internet_users(year: str) -> pd.DataFrame:
    '''
    Get each country's proportion (or share) of the world's total Internet users.
    '''

    country_codes = country_codes_dict()

    def get_alpha2(alpha3):
        try:
            return country_codes[alpha3]
        except (KeyError):
            # Some values are not countries (like WLD, or WORLD)
            # we return -1 for those.
            return -1

    this_year = internet_users[[year, 'Country Code']]
    # get the world's population
    total_users = this_year[this_year['Country Code'] == 'WLD'][year].values[0]
    df = pd.DataFrame({
        'alpha2': this_year['Country Code'].apply(get_alpha2),
        'alpha3': this_year['Country Code'],
        'population-share': this_year[year] / total_users,
    })
    # filter items for which we have no alpha2 code
    df = df[df['alpha2'] != -1]
    return df


idx = None
proportions = []
for year in years:
    prop_df = proportions_of_internet_users(year)
    series = prop_df['population-share']
    series = series.rename(year)
    proportions.append(series)
    idx = prop_df['alpha2']

prop_net_users = pd.DataFrame(proportions).T
prop_net_users.index = idx

prop_net_users.to_csv('prop_net_users.csv')
