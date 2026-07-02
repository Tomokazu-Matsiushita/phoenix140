#!/bin/bash
set -e
mkdir -p backups
if [ -f phoenix140.db ]; then
  timestamp=$(date +"%Y%m%d_%H%M%S")
  cp phoenix140.db "backups/phoenix140_${timestamp}.db"
  echo "Backup created: backups/phoenix140_${timestamp}.db"
else
  echo "phoenix140.db not found."
fi
