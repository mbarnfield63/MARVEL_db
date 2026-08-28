# db_MARVEL

A structured relational database of **MARVEL** runs — the inputs and outputs of
the MARVEL algorithm (Measured Active Rotational-Vibrational Energy Levels;
Furtenbacher, Császár & Tennyson, *J. Mol. Spectrosc.* 245, 2007; Furtenbacher
& Császár, *JQSRT* 113, 2012) collected across many molecules, isotopologues,
and algorithm versions under one schema.

Each **run** is one inversion of measured transitions into empirical energy
levels: a molecule + an input transition set + an algorithm version → solved
levels plus per-transition solve state. Storing many runs together makes them
comparable, queryable, and traceable to their literature sources.

## Schema

Defined in [`db_layout.txt`](db_layout.txt) (dbdiagram.io DBML):
`molecules`, `marvel_versions`, `marvel_runs`, `source`, `energy_levels`,
`transitions`. See `CLAUDE.md` for a per-table summary.

## Running the database

Postgres in Docker, schema applied automatically on first start.

```sh
cp .env.example .env          # edit if you want non-default creds
docker compose up -d          # starts postgres:17, runs schema/schema.sql
docker compose ps             # wait for "healthy"
psql "$DATABASE_URL" -c '\dt' # 8 tables
```

Connect with the `DATABASE_URL` from `.env`
(`postgresql://marvel:marvel@localhost:5432/marvel` by default).

`schema/schema.sql` is applied by the container **only when the data volume is
empty**. After editing the schema, recreate the volume:

```sh
docker compose down -v && docker compose up -d
```

## Status

Schema drafted; Docker Compose Postgres skeleton in place. No loader yet — the
build is being charted with `/wayfinder`.

## Related repos (read-only sources)

- [`MARVEL_scraping`](https://github.com/mbarnfield63/scraping-for-marvel) — papers → MARVEL input files (MRT format)
- [`MARVEL_GNN`](https://github.com/mbarnfield63/MARVEL_GNN) — working Python port of MARVEL 4.1 core + GNN extensions
- [`MARVEL5`](https://github.com/mbarnfield63/MARVEL5) — independent v5 rewrite + graph-visualization app
- `C:\Code\versions_MARVEL` — MARVEL 3.0 / 3.1 / 4.1 C++ sources
- `C:\Code\_raw_data_store` — published MARVEL / ExoMol datasets

## Provenance

If you use MARVEL data or code, cite:

- Furtenbacher, T., Császár, A. G., & Tennyson, J. (2007). *J. Mol. Spectrosc.*, 245, 115–125.
- Furtenbacher, T., & Császár, A. G. (2012). *JQSRT*, 113, 929–935.
