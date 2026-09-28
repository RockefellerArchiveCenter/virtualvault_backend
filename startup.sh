#!/bin/sh

set -e

echo "Starting cron"
crond -b

echo "Running update"
python -m src.update

echo "Starting httpd"
httpd -D FOREGROUND