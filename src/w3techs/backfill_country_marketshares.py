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

# sources we're scraping from
w3techs_sources = {
    'data-centers': {
        'url': "https://w3techs.com/technologies/overview/data_center",
    },
    'operating-system': {
        'url': "https://w3techs.com/technologies/overview/operating_system",
    },
    'web-hosting': {
        'url': "https://w3techs.com/technologies/overview/web_hosting",
    },
    'proxy': {
        'url': "https://w3techs.com/technologies/overview/proxy",
        'double_table': True,
    },
    'dns-server': {
        'url': "https://w3techs.com/technologies/overview/dns_server",
    },
    'email-server': {
        'url': "https://w3techs.com/technologies/overview/email_server",
    },
    'ssl-certificate': {
        'url': "https://w3techs.com/technologies/overview/ssl_certificate",
        'double_table': True,
    },
    'content-delivery': {
        'url': "https://w3techs.com/technologies/overview/content_delivery",
        'double_table': True,
    },
    'traffic-analysis': {
        'url': "https://w3techs.com/technologies/overview/traffic_analysis",
        'double_table': True,
    },
    'advertising': {
        'url': "https://w3techs.com/technologies/overview/advertising",
        'double_table': True,
    },
    'tag-manager': {
        'url': "https://w3techs.com/technologies/overview/tag_manager",
        'double_table': True,
    },
    'social-widgets': {
        'url': "https://w3techs.com/technologies/overview/social_widget",
        'double_table': True,
    },
    # TODO fix
    # 'site-element': {
    #     'url': "https://w3techs.com/technologies/overview/site_element",
    # },
    # TODO fix
    # 'structured-data': {
    #     'url': "https://w3techs.com/technologies/overview/structured_data",
    # },
    'markup-language': {
        'url': "https://w3techs.com/technologies/overview/markup_language",
    },
    'character-encoding': {
        'url': "https://w3techs.com/technologies/overview/character_encoding",
    },
    # TODO fix
    # 'image-format': {
    #     'url': "https://w3techs.com/technologies/overview/image_format",
    # },
    'top-level-domain': {
        'url': 'https://w3techs.com/technologies/overview/top_level_domain'
    },
    'server-location': {
        'url': "https://w3techs.com/technologies/overview/server_location",
    },
    'content-language': {
        'url': "https://w3techs.com/technologies/overview/content_language",
    },
}


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
    end_date = datetime(2021,11,30)
    day = timedelta(days=1)

    while start_date <= end_date:
        logging.info(f'{start_date}')        
        for market in included_markets:
            logging.info(f'Computing country marketshares for {market}')
            country_marketshares = utils.country_marketshare(cur, 'all', market, pd.Timestamp(start_date))
            if country_marketshares is not None:
                extract = partial(utils.extract_from_row_country, market, pd.Timestamp(start_date))
                countries = country_marketshares.apply(extract, axis=1)
                if countries is not None:
                    for country in countries:
                        country.write_to_db(cur, conn)
        start_date = start_date + day


    logging.debug('W3Techs complete.')
