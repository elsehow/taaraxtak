from os import path
import pandas as pd
import logging
from os.path import join
import pytz
from datetime import datetime

from typing import Optional

from config import config
import coloredlogs

#
# Time
#
def now() -> pd.Timestamp:
    return pd.Timestamp.utcnow()


def is_in_future(timestamp: pd.Timestamp) -> bool:
    return timestamp > now()


def to_utc(t: datetime) -> datetime:
    return t.astimezone(pytz.utc)


#
# Type validation
#
def is_nonempty_str(my_str: str) -> bool:
    is_str = type(my_str) == str
    if is_str:
        return len(my_str) > 0
    return False


#
# Jurisdictions of providers
#
dirname = path.dirname(__file__)
pth = join(dirname, 'analysis', 'providers_labeled.csv')
provider_countries = pd.read_csv(pth).set_index('name').drop(['notes', 'url'], axis=1)
provider_countries = provider_countries['country (alpha2)'].to_dict()


def get_country(provider_name: str) -> Optional[str]:
    '''
    Returns alpha2 code (str of length 2).
    '''
    try:
        alpha2 = provider_countries[provider_name]
        if len(alpha2) == 2:
            return alpha2
        return None
    except (TypeError):
        logging.debug(f'Country code for {provider_name} is not a string: {alpha2}')
        return None
    except (KeyError):
        logging.info(f'Cannot find country for {provider_name}')
        return None


def configure_logging():
    logging_config = config['logging']
    log_level = logging_config['level']
    if logging_config['handler'] == 'file':
        logging.basicConfig(level=log_level, filename=logging_config['file'])
    else:
        logging.basicConfig(level=log_level)
        coloredlogs.install()
        coloredlogs.install(level=log_level)
