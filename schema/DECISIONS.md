# Schema v2 — decision record

Resolves [#3 Schema v2 — evolve db_layout.txt for ingestion](https://github.com/mbarnfield63/MARVEL_db/issues/3).
Grilling session 2026-08-28. `schema/schema.sql` is the executable output;
`db_layout.txt` mirrors it for dbdiagram.io.

## Grain

One `marvel_runs` row = one isotopologue's inversion (a molecule + an input
transition set + a MARVEL version). Multiple runs per isotopologue are
expected — version sweeps, testing — and are mostly unpublished, so
`publication_id` is nullable. A published paper contributes one run per
isotopologue.

## `dataset_hash` and run identity

`dataset_hash` = hex sha256 of the run's **primary data file**, normalised
first: LF line endings, each line right-stripped, single trailing newline.
Primary data file = the input transitions file when present, else the output
levels file ("the most upstream file this run has").

`run_files.sha256` separately stores each file's true raw bytes — nothing is
lost to normalisation.

Run identity / dedup key: `UNIQUE (molecule_id, version_id, dataset_hash)`.
Input-only reformatting produces a new hash by design (provenance).

## `publications` vs `source`

Separate tables, **no FK between them**. Join on `doi` when needed. A MARVEL
paper that is also a transition source gets a row in each; that is expected,
not a modelling error.

`publications` is keyed by `bibtex_key` (the human handle). The loader
resolves `doi` / `year` / `title` / `authors` / `journal` from the matching
entry in the **vendored** `data/refs/marvel.bib` (parsed with `bibtexparser`),
and stores that entry verbatim in `bibtex_raw`. **Hard fail if the key is not
in the bib** — this keeps the MARVEL section of the ExoMol bib complete as a
workflow discipline.

`source` is **global**: one row per `source_tag` (MRT tag with the trailing
`.n` stripped), deduped on `source_tag`, shared by every run that cites it.
`unit` defaults to `cm-1` on every row; the segment file overrides it when
present. `source.doi` comes from a bib lookup on `source_tag`, nullable,
non-fatal if absent.

## `run_files`

`file_role` ∈ `input_transitions | output_levels | segment | other` (the
`bibtex` role was dropped — the bib is one vendored repo file, not per-run).
One file per role per run (`UNIQUE (run_id, file_role)`); concatenate on load
if a paper splits a role across files. `rel_path` is repo-relative
(`data/<bibtex_key>/<molecule_slug>/…`) so it becomes an object-store key
later with no schema change.

## `completeness`

Three values: `complete` (input + output + segment), `missing_segment` (input
+ output, no segment), `output_only` (output levels only). Every run has
output levels, so `input_only` is impossible; a segment file without input is
also impossible. If messier real combinations appear, the documented fallback
is 3 booleans + a derived view — a build-time watch, not a decision to make
now.

## `marvel_versions`

Seed rows: `3`, `4`, `unknown`. Major version only. `release_date` nullable.
Manifest supplies a version string; loader looks it up and **hard-fails on an
unseeded value** (deliberate seed additions, no typo proliferation). Default
manifest value `unknown` when the paper does not state a version. No separate
`as_published` sentinel — `unknown` covers it.

## transition ↔ level linking

`energy_levels` are the parsed output levels; `energy` and `uncertainty` are
always populated. Each level gets a `qn_key` (canonical joined QN tokens,
per `MARVEL5/src/marvel5/parse.py._level_id` without the iso prefix) plus the
named `quantum_numbers` JSONB.

