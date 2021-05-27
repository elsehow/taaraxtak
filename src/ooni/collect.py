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
    Collect W3Techs data and write them to the database.
    '''

    logging.debug('Beginning OONI.')


    logging.debug('OONI complete.')
