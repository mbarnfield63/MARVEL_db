"""psycopg connection + per-dataset insert.

One transaction per dataset (loader/DESIGN.md "Failure semantics") — a bad
dataset in a multi-isotopologue manifest doesn't block the others. Callers
manage the boundary with plain conn.commit()/conn.rollback() around each
dataset's work (psycopg3 connections start a new implicit transaction after
each commit/rollback).
"""

import hashlib
import os
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

# The only level_colmap/level_columns "extra" keys the schema has columns
# for. Anything else is a manifest error, not something to invent a slot
# for (loader/DESIGN.md's no-inference stance).
KNOWN_LEVEL_EXTRA_COLUMNS = {"n_transitions", "symmetry", "component_id"}


def connect() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"])


def lookup_version(conn: psycopg.Connection, version: str) -> int:
    row = conn.execute(
        "SELECT id FROM marvel_versions WHERE version = %s", (version,)
    ).fetchone()
    if row is None:
        raise KeyError(
            f"unknown marvel_version {version!r} — seed it in schema.sql first"
        )
    return row[0]


def get_or_create_molecule(
    conn: psycopg.Connection,
    formula: str,
    isotopologue: str,
    inchi_key: str | None = None,
) -> int:
    slug = isotopologue.lower().replace("-", "").replace("+", "p")
    row = conn.execute(
        """
        INSERT INTO molecules (formula, isotopologue, inchi_key, slug)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (isotopologue) DO UPDATE SET formula = EXCLUDED.formula
        RETURNING id
        """,
        (formula, isotopologue, inchi_key, slug),
    ).fetchone()
    return row[0]


def get_or_create_publication(conn: psycopg.Connection, pub: dict) -> int:
    row = conn.execute(
        """
        INSERT INTO publications (bibtex_key, doi, year, title, authors, journal, bibtex_raw)
        VALUES (%(bibtex_key)s, %(doi)s, %(year)s, %(title)s, %(authors)s, %(journal)s, %(bibtex_raw)s)
        ON CONFLICT (bibtex_key) DO UPDATE SET bibtex_key = EXCLUDED.bibtex_key
        RETURNING id
        """,
        pub,
    ).fetchone()
    return row[0]


def get_or_create_source(
    conn: psycopg.Connection, tag: str, unit: str, doi: str | None
) -> int:
    row = conn.execute(
        """
        INSERT INTO source (source_tag, doi, unit)
        VALUES (%s, %s, %s)
        ON CONFLICT (source_tag) DO UPDATE SET unit = EXCLUDED.unit
        RETURNING id
        """,
        (tag, doi, unit),
    ).fetchone()
    return row[0]


def run_exists(
    conn: psycopg.Connection, molecule_id: int, version_id: int, dataset_hash: str
) -> int | None:
    """Return the existing marvel_runs.id for this (molecule, version,
    dataset_hash), or None. Same hash already loaded -> caller no-ops.
    """
    row = conn.execute(
        """
        SELECT id FROM marvel_runs
        WHERE molecule_id = %s AND version_id = %s AND dataset_hash = %s
        """,
        (molecule_id, version_id, dataset_hash),
    ).fetchone()
    return row[0] if row else None


def hash_file(path: Path) -> str:
    """Normalised sha256: strip trailing whitespace per line, LF endings —
    so re-saving a file with different line endings doesn't mint a new
    run."""
    text = path.read_text()
    normalised = "\n".join(line.rstrip() for line in text.splitlines())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def insert_dataset(
    conn: psycopg.Connection,
    *,
    molecule_id: int,
    version_id: int,
    publication_id: int | None,
    dataset_hash: str,
    completeness: str,
    qn_names: list[str],
    description: str | None,
    levels: list,  # list[parse.ParsedLevel]
    transitions: list,  # list[parse.ParsedTransition]
    source_ids: dict[str, int],  # source_tag -> source.id
    files: dict[str, tuple[Path, str]],  # file_role -> (abs_path, repo_rel_path)
) -> int:
    """Insert one dataset's run + run_files + energy_levels + transitions.
    Caller commits or rolls back around this call — one transaction per
    dataset, per loader/DESIGN.md."""
    run_row = conn.execute(
        """
        INSERT INTO marvel_runs
            (molecule_id, version_id, publication_id, dataset_hash, completeness, qn_names, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            molecule_id,
            version_id,
            publication_id,
            dataset_hash,
            completeness,
            qn_names,
            description,
        ),
    ).fetchone()
    run_id = run_row[0]

    for role, (abs_path, rel_path) in files.items():
        conn.execute(
            """
            INSERT INTO run_files (run_id, file_role, rel_path, sha256, byte_size)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, role, rel_path, hash_file(abs_path), abs_path.stat().st_size),
        )

    level_id_by_qn_key: dict[str, int] = {}
    for level in levels:
        qn_key = " ".join(level.qn)
        for key in level.extra:
            if key not in KNOWN_LEVEL_EXTRA_COLUMNS:
                raise ValueError(
                    f"unrecognised level column {key!r} — not one of {KNOWN_LEVEL_EXTRA_COLUMNS}"
                )

        row = conn.execute(
            """
            INSERT INTO energy_levels
                (run_id, energy, uncertainty, quantum_numbers, qn_key, symmetry, n_transitions, component_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                run_id,
                level.energy,
                level.uncertainty,
                Jsonb(dict(zip(qn_names, level.qn))),
                qn_key,
                level.extra.get("symmetry"),
                level.extra.get("n_transitions"),
                level.extra.get("component_id"),
            ),
        ).fetchone()
        level_id_by_qn_key[qn_key] = row[0]

    for transition in transitions:
        upper_key = " ".join(transition.upper_qn)
        lower_key = " ".join(transition.lower_qn)
        try:
            upper_id = level_id_by_qn_key[upper_key]
            lower_id = level_id_by_qn_key[lower_key]
        except KeyError as e:
            raise ValueError(
                f"transition endpoint {e} has no matching energy level"
            ) from e

        source_id = source_ids[transition.source_tag]
        conn.execute(
            """
            INSERT INTO transitions
                (run_id, source_id, source_number, upper_level_id, lower_level_id,
                 obs_freq, og_unc_freq, used_unc_freq, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                source_id,
                transition.source_number,
                upper_id,
                lower_id,
                transition.obs_freq,
                transition.og_unc_freq,
                transition.used_unc_freq,
                transition.note,
            ),
        )

    load_report = {"n_levels": len(levels), "n_transitions": len(transitions)}
    conn.execute(
        "UPDATE marvel_runs SET load_report = %s WHERE id = %s",
        (Jsonb(load_report), run_id),
    )
    return run_id


def list_runs(conn: psycopg.Connection) -> list[tuple]:
    return conn.execute("""
        SELECT r.id, m.isotopologue, v.version, r.completeness, r.loaded_at
        FROM marvel_runs r
        JOIN molecules m ON m.id = r.molecule_id
        JOIN marvel_versions v ON v.id = r.version_id
        ORDER BY r.id
        """).fetchall()


def get_run_report(conn: psycopg.Connection, run_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT m.isotopologue, v.version, r.completeness, r.load_report
        FROM marvel_runs r
        JOIN molecules m ON m.id = r.molecule_id
        JOIN marvel_versions v ON v.id = r.version_id
        WHERE r.id = %s
        """,
        (run_id,),
    ).fetchone()
    if row is None:
        return None
    isotopologue, version, completeness, load_report = row
    return {
        "isotopologue": isotopologue,
        "version": version,
        "completeness": completeness,
        "load_report": load_report,
    }
