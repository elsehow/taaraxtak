# Install

# Pre-requisites

- Python 3.5 or higher
- Postgres 10 or higher
- Grafana server 7.5.4 or higher
- Rust 1.41.0 or higher

# First-time setup


## Collection Backend

### Database setup

Make sure Postgres is running. Create a postgres user with read and write access.

For example:

```
sudo -u postgres psql
create database taaraxtak;
CREATE USER scraper WITH PASSWORD '[unique-password-kept-in-password-manager]';
GRANT ALL PRIVILEGES ON DATABASE taaraxtak TO scraper;
```

Then, if you want to restore from a database backup:

```
psql -U scraper -d taaraxtak -h localhost < [your-database-dump].sql 
```


### Python

A [Python virtual environment](https://docs.python.org/3/library/venv.html) is recommended. Example setup below.

```
# create fresh virtualenv
python3 -m venv venv
# activate it
source venv/bin/activate
# install pre-reqs
pip3 install -r requirements.txt
```

3. Copy `config.example.py` to `config.py` and enter your Postgres credentials. See Config section below for info on
   logging options.
4. Run `python3 create_tables.py` to set up the database. (Alternatively, restore the database from a recent DB dump).

Now you can run `python3 collect.py` to start collecting data.

You can also run the data collection as separate one-time jobs:
- `python3 run.py w3techs`
- `python3 run.py ooni`

This makes it suitable to be run from a system cron, rather than as a standalone continuous process.

### Config

The example config file is set up for logging to the terminal (using the `coloredlogs` package for pretty formatting).
If you want to log to a file instead, you can set the `handler` to `file` and configure the path to the log file and
the format you want to use. An example is below:
```
    "logging": {
        "level": logging.DEBUG,
        "handler": "file",
        "format": "%(asctime)s [%(process)d:%(thread)d] %(levelname)-8s %(name)-30.30s %(message)s",
        "file": "/path/to/log/file"
    }
```
[See the Python module docs](https://docs.python.org/3/library/logging.html#logrecord-attributes) for more info on
specifying the log format.


## Visualization frontend

### Make a grafanareader user in Postgres

Make a postgres user `grafanareader` with *read-only* permissions (important!).
([See Grafana's docs on this](https://grafana.com/docs/grafana/latest/datasources/postgres/#database-user-permissions-important)).

```
sudo -u postgres psql
CREATE USER grafanareader WITH PASSWORD '[unique-password-kept-in-password-manager]';
GRANT CONNECT ON DATABASE taaraxtak TO grafanareader;
\c taaraxtak
\dt
GRANT USAGE ON SCHEMA public TO grafanareader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafanareader;
```

### Run grafana

1. [Install Grafana](https://grafana.com/docs/grafana/latest/installation/debian/)
2. Start Grafana server, (see link above).
3. Log in at http://localhost:3000/login - admin/admin. Then it'll prompt you to make a secure password.
4. [Add a datasource](https://grafana.com/docs/grafana/latest/datasources/add-a-data-source/). Add our PostgreSQL server and configure it with the database name `taaraxtak`, and the `grafanareader` user and password. (For testing locally, you may need to disable TLS/SSL). Press Save & Test and make sure the bottom shows a green "Database OK."
5. In Grafana, make [an API key](https://grafana.com/docs/grafana/latest/http_api/auth/). It should have Admin privileges. You can name it "grafana-backup." Leave TTL empty.
6. Copy `grafana-backup.example.json` to `grafana-backup.json`. Fill in your API key.
7. In your virtualenv, `pip install grafana-backup`, then restore the dashboards with `bash restore-grafana.sh`.

Now, go to Dashboard > Manage and you should see our dashboards.
