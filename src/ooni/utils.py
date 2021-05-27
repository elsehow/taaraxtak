import logging
import coloredlogs
import requests
from time import sleep
from datetime import datetime
import pytz
import socket
import urllib.parse
import geoip2.database
import pandas as pd
from typing import Tuple
from datetime import timedelta

from psycopg2.extensions import cursor
from psycopg2.extensions import connection

import src.ooni.types as ooni_types

from typing import Optional


logging.basicConfig()
logger = logging.getLogger("src.ooni.utils")
# logger.setLevel(logging.DEBUG)
coloredlogs.install()
coloredlogs.install(level='DEBUG')
# coloredlogs.install(level='INFO')

#
# utils
#

def now () -> pd.Timestamp:
    return pd.Timestamp.utcnow()

def is_in_future (timestamp: pd.Timestamp) -> bool:
    return timestamp > now()

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
    with geoip2.database.Reader('src/ooni/analysis/dbip-country-lite-2021-05.mmdb') as reader:
        try:
            response = reader.country(ip)
            return ooni_types.Alpha2(response.country.iso_code)
        except Exception as inst:
            # if we have an error,
            logger.warning(f"Error looking up country code of IP {ip}: {inst}")
            return None

#
# Cacheing IP to hostname mappings
#
def retrieve_ip (cur: cursor, hostname: str) -> Optional[Tuple[datetime, str]]:
    cur.execute('''
    SELECT time, ip from ip_hostname_mapping
    WHERE hostname=hostname
    ORDER BY time DESC
    ''')
    return cur.fetchone()


def lookup_ip (cur: cursor, conn: connection, hostname: str,
               cache_expiry: timedelta = timedelta(days=1)) -> str:
    '''
    Looks up an IP address from a hostname in the cache.
    If the IP address was recorded more than `cache_expiry` ago, it'll fetch a new IP
    '''
    # if we have a result in our DB
    time_ip_tuple = retrieve_ip(cur, hostname)
    if time_ip_tuple:
        time, ip = time_ip_tuple
        # and that result is fresh enough
        is_expired = (now() - cache_expiry) > to_utc(time)
        if not is_expired:
            # return it
            return ip
    # otherwise
    # fetch IP with a query
    ip = fetch_ip_from_hostname(hostname)
    # write that mapping to the DB for the future
    mapping = ooni_types.IPHostnameMapping(ip, hostname, now())
    mapping.write_to_db(cur, conn)
    # return the IP
    return ip

def url_to_alpha2 (cur: cursor, conn: connection, url: str) -> Optional[ooni_types.Alpha2]:
    hostname = get_hostname(url)
    maybe_ip = lookup_ip(cur, conn, hostname)
    if maybe_ip is None:
        return None
    return ip_to_alpha2(maybe_ip)
