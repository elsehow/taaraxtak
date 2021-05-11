#!/bin/bash
rm grafana/*.tar.gz
grafana-backup --config=grafana-backup.json --components=folders,dashboards,alert-channels save
git add grafana/*
