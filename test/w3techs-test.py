import src.w3techs.utils as utils
import src.w3techs.types as types
import src.shared.types as shared_types
import src.w3techs.collect as collect

import pandas as pd
import numpy as np

import psycopg2
import testing.postgresql

import pytest


@pytest.fixture(scope='function')
def postgresdb(request):
    '''Postgres testing mock'''
    postgresql = testing.postgresql.Postgresql()
    conn = psycopg2.connect(**postgresql.dsn())
    cur = conn.cursor()
    types.create_tables(cur, conn)

    def teardown():
        postgresql.stop()

    request.addfinalizer(teardown)

    return (cur, conn)

#
# scraper tests
#


def read_html(pth):
    h = open(pth)
    h = '\n'.join(h.readlines())
    return h


def test_single_table():
    '''
    Read a page with a single table.
    '''
    html = read_html('./test/w3techs-html/ex-single-table.html')
    df = utils.extract_table(html, double_table=False)
    assert(len(df) == 102)


def test_double_table():
    '''
    Read a page with a double table.
    '''
    html = read_html('./test/w3techs-html/ex-double-table.html')
    df = utils.extract_table(html, True)
    assert(len(df) == 12)


#
#  types tests
#


def test_create_tables(postgresdb):
    cur, conn = postgresdb


def test_provider_marketshare_type(postgresdb):
    cur, conn = postgresdb

    ex_ms = types.ProviderMarketshare(
        'Foo', None, shared_types.Alpha2('NL'), 'all', 'ssl-certificate', 0.5, pd.Timestamp('2021-04-20')
    )
    ex_ms.write_to_db(cur, conn)

    cur.execute('SELECT * FROM provider_marketshare')
    item = cur.fetchone()
    assert(item[0] == 'Foo')


def test_pop_weighted_gini_type(postgresdb):
    cur, conn = postgresdb

    ex_g = types.PopWeightedGini(
        'all', 'ssl-certificate', 0.9, pd.Timestamp('2021-04-20')
    )

    ex_g.write_to_db(cur, conn)

    cur.execute('SELECT * FROM pop_weighted_gini')
    item = cur.fetchone()
    assert(item[1] == 'ssl-certificate')

#
#  utils tests
#


def test_sum_proportions():
    '''
    summing up the total proportion of Internet users, we should get about 1.
    '''
    for tot in utils.prop_net_users.sum():
        assert(1 - tot < 0.02)


def test_gini_fn():
    # when everyone has the same amount, gini should be 1
    assert(
        utils.gini(np.array([0.25, 0.25, 0.25, 0.25])) == 0
    )

    # when one person has everything, gini should be very nearly one
    one_person_has_everything = [1] + np.zeros(100).tolist()
    assert(
        1 - utils.gini(np.array(one_person_has_everything)) < 0.01
    )


def test_weighted_gini():
    marketshares = pd.Series([0.25, 0.25, 0.25, 0.25])
    population_shares = pd.Series([0.70, 0.10, 0.10, 0.10])
    assert(round(utils.weighted_gini(marketshares, population_shares), 2) ==
           0.20)


def test_compute_pop_weighted_gini(postgresdb):
    # if there's nothing, it should reutrn one
    cur, conn = postgresdb
    res = utils.population_weighted_gini(
        cur,
        'all',
        'fake-market',
        pd.Timestamp('2021-01-20'),
    )
    assert(res is None)

    # add a provider marketshare
    # tiny netherlands has 50% of the world's market
    types.ProviderMarketshare(
        'Foo', None, shared_types.Alpha2('NL'), 'all', 'ssl-certificate',
        0.5, pd.Timestamp('2021-04-20')
    ).write_to_db(cur, conn)
    # US has the rest
    types.ProviderMarketshare(
        'Foo', None, shared_types.Alpha2('US'), 'all', 'ssl-certificate',
        0.5, pd.Timestamp('2021-04-20')
    ).write_to_db(cur, conn)

    res = utils.population_weighted_gini(
        cur, 'all', 'ssl-certificate', pd.Timestamp('2021-04-20')
    )
    # should result in a gini of 0.99
    assert(round(res.gini, 2) == 0.99)

# NOTE: This test scrapes actual data from the web. Run with care.
def test_collect():
    postgresql = testing.postgresql.Postgresql()
    test_db_config = postgresql.dsn()
    conn = psycopg2.connect(**postgresql.dsn())
    cur = conn.cursor()
    types.create_tables(cur, conn)
    collect.collect(test_db_config)
