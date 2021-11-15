# taaraxtak
# nick merrill
# 2021
#
# w3techs
# collect.py - collects data and saves it in the db.
# (see file by the same name in repository's root).

import psycopg2
import logging
import pandas as pd
from funcy import partial
from datetime import datetime
from datetime import timedelta

import src.w3techs.utils as utils

# These are the markets we include to compute our Gini coefficients.
# Their meaning and rationale are documented in w3techs/README.md
included_markets = [
    'web-hosting',
    'ssl-certificate',
    'proxy',
    'data-centers',
    'dns-server',
    'server-location',
    'top-level-domain',
]

def collect(postgres_config: dict):
    '''
    Collect W3Techs data and write them to the database.
    '''

    logging.debug('Beginning W3Techs.')

    conn = psycopg2.connect(**postgres_config)
    cur = conn.cursor()
    logging.debug('Connected to database.')

    # # Scrape W3Techs data
    # for market_name, dic in w3techs_sources.items():
    #     logging.info(f'Scraping {market_name}')
    #     # scrape table from W3techs
    #     df = utils.scrape_w3techs_table(dic)
    #     # extract Marketshare types from datable
    #     extract = partial(utils.extract_from_row,
    #                       market_name, pd.Timestamp(datetime.now()))
    #     marketshares = df.apply(extract, axis=1)
    #     # write all Marketshares to the cursor
    #     for marketshare in marketshares:
    #         marketshare.write_to_db(cur, conn, commit=False)
    #     # commit all writes to db
    #     conn.commit()

    # Compute gini coefficients

    start_date = datetime(2015,4,2)
    end_date = datetime(2021,11,9)
    day = timedelta(days=1)

    while start_date <= end_date:
        logging.info(f'{start_date}')        
        for market in included_markets:
            logging.info(f'Computing provider-based gini for {market}')
            provider_gini = utils.provider_gini(cur, 'all', market, pd.Timestamp(start_date))
            if provider_gini is not None:
                provider_gini.write_to_db(cur, conn)
            logging.info(f'Computing country-based gini for {market}')
            country_gini = utils.country_gini(cur, 'all', market, pd.Timestamp(start_date))
            if country_gini is not None:
                country_gini.write_to_db(cur, conn)
        start_date = start_date + day


    logging.debug('W3Techs complete.')
