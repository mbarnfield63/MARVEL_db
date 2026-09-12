# Ingestion manifests

One YAML file per publication, at `manifests/by-publication/<bibtex_key>.yaml`.
Its data files live under `data/<bibtex_key>/`; every path in the manifest is
relative to that directory.

Format decided in
[#5](https://github.com/mbarnfield63/MARVEL_db/issues/5) — the rejected flat
`registry.tsv` alternative and the trade-offs are in `prototype/`.

## Shape

```yaml
publication:
  bibtex_key: 16UnTeYu        # resolved against data/refs/marvel.bib; loader hard-fails if missing

defaults:                     # any dataset field; inherited unless a dataset overrides it
  formula: SO2
  marvel_version: "3"
  completeness: complete
  n_unc_cols: 1
  qn_names: [v1, v2, v3, J, Ka, Kc]
  level_colmap: [n_transitions, symmetry, component_id]

datasets:
  - isotopologue: 32S-16O2
    files:
      input_transitions: Transitions_626.txt
      output_levels: EnergyLevels_626.txt
      segment: segments_626.txt

sources:                      # transition-origin refs; seeds the global `source` table
  - tag: 10UlBeGrAl
    unit: cm-1
    doi: 10.1016/j.jqsrt.2010.05.010
  - {tag: "74Ti", unit: cm-1}   # no DOI: pre-DOI or paper-internal
```

## Fields

Every dataset field may be declared in `defaults:` and overridden per dataset.
Required means required *after* the defaults merge.

| Field | Req | Notes |
|---|---|---|
| `publication.bibtex_key` | yes | The only publication field. Author/year/title/DOI come from the vendored bib. |
| `formula` | yes | `SO2` |
| `isotopologue` | yes | ExoMol form, `32S-16O2`. One dataset per isotopologue — that is the run grain. |
| `inchi_key` | no | |
| `marvel_version` | yes | String, matched against seeded `marvel_versions`. `unknown` when the paper does not say. |
| `completeness` | yes | `complete` \| `missing_segment` \| `output_only` — decides which files are required. |
| `n_unc_cols` | yes | `1` or `2`. Not autodetected. `1` → `og_unc_freq = used_unc_freq`. |
| `numeric_field_widths` | no | Fixed character widths for the leading `freq` + uncertainty column(s) in `input_transitions`, `len == 1 + n_unc_cols`. Only needed when those columns are right-justified without a guaranteed separator, so a short uncertainty value can glue onto the frequency with no space (e.g. `15961.7230.0246092`). Omit for normally space-delimited files. |
| `qn_names` | yes | Ordered list, zipped onto the even-split QN tokens. **No inference fallback** — absent = hard fail. |
| `level_colmap` | no | Trailing level-file columns after `energy`, `uncertainty`. Omit if there are none. |
| `level_columns` | no | Full explicit ordered level-file layout. Overrides `level_colmap`; use it when an extra column sits mid-row (e.g. `degree` before `energy` in 24YuMeSy). |
| `files.input_transitions` | see below | |
| `files.output_levels` | yes | A manifest with no output file is invalid. |
| `files.segment` | see below | |
| `sources[].tag` | yes | Segment-file tag, e.g. `10UlBeGrAl`. |
| `sources[].unit` | yes | Free text, whatever the segment file says — `cm-1`, `MHz`, `kHz` all seen in practice (25MaElAb's segment file has all three). |
| `sources[].doi` | no | Absent for pre-DOI or paper-internal measurements. |

Files required per `completeness`:

| `completeness` | input_transitions | output_levels | segment |
|---|---|---|---|
| `complete` | yes | yes | yes |
| `missing_segment` | yes | yes | — |
| `output_only` | — | yes | — |

## Deliberate omissions

- **No `index.tsv`.** The flat whole-corpus view is `grep -r manifests/by-publication/`
  before load and SQL after it. Regenerating a derived index costs a build step
  and buys nothing at POC scale; it can be added later with zero migration.
- **No JSON Schema yet.** The loader (#6) hard-fails on every missing or bad
  field anyway. Write the schema when outside contributors actually submit.
