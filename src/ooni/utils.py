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
import tldextract
import idna
import psycopg2
from multiprocessing import Pool

from typing import List
from IPy import IP
from funcy import partial


import src.shared.utils as shared_utils

# types
from psycopg2.extensions import cursor
from psycopg2.extensions import connection
from multiprocessing.pool import IMapIterator

import src.ooni.types as ooni_types
import src.shared.types as shared_types

from typing import Optional


# how many seconds to wait between paginating
# (so as not to overwhelm the OONI API endpoint)
OONI_SLEEP_PAGINATE = 0.25


logging.basicConfig()
logger = logging.getLogger("src.ooni.utils")
# logger.setLevel(logging.DEBUG)
coloredlogs.install()
coloredlogs.install(level='DEBUG')
# coloredlogs.install(level='INFO')

# disable noisy logging by filelock (called by TLDExtract to deal with its cache)
logging.getLogger("filelock").setLevel(logging.ERROR)

#
# utils
#


def now() -> pd.Timestamp:
    return pd.Timestamp.utcnow()


def is_in_future(timestamp: pd.Timestamp) -> bool:
    return timestamp > now()


def to_utc(t: datetime) -> datetime:
    return t.astimezone(pytz.utc)


#
# OONI querying
#


def api_query(query: str, results=[], queries=1, max_queries=None) -> list:
    '''Recursively query the API, up to `max_queries`. (If `max_queries=None`, we
    will paginate through the results as long as they run).
    '''
    base_url = 'https://api.ooni.io/api/v1/'
    query = '{!s}{!s}'.format(base_url, query)
    try:
        resp = requests.get(query).json()
        results = results + resp['results']
        next_url = resp['metadata']['next_url']
        if max_queries is not None and queries > max_queries:
            return results
        if next_url:
            # sleep so as to not overwhelm the endpoint
            sleep(OONI_SLEEP_PAGINATE)
            # remove base url to perfrom the query
            next_url = next_url.split('api/v1/')[1]
            return api_query(next_url, results, queries + 1, max_queries)
        return results
    except Exception as inst:
        # if we have an error,
        logger.warning("Error querying API: {!s}".format(inst))
        # just return what we've collected
        # (at worst, `results` will be `[]`)
        return results


BASE_QUERY = 'measurements?test_name=web_connectivity&anomaly=true&order_by=test_start_time&limit=1000'


def query_recent_measurements(max_queries=5) -> list:
    '''Queries all recent measurements, up to specified maximum number of queries.'''
    return api_query(BASE_QUERY, max_queries=max_queries)


def query_measurements_after(time: datetime, **kwargs) -> list:
    '''Queries all measurements after time.'''
    def fmt_dt(t: datetime):
        return t.strftime("%Y-%m-%dT%H:%M:%S")
    # format timezone-aware date into UTC fo querying
    utc_dt = to_utc(time)
    # format it into the query url
    dt_str = fmt_dt(utc_dt)
    query_str = BASE_QUERY + f'&since={dt_str}'
    # issue the query
    return api_query(query_str, **kwargs)


def get_blocking_type(measurement) -> Optional[str]:
    '''Get blocking type, if available.'''
    try:
        return measurement['scores']['analysis']['blocking_type']
    except KeyError:
        return None

#
# Get IP from URL
#


