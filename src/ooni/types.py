import src.ooni.utils
import pandas as pd
from IPy import IP

from psycopg2.extensions import cursor
from psycopg2.extensions import connection

class Alpha2 ():
    '''
    Represents an ISO alpha-2 country code.
    '''
    def __init__(self,
                 country_code: str):
        assert(src.ooni.utils.is_nonempty_str(country_code))
        assert(len(country_code)==2)
        self.country_code = country_code

    def __str__(self):
        return f'{self.country_code}'

    def __repr__(self):
        return self.__str__()

#
# Cacheing IP
#
class IPHostnameMapping:
    def __init__ (
        self,
        ip: str,
        hostname: str,
        time: pd.Timestamp,
    ):
        assert(src.ooni.utils.is_nonempty_str(hostname))
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


def create_tables (cur: cursor, conn: connection):
    IPHostnameMapping('198.35.26.96', 'wikipedia.org', src.ooni.utils.now()).create_table(cur, conn)
