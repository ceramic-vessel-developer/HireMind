#!/bin/bash
set -e
export PGHOST=axela-addons-api-server.postgres.database.azure.com
export PGUSER=$DBUSER
export PGPORT=5432
export PGDATABASE=postgres
export PGPASSWORD=$DBPASS
apt update && apt install -y postgresql-client
psql -f db/db_generate.sql
uvicorn main:app --host 0.0.0.0 --port 8000