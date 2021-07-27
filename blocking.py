
# coding: utf-8

# In[20]:


import logging
import requests
from time import sleep

from psycopg2.extensions import cursor
from psycopg2.extensions import connection
import pandas as pd

from src.shared.utils import configure_logging

# In[2]:


configure_logging()
logger = logging.getLogger("poll-ooni")


# In[40]:


import config
from imp import reload
reload(config)
from config import config
import psycopg2

# connect to the db
my_connection = psycopg2.connect(**config['postgres'])
my_cursor = my_connection.cursor()
logger.info('Connected to database.')


# In[71]:


from datetime import datetime
import pytz

def to_utc (t: datetime) -> datetime:
    return t.astimezone(pytz.utc)


# In[6]:


# TODO make dry!
def is_nonempty_str(my_str: str) -> bool:
    return (type(my_str) == str) & (len(my_str) > 0)

class Alpha2 ():
    '''
    Represents an ISO alpha-2 country code.
    '''
    def __init__(self,
                 country_code: str):
        assert(is_nonempty_str(country_code))
        assert(len(country_code)==2)
        self.country_code = country_code
        
    def __str__(self):
        return f'{self.country_code}'
    
    def __repr__(self):
        return self.__str__()


# # Getting the data we need
# 
# ## Measuremnets from OONI

# In[7]:


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
        logger.warning("Error querying API: {!s}".format(inst))
        # just return what we've collected
        # (at worst, `results` will be `[]`)
        return results


# In[8]:


base_query = 'measurements?test_name=web_connectivity&anomaly=true&order_by=test_start_time&limit=1000'

def query_recent_measurements (max_queries=5) -> list:
    '''Queries all recent measurements, up to specified maximum number of queries.'''
    return api_query(base_query, max_queries=max_queries)

def get_blocking_type (measurement) -> str:
    '''Get blocking type, if available.'''
    try:
        return measurement['scores']['analysis']['blocking_type']
    except:
        return None


# In[9]:


# measurements = query_recent_measurements()


# In[10]:


# len(measurements)


# In[11]:


# m_detail = requests.get(m['measurement_url']).json()

# m_detail['test_keys']['queries']
# m_detail


# ## Get IP from URL

# In[13]:


# inputs = [m['input'] for m in measurements]


# In[12]:


import socket
import urllib.parse
from typing import Optional

def get_hostname (url):
    return urllib.parse.urlparse(url).netloc

def fetch_ip_from_hostname (hostname: str) ->  str:
    try:
        return socket.gethostbyname(hostname)
    except Exception as inst:
            logger.warning(f"Error looking up IP of hostname {hostname}: {inst}")
            return None


# In[14]:


# my_ip = fetch_ip_from_hostname(get_hostname(inputs[505]))
# my_ip


# ## Get geolocation from IP

# In[15]:


import geoip2.database
from typing import Optional

def ip_to_alpha2 (ip: str) -> Optional[Alpha2]:
    with geoip2.database.Reader('dbip-country-lite-2021-05.mmdb') as reader:
        try:
            response = reader.country(ip)
            return Alpha2(response.country.iso_code)
        except Exception as inst:
            # if we have an error,
            logger.warning(f"Error looking up country code of IP {ip}: {inst}")
            return None
    
# ip_to_alpha2(my_ip)


# ## Cacheing IP
# 
# ### A data model for IP Hostname mapping

# In[21]:


from IPy import IP
import pandas as pd

