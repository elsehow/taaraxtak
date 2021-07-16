# taaraxtak
# nick merrill
# 2021
#
# create-tables.py - defines the Postgres tables.
# this runs always.

import time
import schedule
import logging
from funcy import partial
from src.shared.utils import configure_logging, run_threaded

from src.w3techs.collect import collect as w3techs_collect
from src.ooni.collect import collect as ooni_collect

from config import config




#
# setup
#
configure_logging()
logger = logging.getLogger("taaraxtak:collect")

# connect to the db
postgres_config = config['postgres']

# configure scrapers for the db
w3techs = partial(w3techs_collect, postgres_config)
ooni = partial(ooni_collect, postgres_config)
#
# run
#

schedule.every().day.at('09:00').do(run_threaded, w3techs)
schedule.every(10).minutes.do(run_threaded, ooni)

while 1:
    schedule.run_pending()
    time.sleep(1)
