# taaraxtak
# nick merrill
# 2021
#
# create-tables.py - sets up database tables
# run this once.

from funcy import partial

from src.w3techs.create-tables import create as w3techs_create

#
# setup
#

# TODO connect to the db

# configure create methods for the db
w3techs = partial(w3techs_create, conn, cur)

#
# run
#
# TODO
w3techs()

