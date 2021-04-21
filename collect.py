# taaraxtak
# nick merrill
# 2021
#
# create-tables.py - defines the Postgres tables.
# this runs always.

import schedule
import psycopg2
from funcy import partial

from src.w3techs.collect import collect as w3techs_collect

#
# setup
#

# TODO connect to the db

# configure scrapers for the db
w3techs = partial(w3techs_collect, conn, cur)

#
# run
#

schedule.every(12).hours(w3techs)
