# taaraxtak
# nick merrill
# 2021
#
# create-tables.py - sets up database tables
# run this once.

from funcy import partial
import logging
import coloredlogs
import psycopg2

from src.w3techs.types import create_tables as w3techs_create

from config import config
#
# setup
#
logging.basicConfig()
logger = logging.getLogger("taaraxtak:create_tables")
# logger.setLevel(logging.DEBUG)
coloredlogs.install()
coloredlogs.install(level='INFO')
# coloredlogs.install(level='DEBUG')

# connect to the db
connection = psycopg2.connect(**config['postgres'])
cursor = connection.cursor()

# configure create methods for the db
w3techs = partial(w3techs_create, cursor, connection)

#
# run
#
# w3techs()
