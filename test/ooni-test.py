import psycopg2
import testing.postgresql
import pytest
from IPy import IP
import pandas as pd


from datetime import datetime
from datetime import timedelta


import src.ooni.utils as ooni_utils
import src.ooni.types as ooni_types
import src.shared.types as shared_types


# TODO make DRY with other test - test utils?
@pytest.fixture(scope='function')
def postgresdb(request):
    '''Postgres testing mock'''
    postgresql = testing.postgresql.Postgresql()
    conn = psycopg2.connect(**postgresql.dsn())
    cur = conn.cursor()
    ooni_types.create_tables(cur, conn)

    def teardown():
        postgresql.stop()

    request.addfinalizer(teardown)

    return (cur, conn)


# def my_db_enabled_test (postgresdb):
#     return

def test_to_utc():
    t = datetime(2021, 5, 27, 21, 40, 17, 486566)
    t_utc = ooni_utils.to_utc(t)
    assert(t_utc.hour == 4)


def test_query_ooni():
    ms = ooni_utils.query_recent_measurements(max_queries=1)
    assert(len(ms) > 1)
    # should not error
    ooni_utils.get_blocking_type(ms[0])
    ms = ooni_utils.query_measurements_after(datetime.now(), max_queries=1)


def test_get_hostname():
    assert(ooni_utils.get_hostname('http://daylight.berkeley.edu/cool-article') == 'daylight.berkeley.edu')


def test_fetch_ip():
    hn = ooni_utils.get_hostname('https://berkeley.edu')
    maybe_ip = ooni_utils.fetch_ip_from_hostname(hn)
    # should not error
    IP(maybe_ip)


def test_ip_to_alpha2():
    alpha2 = ooni_utils.ip_to_alpha2('35.163.72.93')
    assert(str(alpha2) == 'US')


def test_IPHostnameMapping(postgresdb):
    cur, conn = postgresdb
    my_ip = '198.35.26.96'
    t = ooni_utils.now()
    mapping = ooni_types.IPHostnameMapping(my_ip, 'wikipedia.org', t)
    with pytest.raises(Exception):
        mapping = ooni_types.IPHostnameMapping('xxx.xxx.xxx', 'wikipedia.org', t)
    mapping.write_to_db(cur, conn)
    # while we're here, test retrieve_ip and lookup_ip
    time_ip = ooni_utils.retrieve_ip(cur, 'wikipedia.org')[1]
    print(time_ip)
    assert(time_ip == my_ip)
    # lookup ip when cache IS VALID
    ip = ooni_utils.lookup_ip(cur, conn, 'wikipedia.org')
    assert(ip == my_ip)


def test_cache_expiry(postgresdb):
    # lookup ip when cache IS NOT VALID
    cur, conn = postgresdb
    my_ip = '162.00.00.01'
    t = ooni_utils.now() - timedelta(days=3)
    mapping = ooni_types.IPHostnameMapping(my_ip, 'wikipedia.org', t)
    mapping.write_to_db(cur, conn)
    ip = ooni_utils.lookup_ip(cur, conn, 'wikipedia.org')
    # should fetch the real address and deliver me something other than my fake one.
    assert(ip != my_ip)


def test_url_to_alpha2(postgresdb):
    # lookup ip when cache IS NOT VALID
    cur, conn = postgresdb
    # make a DB reading
    my_ip = '198.35.26.96'
    t = ooni_utils.now()
    mapping = ooni_types.IPHostnameMapping(my_ip, 'wikipedia.org', t)
    mapping.write_to_db(cur, conn)
    # look it up
    alpha2 = ooni_utils.url_to_alpha2(cur, conn, 'https://wikipedia.org/')
    assert(str(alpha2) == 'US')


def test_tld_juris():
    juris = ooni_utils.get_tld_jurisdiction('http://mycool.com.br')
    assert(str(juris) == 'BR')
    juris = ooni_utils.get_tld_jurisdiction('https://1.1.1.1/dns-query?dns=q80BAAABAAAAAAAAA3d3dwdleGFtcGxlA2NvbQAAAQAB')
    assert(juris is None)
    # tricky one! internationalized URL
    juris = ooni_utils.get_tld_jurisdiction('http://xn--80aaifmgl1achx.xn--p1ai/')
    assert(str(juris) == 'RU')
    juris = ooni_utils.get_tld_jurisdiction('http://www.sansat.net:25461')
    assert(str(juris) == 'US')


def test_is_in_future():
    future = ooni_utils.now() + timedelta(days=5)
    assert(ooni_utils.is_in_future(future) is True)
    past = ooni_utils.now() - timedelta(days=5)
    assert(ooni_utils.is_in_future(past) is False)


def test_get_latest_reading_time(postgresdb):
    cur, conn = postgresdb
    my_time = pd.Timestamp('2000-01-01 21:41:37+00:00')
    dummy = ooni_types.OONIWebConnectivityTest(
        'example',
        shared_types.Alpha2('US'),
        'example',
        False,
        False,
        'example',
        shared_types.Alpha2('US'),
        shared_types.Alpha2('US'),
        my_time
    )
    dummy.write_to_db(cur, conn)
    most_recent_reading = ooni_utils.get_latest_reading_time(cur)
    assert(most_recent_reading == my_time)
