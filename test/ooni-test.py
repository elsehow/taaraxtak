import psycopg2
import testing.postgresql
import pytest
from IPy import IP

from datetime import datetime

import src.ooni.utils as ooni_utils
import src.ooni.types as ooni_types


# TODO make DRY with other test - test utils?
@pytest.fixture(scope='function')
def postgresdb (request):
    '''Postgres testing mock'''
    postgresql = testing.postgresql.Postgresql()
    conn = psycopg2.connect(**postgresql.dsn())
    cur = conn.cursor()
    types.create_tables(cur, conn)

    def teardown():
        postgresql.stop()

    request.addfinalizer(teardown)

    return (cur, conn)


# def my_db_enabled_test (postgresdb):
#     return

def test_to_utc ():
    t = datetime(2021, 5, 27, 21, 40, 17, 486566)
    t_utc = ooni_utils.to_utc(t)
    assert(t_utc.hour == 4)

def test_is_nonempty_str ():
    ok = ooni_utils.is_nonempty_str('hi')
    assert(ok == True)
    not_ok = ooni_utils.is_nonempty_str('')
    assert(not_ok == False)
    not_ok = ooni_utils.is_nonempty_str(5)
    assert(not_ok == False)

def test_alpha2_codes ():
    ok = ooni_types.Alpha2('US')
    assert(str(ok) == 'US')
    with pytest.raises(Exception):
        not_ok = ooni_types.Alpha2('blah')
        not_ok = ooni_types.Alpha2()
        not_ok = ooni_types.Alpha2(5)

# def test_query_ooni ():
#     ms = ooni_utils.query_recent_measurements(max_queries=1)
#     assert(len(ms) > 1)
#     # should not error
#     ooni_utils.get_blocking_type(ms[0])

def test_get_hostname ():
    assert(ooni_utils.get_hostname('http://www.wikipedia.org')=='wikipedia.org')

def test_fetch_ip ():
    hn = ooni_utils.get_hostname('http://www.wikipedia.org')
    maybe_ip = ooni_utils.fetch_ip_from_hostname(hn)
    # should not error
    IP(maybe_ip)


