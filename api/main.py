"""Public read-only HTTP API over db_MARVEL.

Design: GitHub issues #18/#19 (endpoint shape), #15/#16 (website needs).
Connects as the SELECT-only `marvel_readonly` role via API_DATABASE_URL, so
nothing here can write regardless of bugs.

Run: uv run uvicorn api.main:app --reload
Docs: /docs (Swagger UI), /openapi.json
"""

import os
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

# run_files.rel_path is repo-relative (schema/DECISIONS.md "run_files").
REPO_ROOT = Path(__file__).resolve().parents[1]
FILE_ROLES = ("input_transitions", "output_levels", "segment", "other")
MAX_LIMIT = 10_000

app = FastAPI(
    title="db_MARVEL API",
    description="Read-only access to MARVEL runs: molecules, runs, energy levels, "
    "transitions, raw published files, and their literature sources.",
    version="0.1.0",
)


def db():
    # ponytail: one connection per request, add psycopg_pool if load demands it
    with psycopg.connect(os.environ["API_DATABASE_URL"], row_factory=dict_row) as conn:
        yield conn


def one_or_404(row, what: str):
    if row is None:
        raise HTTPException(404, f"{what} not found")
    return row


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------


@app.get("/molecules")
def list_molecules(conn=Depends(db)):
    return conn.execute(
        "SELECT slug, formula, isotopologue, inchi_key FROM molecules ORDER BY formula, isotopologue"
    ).fetchall()


@app.get("/molecules/{slug}")
def get_molecule(slug: str, conn=Depends(db)):
    row = conn.execute(
        "SELECT slug, formula, isotopologue, inchi_key FROM molecules WHERE slug = %s", (slug,)
    ).fetchone()
    return one_or_404(row, "molecule")


@app.get("/marvel_versions")
def list_versions(conn=Depends(db)):
    return conn.execute("SELECT version, release_date FROM marvel_versions ORDER BY version").fetchall()


PUBLICATION_COLS = """
    p.bibtex_key, p.doi, p.year, p.title, p.authors, p.journal,
    ARRAY(SELECT DISTINCT m.slug FROM marvel_runs r JOIN molecules m ON m.id = r.molecule_id
          WHERE r.publication_id = p.id ORDER BY m.slug) AS isotopologues
"""


@app.get("/publications")
def list_publications(conn=Depends(db)):
    return conn.execute(
        f"SELECT {PUBLICATION_COLS} FROM publications p ORDER BY p.year DESC NULLS LAST, p.bibtex_key"
    ).fetchall()


@app.get("/publications/{bibtex_key}")
def get_publication(bibtex_key: str, conn=Depends(db)):
    row = conn.execute(
        f"SELECT {PUBLICATION_COLS}, p.bibtex_raw, p.notes FROM publications p WHERE p.bibtex_key = %s",
        (bibtex_key,),
    ).fetchone()
    return one_or_404(row, "publication")


@app.get("/sources")
def list_sources(conn=Depends(db)):
    return conn.execute("SELECT source_tag, doi, unit FROM source ORDER BY source_tag").fetchall()


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

# Everything the website's run dropdown needs in one request (#15): counts
# from load_report and per-role file sizes, so no request per file.
RUN_COLS = """
    r.id, m.slug AS molecule, v.version, r.dataset_hash, r.completeness,
    p.bibtex_key AS publication, r.description, r.loaded_at,
    (r.load_report ->> 'n_levels')::int AS n_levels,
    (r.load_report ->> 'n_transitions')::int AS n_transitions,
    COALESCE((SELECT jsonb_object_agg(f.file_role, f.byte_size) FROM run_files f
              WHERE f.run_id = r.id), '{}') AS files
"""
RUN_FROM = """
    FROM marvel_runs r
    JOIN molecules m ON m.id = r.molecule_id
    JOIN marvel_versions v ON v.id = r.version_id
    LEFT JOIN publications p ON p.id = r.publication_id
"""


@app.get("/molecules/{slug}/runs")
def list_runs(
    slug: str,
    version: str | None = None,
    completeness: Literal["complete", "missing_segment", "output_only"] | None = None,
    conn=Depends(db),
):
    """A molecule's runs, newest first. Pick an explicit run id from here: the
    API never merges or silently chooses between coexisting runs."""
    get_molecule(slug, conn)
    return conn.execute(
        f"""SELECT {RUN_COLS} {RUN_FROM}
            WHERE m.slug = %(slug)s
              AND (%(version)s::varchar IS NULL OR v.version = %(version)s)
              AND (%(completeness)s::varchar IS NULL OR r.completeness = %(completeness)s)
            ORDER BY r.loaded_at DESC""",
        {"slug": slug, "version": version, "completeness": completeness},
    ).fetchall()


