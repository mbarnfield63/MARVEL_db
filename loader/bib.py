"""Vendored-bib lookup for `publications` rows.

Uses bibtexparser v1. Reads data/refs/marvel.bib (must be vendored from
C:\\Code\\bib\\MARVEL\\ — not present at POC start, see loader/DESIGN.md).
"""

from pathlib import Path

import bibtexparser

BIB_PATH = Path(__file__).parent.parent / "data" / "refs" / "marvel.bib"


def lookup_publication(bibtex_key: str, bib_path: Path = BIB_PATH) -> dict:
    """Return a `publications`-shaped dict (doi, year, title, authors,
    journal, bibtex_raw) for bibtex_key.

    Raises KeyError if bibtex_key isn't in the vendored bib — hard fail,
    no fallback.
    """
    with open(bib_path, encoding="utf-8") as f:
        db = bibtexparser.load(f)

    entry = db.entries_dict.get(bibtex_key)
    if entry is None:
        raise KeyError(f"{bibtex_key!r} not found in {bib_path}")

    year = entry.get("year")
    return {
        "bibtex_key": bibtex_key,
        "doi": entry.get("doi"),
        "year": int(year) if year and year.isdigit() else None,
        "title": entry.get("title"),
        "authors": entry.get("author"),
        "journal": entry.get("journal"),
        "bibtex_raw": entry["raw"] if "raw" in entry else _reconstruct_raw(entry),
    }


def _reconstruct_raw(entry: dict) -> str:
    """bibtexparser doesn't keep the original text; rebuild a minimal
    verbatim-enough entry for `publications.bibtex_raw`."""
    key = entry.get("ID", "")
    kind = entry.get("ENTRYTYPE", "article")
    fields = "\n".join(
        f"  {k} = {{{v}}}," for k, v in entry.items() if k not in ("ID", "ENTRYTYPE")
    )
    return f"@{kind}{{{key},\n{fields}\n}}"
