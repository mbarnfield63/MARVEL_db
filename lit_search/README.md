# MARVEL citing-papers literature search

Ranked worklist of published papers that cite the MARVEL method and are likely to
contain usable MARVEL spectroscopic data (measured transitions and/or empirical
rovibrational energy levels for a molecule/isotopologue).

**Generated:** 2026-08-27
**Deliverable:** `lit_search/marvel_citing_papers.tsv`
**Scope:** worklist only — no PDFs fetched, no transition data extracted.

## Seed works

| Paper | DOI | OpenAlex id | citing works |
|---|---|---|---|
| Furtenbacher, Császár & Tennyson (2007), *MARVEL: measured active rotational–vibrational energy levels*, J. Mol. Spectrosc. 245, 115–125 | 10.1016/j.jms.2007.07.005 | `W2139332694` | 284 |
| Furtenbacher & Császár (2012), *MARVEL II: algorithmic improvements*, JQSRT 113, 929–935 | 10.1016/j.jqsrt.2012.01.005 | `W2168850167` | 147 |
| Tóbiás, Furtenbacher, Tennyson & Császár (2019), *Accurate empirical rovibrational energies and transitions of H2 16O*, PCCP 21, 3473 | 10.1039/C8CP05169K | `W2909363400` | 77 |

Union of the three citing sets, deduplicated by OpenAlex work id: **309 unique works**
(a secondary dedup by DOI found no additional collisions; 11 works have no DOI).

## has_marvel_data_guess tier counts

| tier | count |
|---|---|
| high | 137 |
| medium | 67 |
| low | 105 |
| **total** | **309** |

`high`   = title/abstract shows the paper itself runs a MARVEL analysis, produces
           empirical (rovibrational) energy levels / a validated transition dataset
           for a species, or is a known ExoMol/MARVEL data paper (ExoMol line-list
           papers, ExoMolHR, IUPAC water evaluations, W2020, term-energy/Ritz analyses).
`medium` = spectroscopy / PES / line-list paper on a specific molecule that plausibly
           contributed to or applied MARVEL data, but the abstract does not make it clear.
`low`    = cites the method in passing — reviews, atmospheric/exoplanet modelling,
           partition-sum / database aggregations, unrelated theory.

## data_location (best guess, not verified — no links chased)

SI 121 · unknown 152 · journal table 15 · CDS/VizieR 12 · ExoMol 5 · Zenodo 4

Heuristic: recent (>=2016) high-tier JQSRT/PCCP/JMS/MNRAS papers → SI; "Zenodo"
mentioned in abstract → Zenodo; pre-2014 → journal table; ExoMol-related medium → ExoMol;
astronomy journals → CDS/VizieR; otherwise unknown.

## Ranking

Rows are sorted: `high` before `medium` before `low`; within a tier, newest
`publication_year` first, then first-author family name. `rank` is the 1-based row number.

## Method

1. Resolved each seed DOI to an OpenAlex work id via
   `https://api.openalex.org/works/doi:<DOI>`.
2. Fetched every citing work for each seed id, cursor-paginated at 200/page:
   ```
   https://api.openalex.org/works?filter=cites:<ID>&per-page=200&cursor=*&mailto=mbarnfield63@gmail.com&select=id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,type
   ```
   following `meta.next_cursor` until exhausted. Raw JSON pages were kept in a
   scratchpad directory outside the repo.
3. Unioned the three result sets, deduplicated by OpenAlex id (then by DOI).
4. For each work: reconstructed the abstract from `abstract_inverted_index`;
   scanned title + abstract for ~110 molecule formulae / names; assigned
   `has_marvel_data_guess` and `data_location` by keyword rules; wrote free-text notes
   (isotopologue counts, "ExoMol line list paper", "MARVEL in title", review flag, etc.).
5. Ranked and wrote the TSV.

### Exact API calls run

```
curl -s 'https://api.openalex.org/works/doi:10.1016/j.jms.2007.07.005?mailto=mbarnfield63@gmail.com'
curl -s 'https://api.openalex.org/works/doi:10.1016/j.jqsrt.2012.01.005?mailto=mbarnfield63@gmail.com'
curl -s 'https://api.openalex.org/works/doi:10.1039/C8CP05169K?mailto=mbarnfield63@gmail.com'

# then, for ID in W2139332694 W2168850167 W2909363400, paginated with cursor:
curl -s 'https://api.openalex.org/works?filter=cites:<ID>&per-page=200&cursor=<CURSOR>&mailto=mbarnfield63@gmail.com&select=id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,type'
```

Pages fetched: W2139332694 → 2, W2168850167 → 1, W2909363400 → 1.

## Caveats for a human reviewer

- `has_marvel_data_guess` is a title/abstract keyword guess. ExoMol line-list papers
  are classed `high` because they are known MARVEL-consuming data papers, but not all
  ship a re-usable MARVEL input+output set — the surest `high` rows are those with
  "MARVEL" or "empirical (rovibrational) energy levels" in the *title* (roughly the
  first ~60 rows).
- OpenAlex abstracts are sometimes null; those works are judged on the title alone.
- Molecule detection misses formulae broken up by OpenAlex title spacing
  (e.g. "14 N 2 16 O" is not caught as N2O).
- A few OpenAlex records are preprint/proceedings duplicates of a journal paper with a
  distinct DOI (e.g. two "Term Energy Analysis of Iron Monohydride" rows) — kept, since
  the ticket dedups by OpenAlex id.
- `data_location` is inferred from journal + era only; no links were checked.
