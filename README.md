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

## API

Read-only HTTP API (FastAPI) in `api/`, connecting as the SELECT-only
`marvel_readonly` role via `API_DATABASE_URL`:

```sh
uv run --env-file .env uvicorn api.main:app   # docs at http://localhost:8000/docs
uv run python -m api.check                    # smoke check against it
```

`/molecules` → `/molecules/{slug}/runs` → `/runs/{id}/levels|transitions|files/{file_role}`,
plus `/publications`, `/sources`, `/marvel_versions`. Every JSON endpoint has a
response model in `/openapi.json`; file links also answer `HEAD`. Design: issues #18/#19.

## Loading data

One YAML manifest per publication in `manifests/by-publication/`, raw files in
`data/<bibtex_key>/` (see `manifests/README.md`):

```sh
uv run --env-file .env marvel-loader validate manifests/by-publication/25MaElAb.yaml
uv run --env-file .env marvel-loader load manifests/by-publication/25MaElAb.yaml
uv run --env-file .env marvel-loader list
```

Re-loading the same data under the same version is skipped, not duplicated.

## Status

- Postgres schema, loader, and read-only API working.
- 7 runs loaded from 6 publications, covering 6 isotopologues: 12C-16O, 13C-16O2,
  1H-2H-18O, 1H-16O-35Cl, 12C-14N, and 31P-14N (2 runs).
- All runs are version `unknown` for now; versions get filled in on a full
  re-load once version parsing exists for each source.
- Public website: [`MARVELdb_online`](https://github.com/mbarnfield63/MARVELdb_online),
  a static Astro site built from this API. Not live yet: the API needs a
  public HTTPS host first.

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