class IPHostnameMapping:
    def __init__ (
        self,
        ip: str,
        hostname: str,
        time: pd.Timestamp,
    ):
        assert(is_nonempty_str(hostname))
        self.hostname = hostname
        # this will throw if `ip` isn't valid
        ip = IP(ip)
        # check that it's a public IP!
        assert(ip.iptype() == 'PUBLIC')
        # we'll just save the IP as a string for simplicity's sake
        self.ip = ip.strNormal()
        assert(type(time) == pd.Timestamp)
        self.time = time
    
    def create_table(
            self,
            cur: cursor,
            conn: connection):
        cmd = """
          CREATE TABLE ip_hostname_mapping (
             hostname                  VARCHAR NOT NULL,
             ip                        VARCHAR NOT NULL,
             time                      TIMESTAMPTZ NOT NULL
          )
        """
        cur.execute(cmd)
        conn.commit()

    def write_to_db(
            self,
            cur: cursor,
            conn: connection,
            commit=True,
    ):
        cur.execute(
            """
            INSERT INTO ip_hostname_mapping
            (hostname, ip, time)
            VALUES
            (%s, %s, %s)
            """, (self.hostname,
                  self.ip,
                  self.time
                 ))
        if commit:
            return conn.commit()
        return

    def __str__(self):
        return f'{self.time: self.hostname->self.ip}'
    


# In[22]:


# ip = IP(my_ip)
# ip.iptype()


# In[23]:


# mapping = IPHostnameMapping('wikipedia.org', '198.35.26.96', now())
# mapping.create_table(my_cursor, my_connection)


# In[24]:


# get_ip('wikipedia.org')


# ## Integrate database read/writes into IP lookup

# In[25]:


from typing import Tuple
def retrieve_ip (cur: cursor, hostname: str) -> Optional[Tuple[datetime, str]]:
    cur.execute('''
    SELECT time, ip from ip_hostname_mapping
    WHERE hostname=hostname
    ORDER BY time DESC
    ''')
    return cur.fetchone()


# In[26]:


from datetime import timedelta

def lookup_ip (cur: cursor, conn: connection, hostname: str, 
               cache_expiry: timedelta = timedelta(days=1)):
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
    mapping = IPHostnameMapping(ip, hostname, now())
    mapping.write_to_db(cur, conn)
    # return the IP
    return ip
    
# lookup_ip(my_cursor, my_connection, 'wikipedia.org')


# In[27]:


def url_to_alpha2 (cur: cursor, conn: connection, url: str) -> Optional[Alpha2]:
    hostname = get_hostname(url)
    maybe_ip = lookup_ip(cur, conn, hostname)
    if maybe_ip is None:
        return None
    return ip_to_alpha2(maybe_ip)

# url_to_alpha2(my_cursor, my_connection, 'https://wikipedia.org/')


# ## Get TLD jurisdiction

# In[29]:


from imp import reload
from src.w3techs import utils as w3techs_utils
reload(w3techs_utils)
from tldextract import extract
import idna


# In[30]:


def get_tld_jurisdiction (url: str) -> Optional[Alpha2]:
    '''
    Takes a URL and gets an Alpha 2
    representing the jurisdiction of the URL's top-level domain.
    '''
    # sometimes, URL is an IP - that's fine
    hostname = get_hostname(url)
    try:
        IP(hostname) # if this doesn't throw an exception
        return None
    except:
        pass
    # decode IDNA (internationalized) hostnames
    # e.g. http://xn--80aaifmgl1achx.xn--p1ai/
    decoded_hostname = idna.decode(hostname)
    tld = extract(decoded_hostname)
    # get last item in url
    # e.g., '.com.br' should be '.br'
    tld = tld.suffix
    cc_tld = tld.split('.')[-1]
    # put it
    cc_tld_str = f'.{cc_tld}'
    cc =  w3techs_utils.get_country(cc_tld_str)
    if cc is not None:
        return Alpha2(cc)
    logger.warning(f'No TLD jurisidiction found for {url}')
    return None

get_tld_jurisdiction('http://mycool.com.br')
get_tld_jurisdiction('https://1.1.1.1/dns-query?dns=q80BAAABAAAAAAAAA3d3dwdleGFtcGxlA2NvbQAAAQAB')
get_tld_jurisdiction('http://xn--80aaifmgl1achx.xn--p1ai/')


# # Model the datatype

# In[31]:


import pandas as pd

def now () -> pd.Timestamp:
    return pd.Timestamp.utcnow()

def is_in_future (timestamp: pd.Timestamp) -> bool:
    return timestamp > now()

