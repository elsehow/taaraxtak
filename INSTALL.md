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

3. Copy `config.example.py` to `config.py` and enter your Postgres credentials. 
4. Run `python3 create-tables.py` to set up the database. (Alternatively, restore the database from a recent DB dump).

Now you can run `python3 collect.py` to start collecting data.

## Visualization frontend

### Make a grafanareader user in Postgres

Make a postgres user `grafanareader` with *read-only* permissions (important!).

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

1. Start Grafana server, and attach your Postgres database as a data source.
   (Important: [make a grafanareader user in
   Postgres](https://grafana.com/docs/grafana/latest/datasources/postgres/#database-user-permissions-important).
   That user should NOT have write access.)
2. In Grafana, make [an API key with Admin privileges](https://grafana.com/docs/grafana/latest/http_api/auth/)
3. Copy `grafana-backup.example.json` to `grafana-backup.json`. Fill in your API key.
3. `pip install grafana-backup`, then restore the dashboards with `grafana-backup --config=grafana-backup.json restore grafana/<archive_file>`.

Note: `grafana-backup` is installed via `requirements.txt` above.
