# Install

## Pre-requisites

- Python 3.5 or higher
- Postgres 10 or higher
- Grafana server 7.5.4 or higher
- Rust 1.41.0 or higher

## First-time setup

### Backend

A [Python virtual environment](https://docs.python.org/3/library/venv.html) is recommended.

0. Upgrade pip with `python -m pip install --upgrade pip`.
1. Install pre-requisites with `pip3 install -r requirements.txt`. 
2. Make sure Postgres is running. Make a database and a user with write access.
3. Copy `config.example.py` to `config.py` and enter your credentials. 
4. Set up the database with `python3 create-tables.py`. 

## Frontend

1. Start Grafana server, and attach your Postgres database as a data source.
   (Important: [make a grafanareader user in
   Postgres](https://grafana.com/docs/grafana/latest/datasources/postgres/#database-user-permissions-important).
   That user should NOT have write access.)
2. In Grafana, make [an API key with Admin privileges](https://grafana.com/docs/grafana/latest/http_api/auth/)
3. Copy `grafana-backup.example.json` to `grafana-backup.json`. Fill in your API key.
3. `pip install grafana-backup`, then restore the dashboards with `grafana-backup --config=grafana-backup.json restore grafana/<archive_file>`.

Note: `grafana-backup` is installed via `requirements.txt` above.