is_in_future(  pd.Timestamp('2021-06-24T20:36:06Z'))


# In[32]:



class OONIWebConnectivityTest():
    '''
    Class to capture results of an OONI web connectivity test.
      - https://ooni.org/nettest/web-connectivity/
    See README for more details on these fields.
    
    This is where validation happens.
    TODO - Check for SQL injection attacks.
    '''
    def __init__(self,
                  blocking_type: str,
                  probe_alpha2: Alpha2,
                  input_url: str,
                  anomaly: bool,
                  confirmed: bool,
                  report_id: str,
                  input_ip_alpha2: Alpha2,
                  tld_jurisdiction_alpha2: Alpha2,
                  measurement_start_time: pd.Timestamp):
            # we only want stuff where blocking actually happened 
            assert(blocking_type != False)
            self.blocking_type = blocking_type
            
            assert(type(probe_alpha2) == Alpha2)
            self.probe_alpha2 = str(probe_alpha2)
            
            assert(is_nonempty_str(input_url))
            self.input_url = input_url
            
            assert(type(anomaly) == bool)
            self.anomaly = anomaly
            
            assert(type(confirmed) == bool)
            self.confirmed = confirmed
            
            assert(is_nonempty_str(report_id))
            self.report_id = report_id
            
            # type is optional
            assert((type(input_ip_alpha2) == Alpha2) or 
                   (input_ip_alpha2 == None))
            if input_ip_alpha2 == None:
                self.input_ip_alpha2 = None
            else:
                self.input_ip_alpha2 = str(input_ip_alpha2)
            
            # type is optional
            assert((type(tld_jurisdiction_alpha2) == Alpha2) or
                   (tld_jurisdiction_alpha2 == None))
            if tld_jurisdiction_alpha2 == None:
                self.tld_jurisdiction_alpha2 = None
            else:
                self.tld_jurisdiction_alpha2 = str(tld_jurisdiction_alpha2)
            
            assert(type(measurement_start_time) == pd.Timestamp)
            # if the timestamp is in the future...
            if is_in_future(measurement_start_time):
                logger.debug(f'Time is in future: {measurement_start_time}. Setting time to now.')
                # set the time to now.
                self.measurement_start_time = now()
            # otherwise
            else:
                # set it to whenever it was reported
                self.measurement_start_time = measurement_start_time
            
    def create_table(
            self,
            cur: cursor,
            conn: connection):
        cmd = """
          CREATE TABLE ooni_web_connectivity_test (
             blocking_type             VARCHAR,
             probe_alpha2              CHAR(2) NOT NULL,
             input_url                 VARCHAR NOT NULL,
             anomaly                   BOOLEAN NOT NULL,
             confirmed                 BOOLEAN NOT NULL,
             report_id                 VARCHAR NOT NULL,
             input_ip_alpha2           CHAR(2),
             tld_jurisdiction_alpha2   CHAR(2),
             measurement_start_time    TIMESTAMPTZ NOT NULL
          )
        """
        cur.execute(cmd)
        conn.commit()

    def write_to_db(
            self,
            cur: cursor,
            conn: connection,
            commit=True,
    ):
        cur.execute(
            """
            INSERT INTO ooni_web_connectivity_test
            (blocking_type, probe_alpha2, input_url, anomaly, confirmed, report_id,  
            input_ip_alpha2, tld_jurisdiction_alpha2, measurement_start_time)   
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)   
            """, (self.blocking_type,
                  self.probe_alpha2,
                  self.input_url,
                  self.anomaly,
                  self.confirmed,
                  self.report_id,
                  self.input_ip_alpha2,
                  self.tld_jurisdiction_alpha2,
                  self.measurement_start_time))
        if commit:
            return conn.commit()
        return

    def __str__(self):
        # TODO make DRY with write_to_db?
        # TODO do this in general?
        return f'{self.measurement_start_time} - {self.probe_alpha2} -> {self.input_ip_alpha2}, {self.tld_jurisdiction_alpha2} ({self.blocking_type} {self.input_url})'

    def __repr__(self):
        return self.__str__()


