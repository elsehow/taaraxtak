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


logger = logging.getLogger("src.w3techs.collect")


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

    logger.info('Beginning W3Techs.')

    try:
        conn = psycopg2.connect(**postgres_config)
        cur = conn.cursor()
        logger.debug('Connected to database.')

        # Scrape W3Techs data
        for market_name, dic in w3techs_sources.items():
            logger.info(f'Scraping {market_name}')
            # scrape table from W3techs
            df = utils.scrape_w3techs_table(dic)
            # extract Marketshare types from datable
            extract = partial(utils.extract_from_row,
                              market_name, pd.Timestamp(datetime.now()))
            marketshares = df.apply(extract, axis=1)
            # write all Marketshares to the cursor
            for marketshare in marketshares:
                marketshare.write_to_db(cur, conn, commit=False)
            # commit all writes to db
            conn.commit()

        # Compute gini coefficients
        for market in included_markets:
            logging.info(f'Computing provider-based gini for {market}')
            provider_gini = utils.provider_gini(cur, 'all', market, pd.Timestamp(datetime.now()))
            provider_gini.write_to_db(cur, conn)
            logger.info(f'Computing country-based ginis for {market}')
            country_gini = utils.country_gini(cur, 'all', market, pd.Timestamp(datetime.now()))
            country_gini.write_to_db(cur, conn)

        logger.info('W3Techs complete.')
    except Exception as e:
        logger.error(f'Error collecting W3Techs data {e}')
