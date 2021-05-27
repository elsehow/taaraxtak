import psycopg2
import testing.postgresql
import pytest

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
    return t_utc.hour == 4

def alpha2_codes ():
    ok = ooni_types.Alpha2('US')
    with pytest.raises(Exception):
        not_ok = ooni_types.Alpha2('blah')
        not_ok = ooni_types.Alpha2()
        not_ok = ooni_types.Alpha2('5')

