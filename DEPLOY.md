# Deployment

Currently, we deploy this project on a Linode instance. Only devops has direct access to this instance.

## Separating production and production

TLDR: We *never* develop on the production environment directly. We only interact with our local production environment.

Implications:

- Database. Set up your own Postgres instance locally. You can restore that database from a recent dump. 
    - The only thing that can write to the production database is the `collect.py` in taaraxtak production. 
        - Don't ask me for write access to the production database. I won't give it to you.
    - The only thing that can read from the production database is the `grafanareader` user, which is set up to Grafana. You can only see the production database through the Grafana database. 
        - Don't ask me for read access to the production database. I won't give it to you.
- Grafana: Set up your own Grafana instance locally. You can set that up from `grafana/` with `restore-grafana.sh`.
    - You can't edit the production Grafana dashboard directly. You'll have to use `backup-grafana.sh** to write your changes, commit them, and open an PR.

## What happens if something goes wrong in the production database?


If something has gone wrong in the production database, here are the steps to correct it:

1. ***Contact devops**. (For now, that's me). Only the database administrator can drop rows or delete data. 
    - What went wrong?
    - Why did it go wrong? (Inadequate testing? Inadequate validation? etc...)
2. You and devops work together to write a before-action-report
    - What is the problem?
    - What will we do to fix the problem? List steps.
    - How will we assess that the problem has been fixed?
3. Database administrator will carry out the steps from the before-action report.
4. Database administrator will produce an after-action report.
    - What did we expect to happen?
    - What actually happened?
