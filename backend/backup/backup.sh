#!/bin/sh
set -e

echo "[$(date -Iseconds)] Starting backup..."

# Safe SQLite snapshot (atomic, won't corrupt during writes)
sqlite3 /data/stocks.db ".backup /backups/stocks.db"

# Sync images and videos
rsync -a --delete /data/images/ /backups/images/

echo "[$(date -Iseconds)] Backup complete"