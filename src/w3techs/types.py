# taaraxtak
# nick merrill
# 2021
#
# w3techs
# create-tables.py - defines the Postgres tables.
# (see file by the same name in repository's root).

from psycopg2.extensions import cursor
from psycopg2.extensions import connection
from typing import Optional

import pandas as pd

def is_nonempty_str (my_str: str) -> bool:
    return (type(my_str) == str) & (len(my_str)>0)

def is_float_0_1 (my_float: float) -> bool:
    return (type(my_float) == float) & (my_float>=0) & (my_float<=1)

class ProviderMarketshare ():
    '''
    Class for the table `provider marketshare`.

    This is where validation happens.

    TODO - Check for SQL injection attacks.
    '''
    def __init__ (self,
                  name: str,
                  url: Optional[str],
                  jurisdiction_alpha2: Optional[str],
                  market: str,
                  marketshare: float,
                  time: pd.Timestamp
    ):
        assert(type(name) == str)
        assert(len(name)>0)
        self.name = name

        if url == None:
            self.url = None
        else:
            assert(is_nonempty_str(url))
            self.url = url

        if jurisdiction_alpha2 == None:
            self.jurisdiction_alpha2 = None
        else:
            assert(type(jurisdiction_alpha2) == str)
            assert(len(jurisdiction_alpha2)==2)
            self.jurisdiction_alpha2 = jurisdiction_alpha2

        assert(is_nonempty_str(market))
        self.market = market

        assert(is_float_0_1(marketshare))
        self.marketshare = marketshare

        assert(type(time) == pd.Timestamp)
        self.time = time

    def create_table (
            self,
            cur: cursor,
            conn: connection,
    ):
        cmd = f'''
        CREATE TABLE provider_marketshare (
        name                VARCHAR NOT NULL,
        url                 VARCHAR,
        jurisdiction_alpha2 CHAR(2),
        market              VARCHAR NOT NULL,
        marketshare         NUMERIC NOT NULL,
        time                TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        '''
        cur.execute(cmd)
        conn.commit()

    def write_to_db (
            self,
            cur: cursor,
            conn: connection,
            commit=True,
    ):
        cur.execute(
            f"""
            INSERT INTO provider_marketshare
            (name, url, jurisdiction_alpha2, market, marketshare, time)
            VALUES
            (%s, %s, %s, %s, %s, %s)
            """, (self.name,
                  self.url,
                  self.jurisdiction_alpha2,
                  self.market,
                  self.marketshare,
                  self.time))
        if commit:
            return conn.commit()
        return

    def __str__ (self):
        return f'{self.name} {self.url} {self.jurisdiction_alpha2}  {self.market} {self.marketshare} {self.time}'

    def __repr__ (self):
        return self.__str__()

class PopWeightedGini ():
    '''
    Class for the table `pop_weighted_gini`.

    This is where validation happens.

    TODO - Check for SQL injection attacks.
    '''
    def __init__(self,
                 market: str,
                 gini: float,
                 time: pd.Timestamp,
    ):
        assert(is_nonempty_str(market))
        self.market = market

        assert(is_float_0_1(float(gini)))
        self.gini = gini

        assert(type(time) == pd.Timestamp)
        self.time = time

    def create_table (
            self,
            cur: cursor,
            conn: connection,
    ):
        cmd = f'''
        CREATE TABLE pop_weighted_gini (
        market              VARCHAR NOT NULL,
        gini                NUMERIC NOT NULL,
        time                TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        '''
        cur.execute(cmd)
        conn.commit()

    def write_to_db (
            self,
            cur: cursor,
            conn: connection,
            commit=True,
    ):
        cur.execute(
            f"""
            INSERT INTO pop_weighted_gini
            (market, gini, time)
            VALUES
            (%s, %s, %s)
            """, (self.market, self.gini, self.time))
        if commit:
            return conn.commit()
        return

    def __str__ (self):
        return f'{self.market} {self.gini} {self.time}'

    def __repr__ (self):
        return self.__str__()


def create_tables (cur: cursor, conn: connection):
    '''
    Create database tables for W3Techs data.
    '''

    # dummy data - just a demo
    ProviderMarketshare(
        'name', None, 'CA', 'ssl-certificate', 0.5, pd.Timestamp('2021-04-20')
    ).create_table(cur, conn)

    # dummy data - just a demo
    PopWeightedGini(
        'ssl-certificate', 0.9, pd.Timestamp('2021-04-20')
    ).create_table(cur, conn)
