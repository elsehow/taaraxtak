import logging
import coloredlogs
import requests
from time import sleep
from datetime import datetime
import pytz
import pandas as pd
import socket
import urllib.parse
import geoip2

import src.ooni.types as ooni_types

from typing import Optional
from psycopg2.extensions import cursor
from psycopg2.extensions import connection

def to_utc (t: datetime) -> datetime:
    return t.astimezone(pytz.utc)

# TODO make this dry! it's shared with w3techs rn
def is_nonempty_str(my_str: str) -> bool:
    is_str = type(my_str) == str
    if is_str:
        return len(my_str) > 0
    return False

#
# OONI querying
#

def api_query (query: str, results=[], queries=1, max_queries=None) -> list:
    '''Recursively query the API, up to `max_queries`. (If `max_queries=None`, we
    will paginate through the results as long as they run).
    '''
    base_url = 'https://api.ooni.io/api/v1/'
    query = '{!s}{!s}'.format(base_url, query)
    try:
        resp =  requests.get(query).json()
        results = results + resp['results']
        next_url = resp['metadata']['next_url']
        if max_queries is not None and queries > max_queries:
            return results
        if next_url:
            # sleep so as to not overwhelm the endpoint
            sleep(config['sleep-times']['ooni-paginate'])
            # remove base url to perfrom the query
            next_url = next_url.split('api/v1/')[1]
            return api_query(next_url, results, queries+1, max_queries)
        return results
    except Exception as inst:
        # if we have an error,
        logging.warning("Error querying API: {!s}".format(inst))
        # just return what we've collected
        # (at worst, `results` will be `[]`)
        return results

def query_recent_measurements (max_queries=5) -> list:
    '''Queries all recent measurements, up to specified maximum number of queries.'''
    base_query = 'measurements?test_name=web_connectivity&anomaly=true&order_by=test_start_time&limit=1000'
    return api_query(base_query, max_queries=max_queries)

def get_blocking_type (measurement) -> str:
    '''Get blocking type, if available.'''
    try:
        return measurement['scores']['analysis']['blocking_type']
    except:
        return None

#
# Get IP from URL
#

def get_hostname (url):
    return urllib.parse.urlparse(url).netloc

def fetch_ip_from_hostname (hostname: str) ->  str:
    try:
        return socket.gethostbyname(hostname)
    except Exception as inst:
            logger.warning(f"Error looking up IP of hostname {hostname}: {inst}")
            return None

#
# Get location from IP
#
def ip_to_alpha2 (ip: str) -> Optional[ooni_types.Alpha2]:
    with geoip2.database.Reader('dbip-country-lite-2021-05.mmdb') as reader:
        try:
            response = reader.country(ip)
            return ooni_types.Alpha2(response.country.iso_code)
        except Exception as inst:
            # if we have an error,
            logger.warning(f"Error looking up country code of IP {ip}: {inst}")
            return None
