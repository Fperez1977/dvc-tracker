#!/bin/sh
# Keeps the SQLite database and uploaded purchase agreements on the
# /app/data volume (mounted from the Synology host) so they survive
# container recreation, upgrades, and restarts, without requiring any
# changes to app.py's relative-path assumptions.
set -e

mkdir -p /app/data/purchase_agreements

# First run: seed the data volume from anything baked into the image.
if [ ! -e /app/data/dvc_tracker.db ] && [ -e /app/dvc_tracker.db ]; then
    mv /app/dvc_tracker.db /app/data/dvc_tracker.db
fi

ln -sfn /app/data/dvc_tracker.db /app/dvc_tracker.db
rm -rf /app/purchase_agreements
ln -sfn /app/data/purchase_agreements /app/purchase_agreements

exec "$@"