def get_run_row(run_id: int, conn):
    row = conn.execute(
        f"SELECT {RUN_COLS}, r.qn_names, r.load_report {RUN_FROM} WHERE r.id = %s", (run_id,)
    ).fetchone()
    return one_or_404(row, "run")


@app.get("/runs/{run_id}")
def get_run(run_id: int, conn=Depends(db)):
    return get_run_row(run_id, conn)


@app.get("/runs/{run_id}/levels")
def list_levels(
    run_id: int,
    request: Request,
    qn_key: str | None = Query(None, description="Exact canonical QN string, e.g. '0 0 0 1 1 0'"),
    limit: int = Query(1000, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    conn=Depends(db),
):
    """Paginated levels, ordered by energy. Filter per quantum number with
    `qn.<name>=<value>`; names must be in the run's `qn_names`."""
    qn_names = get_run_row(run_id, conn)["qn_names"]
    qn_filter = {k[3:]: v for k, v in request.query_params.items() if k.startswith("qn.")}
    unknown = set(qn_filter) - set(qn_names)
    if unknown:
        raise HTTPException(422, f"unknown QN name(s) {sorted(unknown)}; this run has {qn_names}")
    return conn.execute(
        """SELECT id, energy, uncertainty, quantum_numbers, qn_key, symmetry,
                  n_transitions, consistency_flag, component_id
           FROM energy_levels
           WHERE run_id = %(run_id)s
             AND (%(qn_key)s::text IS NULL OR qn_key = %(qn_key)s)
             AND quantum_numbers @> %(qn)s
           ORDER BY energy, id
           LIMIT %(limit)s OFFSET %(offset)s""",
        {"run_id": run_id, "qn_key": qn_key, "qn": Jsonb(qn_filter), "limit": limit, "offset": offset},
    ).fetchall()


@app.get("/runs/{run_id}/transitions")
def list_transitions(
    run_id: int,
    source_tag: str | None = None,
    removed: bool | None = None,
    consistency_flag: bool | None = None,
    limit: int = Query(1000, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    conn=Depends(db),
):
    """Paginated input transitions. `upper`/`lower` are endpoint qn_keys; null
    when that state was never solved (floating network component)."""
    get_run_row(run_id, conn)
    return conn.execute(
        """SELECT t.id, s.source_tag, t.source_number,
                  t.upper_level_id, u.qn_key AS upper, t.lower_level_id, l.qn_key AS lower,
                  t.obs_freq, t.og_unc_freq, t.used_unc_freq, t.residual, t.consistency_flag,
                  t.uncertainty_source, t.removed, t.removed_reason, t.note
           FROM transitions t
           JOIN source s ON s.id = t.source_id
           LEFT JOIN energy_levels u ON u.id = t.upper_level_id
           LEFT JOIN energy_levels l ON l.id = t.lower_level_id
           WHERE t.run_id = %(run_id)s
             AND (%(source_tag)s::varchar IS NULL OR s.source_tag = %(source_tag)s)
             AND (%(removed)s::boolean IS NULL OR t.removed = %(removed)s)
             AND (%(cf)s::boolean IS NULL OR t.consistency_flag = %(cf)s)
           ORDER BY t.id
           LIMIT %(limit)s OFFSET %(offset)s""",
        {"run_id": run_id, "source_tag": source_tag, "removed": removed,
         "cf": consistency_flag, "limit": limit, "offset": offset},
    ).fetchall()


@app.get("/runs/{run_id}/files/{file_role}", response_class=FileResponse)
def get_file(run_id: int, file_role: Literal[FILE_ROLES], conn=Depends(db)):
    """The original published file, byte for byte, as text/plain. This is the
    bulk-export path: shown inline in a browser, save-as to download."""
    row = conn.execute(
        "SELECT rel_path FROM run_files WHERE run_id = %s AND file_role = %s", (run_id, file_role)
    ).fetchone()
    path = REPO_ROOT / one_or_404(row, "file")["rel_path"]
    if not path.is_file():
        raise HTTPException(404, "file missing from data store")
    return FileResponse(
        path, media_type="text/plain; charset=utf-8", filename=path.name, content_disposition_type="inline"
    )
