# db_MARVEL

## Project Purpose

This repository builds a **structured relational database of MARVEL runs** —
inputs and outputs of the MARVEL algorithm (Furtenbacher, Császár & Tennyson
2007; Furtenbacher & Császár 2012) across many molecules, isotopologues, and
algorithm versions, stored under one schema so runs can be compared,
re-queried, and traced back to their literature sources.

MARVEL inverts measured rotational-vibrational transitions into empirical
energy levels with well-defined uncertainties, via a spectroscopic network
(energy levels = nodes, transitions = edges). Every run here is one such
inversion: a molecule + an input transition set + an algorithm version →
solved energy levels plus the per-transition solve state (used uncertainty,
residual, consistency flag).

The target schema is defined in **`db_layout.txt`** (dbdiagram.io DBML). It is
the single source of truth for table/column structure — read it before
touching anything data-shaped.

This is a **sibling** of, not a dependency on, the other MARVEL repos in
`C:\Code` (see Data Sources). It consumes their outputs; it does not modify
them.

## Operating Rules

### 1. Initialize
When the user says **"get up to speed"**, immediately read the Obsidian state
file at `C:/Obsidian/Claude_State/db_MARVEL.md` to reconstruct full context.

### 2. Log & Save
When reaching a milestone or when the user says **"save state"**:
1. Overwrite the Obsidian state file (`C:/Obsidian/Claude_State/db_MARVEL.md`)
   with a clean update (see Rule 3 format).
2. Append a summary of work done to the log file
   (`C:/Obsidian/Logs/db_MARVEL Log.md`).
3. Once schema/loader code exists and a `graphify-out/` is present, run
   `graphify update .` so the knowledge graph reflects the session's changes.

Never change any other files within `C:/Obsidian/`.

### 3. Obsidian State File Format
When writing to `C:/Obsidian/Claude_State/db_MARVEL.md`, always overwrite with:

```
# db_MARVEL — Claude State

**Last Modified:** YYYY-MM-DD HH:MM

**Completed:**
- What's been built/decided/loaded since the last state save.

**Key decisions:**
- Anything decided this session not already captured in the wayfarer plan.

**Next Steps / Blockers:**
- Exactly what needs to be tackled next session, or what's blocking progress.
```

### 4. Git
Repo is not yet initialized. Once it is: suggest which files to stage and a
commit message written per the user's global style (one short sentence, no
Claude/Anthropic mentions), then stop and let the user commit. Never commit
raw datasets, DB files, or generated dumps — those belong in `.gitignore`.

## Schema (summary — `db_layout.txt` is authoritative)

| Table | Holds | Key points |
|---|---|---|
| `molecules` | one row per isotopologue | `formula` (`H2O`), `isotopologue` (`1H2-16O`), `inchi_key` unique, `slug` unique |
| `marvel_versions` | algorithm versions | `version` (`3.0`, `3.1`, `4.1`, `5.0`), `release_date` |
| `marvel_runs` | one MARVEL inversion | FK molecule + version, `run_timestamp`, `description`, `dataset_hash` (hash of the input files — dedup / provenance) |
| `source` | literature references | `source_tag` (ExoMol bib tag, `20BnTe.H2O`), `doi`, `unit` (`cm-1`, `MHz`) |
| `energy_levels` | solved levels of a run | FK run, `energy` (double, high precision), `nqn`, `quantum_numbers` JSONB, `degree` |
| `transitions` | input transitions of a run | FK run + source, `source_number`, `upper_level_id`/`lower_level_id` (FK energy_levels), `obs_freq`, `og_unc_freq` (as published), `used_unc_freq` (as used in the solve) |

Notes:
- `quantum_numbers` is JSONB precisely because the QN schema differs by
  molecular type (diatomic `v,J`; linear triatomic Herzberg `v1 v2 l2 v3, J`;
  asymmetric top `v1 v2 v3, J, Ka, Kc`; electronic/hyperfine variants). Do not
  flatten it into columns.
- A `(molecule, version, dataset_hash)` triple identifies a run; re-loading
  the same inputs under the same version should not create a duplicate.

## Data Sources

All read-only. Nothing here writes back to these repos.

| Path | What it provides |
|---|---|
| `C:\Code\MARVEL_scraping\molecules\<mol>\output\*.txt` | MRT-format MARVEL **input** files (transitions + QNs + source tags), produced from published papers |
| `C:\Code\_raw_data_store\` | Published MARVEL energy/state/trans files + Duo/ExoMol outputs, by molecular type (`Diatomics/`, `Triatomics/`) |
| `C:\Code\MARVEL_GNN` | Working Python port of MARVEL 4.1 core (parser, DFS components, WLS solver, bootstrap+Dijkstra uncertainty); validated on CO, CO2. Can generate runs. |
| `C:\Code\MARVEL5` | v5 engine (independent Python rewrite). Emits `<run>_levels.csv` / `<run>_transitions.csv` — column names map closely onto `energy_levels` / `transitions`. |
| `C:\Code\versions_MARVEL` | MARVEL 3.0 / 3.1 / 4.1.x C++ source + built `.exe`s — to reproduce historical-version runs |
| `C:\Code\bib\MARVEL\*.bib` | BibTeX for `source` rows (DOIs, tags) |

Obsidian context for the siblings (background reading, do not edit):
`C:/Obsidian/Claude_State/MARVEL{5, GNN, scraping}.md` and the matching
`C:/Obsidian/Logs/*.md`.

## Directory Structure

```
db_MARVEL\
├── db_layout.txt   # DBML schema — source of truth
├── CLAUDE.md        # this file
└── README.md        # project overview
```

Schema/loader/DB code does not exist yet — the build is charted next via
`/wayfarer`.
