# schema/

- `schema.sql` — executable Postgres DDL, **the source of truth**. Applied via
  the Postgres container's `/docker-entrypoint-initdb.d/` (ticket #4).
- `zz_api_role.sh` — creates the `marvel_readonly` role the future API backend
  connects as (ticket #20). Runs after `schema.sql` in the same
  `/docker-entrypoint-initdb.d/` pass (alphabetically last by design), reads
  `MARVEL_READONLY_PASSWORD` from the environment — see `.env.example`.
- `db_layout.txt` (repo root) — dbdiagram.io DBML mirror, kept in sync by hand.
- `DECISIONS.md` — why the schema looks the way it does (grilling, 2026-08-28).

No migration tool for the POC. On schema change: edit `schema.sql`, mirror
into `db_layout.txt`, recreate the Postgres volume. Adopt Alembic post-POC.