def get_hostname(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc
    if parsed.port:
        return netloc.split(':')[0]
    return netloc


def fetch_ip_from_hostname(hostname: str) -> Optional[str]:
    try:
        return socket.gethostbyname(hostname)
    except Exception as inst:
        logger.warning(f"Error looking up IP of hostname {hostname}: {inst}")
        return None

#
# Get location from IP
#


def ip_to_alpha2(ip: str) -> Optional[shared_types.Alpha2]:
    with geoip2.database.Reader('src/ooni/analysis/dbip-country-lite-2021-05.mmdb') as reader:
        try:
            response = reader.country(ip)
            return shared_types.Alpha2(response.country.iso_code)
        except Exception as inst:
            # if we have an error,
            logger.warning(f"Error looking up country code of IP {ip}: {inst}")
            return None


#
# Cacheing IP to hostname mappings
#

def retrieve_ip(cur: cursor, hostname: str) -> Optional[Tuple[datetime, str]]:
    cur.execute(f'''
    SELECT time, ip from ip_hostname_mapping
    WHERE hostname='{hostname}'
    ORDER BY time DESC
    ''')
    return cur.fetchone()

def retrieve_cached_ip (cur: cursor, hostname: str,
                     cache_expiry: timedelta = timedelta(days=1)):
    # if we have a result in our DB
    time_ip_tuple = retrieve_ip(cur, hostname)
    if time_ip_tuple:
        time, ip = time_ip_tuple
        # and that result is fresh enough
        print(cache_expiry, to_utc(time))
        is_expired = (now() - cache_expiry) > to_utc(time)
        if not is_expired:
            # return it
            return ip
        return None

def lookup_ip(cur: cursor, conn: connection, hostname: str) -> Optional[str]:
    '''
    Looks up an IP address from a hostname in the cache.
    If the IP address was recorded more than `cache_expiry` ago, it'll fetch a new IP
    '''
    maybe_ip: Optional[str] = retrieve_cached_ip(cur, hostname)
    if maybe_ip:
        return maybe_ip
    # otherwise
    # fetch IP with a query
    maybe_ip: Optional[str] = fetch_ip_from_hostname(hostname)
    if maybe_ip:
        # write that mapping to the DB for the future
        mapping = ooni_types.IPHostnameMapping(maybe_ip, hostname, now())
        mapping.write_to_db(cur, conn)
        # return the IP
        return maybe_ip
    return None


def url_to_alpha2(cur: cursor, conn: connection, url: str) -> Optional[shared_types.Alpha2]:
    hostname = get_hostname(url)
    maybe_ip = lookup_ip(cur, conn, hostname)
    if maybe_ip is None:
        return None
    return ip_to_alpha2(maybe_ip)


#
# Get TLD jurisdiction
#

# keep a cache of TLDs in this directory
# this should make an HTTP request on first call, then refer to cache.
# TODO - update this cache occasionally.
extract_tld = tldextract.TLDExtract(cache_dir='my-tld-cache')
# extract_tld = tldextract.TLDExtract()


def get_tld_jurisdiction(url: str) -> Optional[shared_types.Alpha2]:
    '''
    Takes a URL and gets an Alpha 2
    representing the jurisdiction of the URL's top-level domain.
    '''
    hostname = get_hostname(url)
    try:
        # sometimes, the hostname is just an IP
        # we can't get any TLD from that of course,
        IP(hostname)  # so we'll just return None
        return None
    except ValueError:
        pass
    # decode IDNA (internationalized) hostnames
    # e.g. http://xn--80aaifmgl1achx.xn--p1ai/
    decoded_hostname = idna.decode(hostname)
    tld = extract_tld(decoded_hostname)
    # get last item in url
    # e.g., '.com.br' should be '.br'
    tld = tld.suffix
    cc_tld = tld.split('.')[-1]
    # put it
    cc_tld_str = f'.{cc_tld}'
    cc = shared_utils.get_country(cc_tld_str)
    if cc is not None:
        return shared_types.Alpha2(cc)
    logger.warning(f'No TLD jurisidiction found for {url}')
    return None


#
# Querying and ingesting measurements
#
def get_latest_reading_time(cur: cursor) -> Optional[datetime]:
    '''Get time of most recent measurement in database'''
    try:
        cur.execute('SELECT measurement_start_time from ooni_web_connectivity_test ORDER BY measurement_start_time DESC')
        return cur.fetchone()[0]
    except TypeError:
        logger.info('No recent measurement found!')
        return None


def ingest_api_measurement(postgres_config: dict, measurement: dict) -> ooni_types.OONIWebConnectivityTest:
    '''
    Marshall from API format to our type.
    '''
    # make a connection and cursor (for this thread)
    # connection = psycopg2.connect(**config['postgres'])
    connection = psycopg2.connect(**postgres_config)
    cursor = connection.cursor()
    blocking_type = get_blocking_type(measurement)
    probe_alpha2 = shared_types.Alpha2(measurement['probe_cc'])
    input_url = measurement['input']
    anomaly = measurement['anomaly']
    confirmed = measurement['confirmed']
    report_id = measurement['report_id']
    input_ip_alpha2 = url_to_alpha2(cursor, connection, input_url)
    tld_jurisdiction_alpha2 = get_tld_jurisdiction(input_url)
    measurement_start_time = pd.Timestamp(measurement['measurement_start_time'])
    return ooni_types.OONIWebConnectivityTest(
        blocking_type,
        probe_alpha2,
        input_url,
        anomaly,
        confirmed,
        report_id,
        input_ip_alpha2,
        tld_jurisdiction_alpha2,
        measurement_start_time
    )


def ingest_api_measurements(measurements: List[dict], postgres_config: dict) -> List[ooni_types.OONIWebConnectivityTest]:
    my_ingest = partial(ingest_api_measurement, postgres_config)
    with Pool() as p:
        return p.map(my_ingest, measurements)


def write_to_db(cur: cursor, conn: connection, connectivity_tests: List[ooni_types.OONIWebConnectivityTest]) -> None:
    for t in connectivity_tests:
        t.write_to_db(cur, conn, commit=False)
    conn.commit()
