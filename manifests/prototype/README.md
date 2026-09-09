# Ingestion manifest format — prototype (ticket #5)

Mocks of the two candidate formats over **3 real papers** spanning the QN
schema types and the awkward cases. Files here are illustrative; the referenced
data files are not vendored yet.

| Paper (key) | Molecule | QN schema | Quirks exercised |
|---|---|---|---|
| `87Toth` | N2O (3 isotopologues) | linear triatomic Herzberg `v1 v2 l2 v3 J` | no segment file (`missing_segment`), 1 unc col |
| `16UnTeYu` | SO2 (3 isotopologues) | asymmetric top `v1 v2 v3 J Ka Kc` | trailing level cols (symmetry, block id), 1 unc col |
| `24YuMeSy` | SO (1 isotopologue) | diatomic electronic `State v ef J` | 2 unc cols, multi-electronic-state, mid-row `degree` col in level file |

- **Format 1 — flat registry:** [`registry.tsv`](registry.tsv)
- **Format 2 — per-publication:** [`by-publication/`](by-publication/) (`87Toth.yaml`, `16UnTeYu.yaml`, `24YuMeSy.yaml`)
- **Hybrid — generated index from Format 2:** [`index.tsv`](index.tsv)

## Trade-offs

### Format 1 — flat `registry.tsv`

**For:**
- One file, whole corpus visible. `grep`, `sort`, `awk`, spreadsheet all work.
- Add data = append one line. Diffs are one line.
- Mirrors MARVEL's own segment-file convention — familiar to the group.
- Loader input is trivial: `csv.DictReader(delimiter="\t")`.

**Against:**
- List/struct fields fight the format. `qn_names` and `level_colmap` become
  `|`-joined strings the loader must re-split — a second ad-hoc grammar inside a cell.
- Multi-isotopologue papers repeat the `bibtex_key` + every default across N rows
  (SO2 = 3 identical-but-for-isotopologue rows). Edit the version, edit it 3×.
- `sources:` (tag → unit → DOI, several per paper) has no clean home. Either a
  second file, or more `|`-packed cells.
- No natural place for per-dataset overrides (the SO `level_columns` case).
- One malformed row can wedge the whole corpus; no per-submission boundary.

### Format 2 — per-publication YAML

**For:**
- One folder = one reviewable submission. PRs are self-contained.
- `defaults:` block — declare shared fields once, override per dataset.
- Native lists/maps: `qn_names`, `level_colmap`, `sources:` all first-class.
- Room to grow (per-dataset `level_columns`, notes, provenance) without reworking a schema.
- JSON Schema validation catches errors at submit time, per file.

**Against:**
- N files to open to see the whole corpus (mitigated by the generated `index.tsv`).
- Contributors must write YAML correctly (indentation). Higher floor than "append a TSV line".
- Loader carries a YAML parser + schema validator (`pyyaml` + `jsonschema` — both cheap).
- Bikeshed surface: nesting depth, key names, where `defaults` stops applying.

### Hybrid

Author in Format 2, `make index` emits the read-only [`index.tsv`](index.tsv)
for the flat scan/grep view. Costs a build step and the rule "never edit index.tsv".

## Open questions for the group

1. Who writes manifests — you three, or outside contributors later? (sets the usability bar)
2. Is the whole-corpus grep view a real workflow, or a nice-to-have? (decides if the hybrid earns its build step)
3. `sources:` — in the manifest, or a separate per-paper `segments`-style file the loader already has to parse?
4. Is one-row-per-dataset (Format 1) or one-file-per-paper (Format 2) the unit a reviewer wants to look at?
