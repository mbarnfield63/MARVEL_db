# Loader design

Resolves [#6](https://github.com/mbarnfield63/MARVEL_db/issues/6). Full
implementation is out of scope here — that's the POC slice
([#7](https://github.com/mbarnfield63/MARVEL_db/issues/7)), blocked by this
ticket. This is the shape everything below builds against.

## Stack

Python + `psycopg` (v3), raw SQL, no ORM. Sibling repos (MARVEL5, MARVEL_GNN)
are already Python; the schema is 8 fixed tables with `schema.sql` as sole
source of truth (no migration tool per POC decision) — an ORM buys nothing
here.

## Parser reuse

`loader/parse.py`'s transitions parser is a copy-and-adapt of
`MARVEL5/src/marvel5/parse.py::parse_mrt_transitions` (sibling repo, read-only
reference — not an import dependency). Changes from the original:

- Strip solve-state fields (`removed`, `residual`, `uncertainty_used`, ...) —
  this loader stores published input, it doesn't solve.
- Tag extraction: regex, not last-token — this loader's files carry trailing
  flag/annotation columns (e.g. `note` in the `transitions` table) that
  MARVEL5's inputs don't. The tag regex splits at the trailing digit run
  (optional dot before it) rather than assuming a fixed shape — covers
  `49HeNa.1`, `06DiShWa1` (no dot), and synthetic/pseudo-transition tags
  like `PGOPHER-95LiCoxx-0-0.1` (seen in 20YiOwTe, used to bridge otherwise
  disconnected spectroscopic-network components — same idea as C3's
  `23MaQiDoPi_EH`). Each such synthetic tag still needs its own
  `sources[].tag` entry in the manifest, typically with no `doi`.
- QN split point is **not inferred**. The manifest already declares
  `qn_names`, so `nqn = len(qn_names)` is known upfront; the parser validates
  each line's QN-token count against `2 * nqn` and hard-fails on mismatch
  (see QN schema below).
- No leading Iso/Name columns before `freq` (unlike MARVEL5's inputs) — real
  MARVEL transitions files, whether author-supplied or an IOP MRT export,
  start the line with the frequency. Confirmed against all 5 POC papers'
  real files during #7; the original assumption (freq at token 2) was only
  ever checked against a synthetic fixture and silently misparsed every real
  file.

Output-levels file: one parser, always driven by a resolved `level_columns`
list. When the manifest gives `level_colmap` instead of `level_columns`, the
loader builds the full list itself: `qn_names + [energy, uncertainty] +
level_colmap`. No branching on which key the manifest used.

## CLI surface

Four commands:

- `load <manifest>` — parse, validate, insert.
- `validate <manifest>` — same checks, no DB writes (dry run).
- `list` — what's in the DB (runs, one line each).
- `show <run_id>` — one run's `load_report`: molecule, version, counts,
  warnings.

Nothing else for POC — no `delete`/`reload`; `docker compose down -v` is the
reset button.

## Idempotency

Keyed by `dataset_hash`, per the schema's `UNIQUE (molecule_id, version_id,
dataset_hash)` on `marvel_runs`:

- Same hash already loaded → no-op, log "already loaded, skipping".
- Different hash (edited file, new preprint version) → new run row, inserted
  clean. Old row is left alone; both coexist. No supersede/replace logic —
  correcting a bad load is a manual `DELETE` + reload, not loader behavior.

## Partial loads

`completeness` (`complete | missing_segment | output_only`) only gates which
files are *required* per `manifests/README.md`'s table — parsing logic is
identical across all three. `input_only` doesn't exist (every run has output
levels, decided in #3). The `segment` file, when present, is stored verbatim
in `run_files` (`file_role='segment'`) but never parsed for data — `unit` and
`doi` are always manifest-declared directly under `sources:`, consistent with
the schema's no-inference stance throughout.

## Bibtex

`bibtexparser` (v1, stable — not the still-pre-1.0 v2 rewrite). Loader looks
up `publication.bibtex_key` against the vendored `data/refs/marvel.bib`,
hard-fails on a missing key, else fills `publications` (doi, year, title,
authors, journal, `bibtex_raw`).

Note: `data/refs/marvel.bib` doesn't exist yet — only a README placeholder.
Must be vendored from `C:\Code\bib\MARVEL\` before `load` can run against real
data; `validate` can still run schema/parse checks without it failing on the
bib lookup if the manifest step is skipped, but `load` needs it.

## QN schema

No runtime inference — manifest's `qn_names` gives `nqn` directly. A
transition line whose QN-token count doesn't equal `2 * nqn` (asymmetric
upper/lower QN counts — electronic/hyperfine cases) is a **hard fail** for
now. A manual-review flag for that case is deliberately not built — no
concrete paper needs it yet; stays fog on the map (see "Not yet specified").

## Failure semantics

Transaction **per dataset**, not per manifest. A manifest may hold multiple
isotopologues (e.g. 87Toth: three); one bad dataset shouldn't block the
others. Each dataset's insert (run + files + levels + transitions) is one
transaction. `load` reports per-dataset success/fail/skip at the end,
non-zero exit if any dataset failed.
