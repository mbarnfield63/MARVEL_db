# Citing-papers review pipeline

Scripts used to content-review `../marvel_citing_papers.tsv` — locating each
paper's MARVEL input transitions and empirical energy levels and recording where
they live. **Nothing here downloads spectroscopic data**; it fetches metadata,
probes supplementary-material assets, and reads open-access PDFs of the papers
themselves.

High (ranks 1-137) and medium (138-204) are done. Low (205-309, 105 rows) is not.

Medium needed no browser sweep: the API pass plus `pdfscan.py` settled all 67 rows.
It kept 1 (rank 144, H216O reassessment) and dropped 66 — mostly PES/line-list,
ab initio, derived-use and measurement-source papers that cite MARVEL without
running it.

## Running a tier

The worklist is the **original** 9-column file
(`rank doi year first_author title molecules_mentioned has_marvel_data_guess
data_location notes`), which `../marvel_citing_papers.tsv` no longer is — it now
holds the rewritten output schema. Recover the worklist from git:

```sh
git log --oneline -- ../marvel_citing_papers.tsv    # find a pre-rewrite commit
git show <rev>:lit_search/marvel_citing_papers.tsv > worklist.tsv
```

Then, in order:

```sh
python bibmap.py                       # DOI -> ExoMol key map over C:\Code\bib\**\*.bib
python harvest.py worklist.tsv medium  # Crossref + Unpaywall + Zenodo + SI asset probes
python digest.py > digest.txt          # compact per-row digest for reading
python pdfscan.py > pdfscan.txt        # OA PDFs -> Data Availability / SI statements
# ... record verdicts in decisions.py, browser-sweep results in sweep.py ...
python build_tsv.py 138 204 medium_tier_rows.tsv   # rows for that rank range + needs-browser list
```

On Windows run with `PYTHONIOENCODING=utf-8`; the console codepage cannot print
the unicode in titles and abstracts.

`build_tsv.py` emits a tier fragment (rank range + output name as argv, default
`1 137 high_tier_rows.tsv`); the 3-line header lives in
`../marvel_citing_papers.tsv`, and kept rows are merged into it by hand in the
molecules A-Z / year-newest-first order.

`harvest.py` and `pdfscan.py` are resumable — both skip rows already cached, so
re-running after an interruption is cheap. Everything they write is gitignored.

## The two hand-maintained files

- **`decisions.py`** — one verdict per rank: keep, or drop with a reason.
  This is the judgment record; the rest of the pipeline is mechanical.
- **`sweep.py`** — results of the batched browser pass over rows whose
  supplementary listings the APIs cannot reach.

Both are keyed by the worklist `rank`. `decisions.py` covers ranks 1-204;
`sweep.py` holds the high tier only (medium needed no sweep).

## What worked, and what to reach for first

Fetching the OA PDF and grepping its Data Availability / Supporting Information
section answered the keep/drop question far more often than any metadata API
did — 63 PDFs cut a 137-row browser sweep down to 43. Run `pdfscan.py` before
reaching for the browser.

Publisher-specific notes, learned the hard way on the high tier:

| Publisher | Supplementary material |
|---|---|
| Elsevier | `ars.els-cdn.com/content/image/1-s2.0-<PII>-mmcN.<ext>` is HEAD-probeable, no browser needed — but captions are invisible, so filenames stay opaque |
| IOP / AAS | best case: MARVEL files published as machine-readable tables with clean per-table `_ascii.txt` URLs |
| RSC | clean `article-supplement/<id>/txt/<art>N_suppl/` URLs, but only on the `pubs.rsc.org/cp/article/...` page, never on `articlelanding` |
| ACS | per-file URLs |
| OUP | asset URLs are tokenised; link to the article page + `#supplementary-data`, and read the filename and caption from the DOM |
| Wiley, AIP | a single zip |
| Springer | `static-content.springer.com/esm/art%3A<doi>/MediaObjects/<art>_MOESMn_ESM.<ext>` is guessable and probeable |

OUP, ScienceDirect, IOP and RSC bot-block plain HTTP. Those are **bot-blocks,
not paywalls** — the browser pass exists to get past the blocking, not to buy
access.

`exomol.com` does not host `.marvel` files (checked via the site and its JSON
API). MARVELonline (`kkrk.chem.elte.hu/marvelonline/`) is live but login-gated,
so it is a manual-chase resource, never a recorded data link.
