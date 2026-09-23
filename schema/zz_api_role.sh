#!/bin/bash
# Read-only Postgres role for the future API (ticket #20). Runs after
# schema.sql (docker-entrypoint-initdb.d executes *.sql/*.sh alphabetically,
# and "zz_" sorts last) so the GRANT below sees the real tables.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE marvel_readonly LOGIN PASSWORD '$MARVEL_READONLY_PASSWORD';
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO marvel_readonly;
    GRANT USAGE ON SCHEMA public TO marvel_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO marvel_readonly;
    ALTER DEFAULT PRIVILEGES FOR ROLE $POSTGRES_USER IN SCHEMA public
        GRANT SELECT ON TABLES TO marvel_readonly;
EOSQL
