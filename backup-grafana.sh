#!/bin/bash
rm grafana/*.tar.gz
grafana-backup --config=grafana-backup.json --components=dashboards save
