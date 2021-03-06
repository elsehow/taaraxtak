# taaraxtak
# nick merrill
# 2021
#
# w3techs
# collect.py - collects data and saves it in the db.
# (see file by the same name in repository's root).

import logging
import psycopg2

import src.ooni.utils as utils


logger = logging.getLogger("src.ooni.collect")


def collect(postgres_config: dict):
    '''
    Collect OONI data and write them to the database.
    '''
    logger.info('Beginning OONI.')

    try:
        conn = psycopg2.connect(**postgres_config)
        cur = conn.cursor()
        logger.debug('Connected to database.')

        # get most recent time represented in the DB
        maybe_t = utils.get_latest_reading_time(cur)
        # if we have no time
        if maybe_t is None:
            # query recent measurements (i.e., seed the DB)
            logger.info('Querying recent measurements.')
            ms = utils.query_recent_measurements()
        # if there is a measurement
        else:
            # query all the results since that measurmeent
            logger.debug(f'Querying results after {maybe_t}.')
            ms = utils.query_measurements_after(maybe_t)
        # marshall them into our format (validating htem in the process)
        logger.debug(f'Retrieved {len(ms)} results.')
        ingested = utils.ingest_api_measurements(ms, postgres_config)
        logger.debug(f'Ingested {len(ingested)} results.')
        # and write them to the database
        utils.write_to_db(cur, conn, ingested)
        logger.info(f'Wrote {len(ingested)} results to database.')

        logger.info('OONI complete.')
    except Exception as e:
        logger.error(f'Error collecting OONI data {e}')