The loader matches each transition endpoint's QN tuple against `qn_key` within
the same run to resolve `upper_level_id` / `lower_level_id`. Both FKs are
**nullable** (revised during #7's real-data POC — confirmed against CO, CN,
CaOH: a transition can cite an endpoint state that was never solved into a
level at all, when that state's spectroscopic-network component never
connects to the absolute energy zero-point — "floating components," per
MARVEL's own theory, explicitly called out in 25MaElAb's text. This is not
missing/bad data and not the same thing as the negative-frequency
"excluded from the solve" convention — a null FK here just records "this
state was never resolved," no solving performed by the loader).

`output_only` runs have zero `transitions` rows.

## `quantum_numbers` JSONB

The manifest **must** declare `qn_names` — an ordered list — per run. The
loader zips it onto the even-split QN tokens to build the JSONB. **Hard fail**
if `qn_names` is absent or its length does not match the token count. No
inference from token count, no built-in per-molecular-type map.

`qn_names` is stored on `marvel_runs` (run-level: every level in a run shares
the schema). QN tokens and JSONB values are **text** — many are non-numeric
(`b1Sig+`, `e`, `A+`). `qn_key` is used for linking and is name-independent.

## Output solve-state columns

Store the full published per-row solve state, nullable where it is
version-dependent (v3/v4 output files omit columns that MARVEL5 emits).

`energy_levels`: `energy` (NN), `uncertainty` (NN), `quantum_numbers` (NN),
`qn_key` (NN), `symmetry`, `n_transitions`, `consistency_flag`,
`component_id`. Dropped `nqn` (redundant with `qn_names` length) and `degree`
(taken to mean node degree = `n_transitions`).

`transitions`: `obs_freq` (NN, signed), `og_unc_freq`, `used_unc_freq`,
`residual`, `consistency_flag`, `uncertainty_source`, `removed`
(NN default false), `removed_reason`, `note`.

## File-format variability

Confirmed against real published files (SO₂, SO, CO₂):

- Some transition files carry trailing flag/comment columns *after* the tag
  (`… 10UlBeGrAl.223   DE   BAD EHM`). The tag must be found by pattern
  (`^(?P<key>.+)\.(?P<n>\d+)$`), not as the last token; trailing tokens go to
  `transitions.note`.
- Input files have **1 or 2** uncertainty columns (SO₂: 1; SO, CO₂: 2).
  Autodetection is unreliable (a QN token can look like a float), so the
  manifest carries an `n_unc_cols` hint; 1 → `og_unc_freq = used_unc_freq`.
  **(spec'd in #5 / #6.)**
- Energy-level files carry a symmetry label and a trailing integer
  (component/block id) after `energy`/`uncertainty`. Column mapping beyond
  `<QN…> energy uncertainty` is a loader concern, possibly manifest-hinted.
  **(spec'd in #5 / #6.)**

Schema absorbs this via `transitions.note` and `energy_levels.symmetry`; the
rest is punted to the manifest format (#5) and loader design (#6).

## Re-load / idempotency

Default: a load that hits an existing `(molecule_id, version_id,
dataset_hash)` **skips**, logs the existing `run_id`, exits 0. `--force`
does `DELETE FROM marvel_runs WHERE id = N` (children cascade) and reloads.
No partial-update path. Each run loads in **one transaction** — commit or
roll back whole. Shared tables (`molecules`, `publications`, `source`) never
cascade-delete.

## `molecules`

Manifest supplies `formula` + `isotopologue` (ExoMol form). Loader derives
`slug`. `inchi_key` is nullable and manifest-optional (no chemistry toolkit
in the POC). Dedupe on `isotopologue`.

## Constraints and indexes

`UNIQUE`: `molecules.isotopologue`, `molecules.slug`, `molecules.inchi_key`,
`marvel_versions.version`, `publications.bibtex_key`, `publications.doi`,
`source.source_tag`, `marvel_runs (molecule_id, version_id, dataset_hash)`,
`run_files (run_id, file_role)`, `energy_levels (run_id, qn_key)`,
`transitions (run_id, source_id, source_number)` (hard-fail on violation —
MARVEL tags are meant to be unique).

`ON DELETE CASCADE` on `run_id` FKs only (`energy_levels`, `transitions`,
`run_files`). All other FKs restrict.

Indexes: `energy_levels(run_id)`, GIN on `energy_levels.quantum_numbers`,
`transitions(run_id)`, `transitions(upper_level_id)`,
`transitions(lower_level_id)`, `transitions(source_id)`.

## Enums

`varchar + CHECK (col IN (…))`, not native PG `ENUM` — one-line edits, and
the volume is recreated on schema change anyway.

## Migration mechanism

Raw `schema/schema.sql`, mounted into the Postgres container's
`/docker-entrypoint-initdb.d/` (#4). No Alembic/sqitch for the POC — schema
is pre-1.0 and there is no production data. Recreate the volume on change.
Adopt Alembic post-POC with the then-current schema as the baseline.
`db_layout.txt` is kept in sync by hand as the dbdiagram.io visual.

## Read-only API role (2026-09-22, task, not grilled)

Added `marvel_readonly`: `CONNECT` + `USAGE` on `public` + `SELECT` on all
current and future tables, via a second init script (`zz_api_role.sh`,
alphabetically after `schema.sql` so the tables it grants against already
exist). Separate from `POSTGRES_USER` (the loader's write role) so the
future API backend (see [db_MARVEL public API — architecture decisions](https://github.com/mbarnfield63/MARVEL_db/issues/18))
can never write, regardless of bugs in its own code. Password lives in
`MARVEL_READONLY_PASSWORD` (`.env`, gitignored) — not in `schema.sql` itself,
which is committed.
