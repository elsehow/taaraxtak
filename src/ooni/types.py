# taaraxtak
# nick merrill
# 2021
#
# ooni
# create-tables.py - defines the Postgres tables.
# (see file by the same name in repository's root).

import logging
import pandas as pd
from IPy import IP

import src.shared.utils as shared_utils
import src.shared.types as shared_types

from psycopg2.extensions import cursor
from psycopg2.extensions import connection


#
# Cacheing IP
#
class IPHostnameMapping:
    def __init__(
        self,
        ip: str,
        hostname: str,
        time: pd.Timestamp,
    ):
        assert(shared_utils.is_nonempty_str(hostname))
        self.hostname = hostname
        # this will throw if `ip` isn't valid
        parsed_ip = IP(ip)
        # check that it's a public IP!
        assert(parsed_ip.iptype() == 'PUBLIC')
        # we'll just save the IP as a string for simplicity's sake
        self.ip = parsed_ip.strNormal()
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
                  self.time))
        if commit:
            return conn.commit()
        return

    def __str__(self):
        return f'{self.time: self.hostname->self.ip}'


class OONIWebConnectivityTest():
    '''
    Class to capture results of an OONI web connectivity test.
      - https://ooni.org/nettest/web-connectivity/
    See README for more details on these fields.

    This is where validation happens.
    TODO - Check for SQL injection attacks.
    '''
    def __init__(
           self,
           blocking_type: str,
           probe_alpha2: shared_types.Alpha2,
           input_url: str,
           anomaly: bool,
           confirmed: bool,
           report_id: str,
           input_ip_alpha2: shared_types.Alpha2,
           tld_jurisdiction_alpha2: shared_types.Alpha2,
           measurement_start_time: pd.Timestamp
    ):
        # we only want stuff where blocking actually happened
        assert(blocking_type is not False)
        self.blocking_type = blocking_type

        assert(type(probe_alpha2) == shared_types.Alpha2)
        self.probe_alpha2 = str(probe_alpha2)

        assert(shared_utils.is_nonempty_str(input_url))
        self.input_url = input_url

        assert(type(anomaly) == bool)
        self.anomaly = anomaly

        assert(type(confirmed) == bool)
        self.confirmed = confirmed

        assert(shared_utils.is_nonempty_str(report_id))
        self.report_id = report_id

        # type is optional
        assert((type(input_ip_alpha2) == shared_types.Alpha2) or
               (input_ip_alpha2 is None))
        if input_ip_alpha2 is None:
            self.input_ip_alpha2 = None
        else:
            self.input_ip_alpha2 = str(input_ip_alpha2)

        # type is optional
        assert((type(tld_jurisdiction_alpha2) == shared_types.Alpha2) or
               (tld_jurisdiction_alpha2 is None))
        if tld_jurisdiction_alpha2 is None:
            self.tld_jurisdiction_alpha2 = None
        else:
            self.tld_jurisdiction_alpha2 = str(tld_jurisdiction_alpha2)

        assert(type(measurement_start_time) == pd.Timestamp)
        # if the timestamp is in the future...
        if shared_utils.is_in_future(measurement_start_time):
            logging.debug(f'Time is in future: {measurement_start_time}. Setting time to now.')
            # set the time to now.
            self.measurement_start_time = shared_utils.now()
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
        return f'{self.measurement_start_time} - {self.probe_alpha2} ->' +\
            ' {self.input_ip_alpha2}, {self.tld_jurisdiction_alpha2} ({self.blocking_type} {self.input_url})'

    def __repr__(self):
        return self.__str__()


def create_tables(cur: cursor, conn: connection):
    IPHostnameMapping('198.35.26.96', 'wikipedia.org', shared_utils.now()).create_table(cur, conn)
    # dummy data
    OONIWebConnectivityTest(
        'example',
        shared_types.Alpha2('US'),
        'example',
        False,
        False,
        'example',
        shared_types.Alpha2('US'),
        shared_types.Alpha2('US'),
        pd.Timestamp('2000-01-01 21:41:37+00:00')
    ).create_table(cur, conn)
