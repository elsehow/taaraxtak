from config import config
import logging
import sys
from funcy import partial

from src.shared.utils import configure_logging, run_threaded


#
# setup
#
configure_logging()
logger = logging.getLogger("taaraxtak:collect")

# connect to the db
postgres_config = config['postgres']

if len(sys.argv) != 2:
    logging.error('You must provide an argument for which job to run')
else:
    command = sys.argv[1]
    collect = None
    if command == 'w3techs':
        from src.w3techs.collect import collect
    elif command == 'ooni':
        from src.ooni.collect import collect

    if collect is not None:
        do_command = partial(collect, postgres_config)
        run_threaded(do_command)
    else:
        logging.error(f"Command {command} not found")
