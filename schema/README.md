# schema/

- `schema.sql` — executable Postgres DDL, **the source of truth**. Applied via
  the Postgres container's `/docker-entrypoint-initdb.d/` (ticket #4).
- `db_layout.txt` (repo root) — dbdiagram.io DBML mirror, kept in sync by hand.
- `DECISIONS.md` — why the schema looks the way it does (grilling, 2026-08-28).

No migration tool for the POC. On schema change: edit `schema.sql`, mirror
into `db_layout.txt`, recreate the Postgres volume. Adopt Alembic post-POC.
