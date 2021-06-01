from os import path
import pandas as pd
import logging

from typing import Optional

#
# Type validation
#
def is_nonempty_str(my_str: str) -> bool:
    is_str = type(my_str) == str
    if is_str:
        return len(my_str) > 0
    return False


#
# File I/O
#
def path_to (*args, relative=False) -> str:
    if relative:
        dirname = path.dirname(__file__)
        return path.join(dirname, *args)
    return path.join(*args)


#
# Jurisdictions of providers
#
provider_countries = pd.read_csv(
    path_to('analysis', 'providers_labeled.csv', relative=True)
).set_index('name').drop(['notes', 'url'], axis=1)
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

