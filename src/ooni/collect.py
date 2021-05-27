# taaraxtak
# nick merrill
# 2021
#
# w3techs
# collect.py - collects data and saves it in the db.
# (see file by the same name in repository's root).

import logging
import pandas as pd
from funcy import partial
from datetime import datetime

from psycopg2.extensions import cursor
from psycopg2.extensions import connection

import src.w3techs.utils as utils


def collect(cur: cursor, conn: connection):
    '''
    Collect OONI data and write them to the database.
    '''
    logging.debug('Beginning OONI.')

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
    ingested = utils.ingest_api_measurements(ms)
    logger.debug(f'Ingested {len(ingested)} results.')
    # and write them to the database
    utils.write_to_db(cur, conn, ingested)
    logger.info(f'Wrote {len(ingested)} results to database.')
    utils.scrape(cur, conn)

    logging.debug('OONI complete.')