# # Marshall from datatype

# In[33]:


def ingest_api_measurement (measurement: dict) -> OONIWebConnectivityTest:
    # make a connection and cursor (for this thread)
    connection = psycopg2.connect(**config['postgres'])
    cursor = connection.cursor()
    blocking_type = get_blocking_type(measurement)
    probe_alpha2 = Alpha2(measurement['probe_cc'])
    input_url = measurement['input']
    anomaly = measurement['anomaly']
    confirmed = measurement['confirmed']
    report_id = measurement['report_id']
    input_ip_alpha2 = url_to_alpha2(cursor, connection, input_url) 
    tld_jurisdiction_alpha2 = get_tld_jurisdiction(input_url)
    measurement_start_time = pd.Timestamp(measurement['measurement_start_time'])
    return OONIWebConnectivityTest(
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

# ingest_api_measurement(measurements[0])


# In[34]:


from multiprocessing import Pool
from typing import List

def ingest_api_measurements (measurements: List[dict]) -> List[OONIWebConnectivityTest]:
    with Pool() as p:
        return p.map(ingest_api_measurement, measurements)


# # Test it with the DB

# In[35]:


# In[37]:


def rollback():
    my_cursor.execute("ROLLBACK")
    my_connection.commit()


# In[42]:


# rollback()
# test = None
# for mt in my_types:
#     try:
#         mt.write_to_db(my_cursor, my_connection, commit=False) 
#     except Exception as e:
#         test = mt
#         print(mt)
#         print(e)
#         break
        


# In[38]:


# my_connection.commit()


# # Set up a flow

# In[73]:


from datetime import datetime

def get_latest_reading_time (cur: cursor) -> Optional[datetime]:
    '''Get time of most recent measurement'''
    try:
        cur.execute('SELECT measurement_start_time from ooni_web_connectivity_test ORDER BY measurement_start_time DESC')
        return cur.fetchone()[0]
    except TypeError:
        logger.info('No recent measurement found!')
        return None
    
most_recent_reading = get_latest_reading_time(my_cursor)
most_recent_reading, to_utc(most_recent_reading)


# In[76]:


import pytz

def query_measurements_after (time: datetime, **kwargs) -> list:
    '''Queries all measurements after time.'''

    def fmt_dt (t: datetime):
        return t.strftime("%Y-%m-%dT%H:%M:%S")
    # format timezone-aware date into UTC fo querying
    utc_dt = to_utc(time)
    # format it into the query url
    dt_str = fmt_dt(utc_dt)
    query_str = base_query + f'&since={dt_str}'
    # issue the query
    return api_query(query_str, **kwargs)

# ms  = query_measurements_after(most_recent_reading)


# In[81]:


def write_to_db (cur: cursor, conn: connection, connectivity_tests: List[OONIWebConnectivityTest]) -> None:
    for t in connectivity_tests:
        t.write_to_db(cur, conn, commit=False)
    conn.commit()


# # Tying it all together

# In[ ]:


# initial query.... try it out


# In[83]:


ms = query_recent_measurements()


# In[87]:


def scrape (cur: cursor, conn: connection) -> None:
    maybe_t = get_latest_reading_time(cur)
    if maybe_t is None:
        logger.info('Querying recent measurements.')
        ms = query_recent_measurements()
    else:
        logger.debug(f'Querying results after {maybe_t}.')
        ms = query_measurements_after(maybe_t)
    logger.debug(f'Retrieved {len(ms)} results.')
    ingested = ingest_api_measurements(ms)
    logger.debug(f'Ingested {len(ingested)} results.')
    write_to_db(cur, conn, ingested)
    logger.info(f'Wrote {len(ingested)} results to database.')


# In[88]:


# In[ ]:


while True:
    # TODO important that sleep happens syncronously rather than on schedule... we really don't know how long it will take to complete the scrape. how can we verify this with schedule one way or the other?
    scrape(my_cursor, my_connection)
    sleep(config['sleep-times']['ooni-poll'])

