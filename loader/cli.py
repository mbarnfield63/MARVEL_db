"""loader CLI: load, validate, list, show."""

import argparse
import sys
from pathlib import Path

from loader import bib, db
from loader.manifest import load_manifest, validate_manifest
from loader.parse import parse_levels, parse_transitions


def _data_dir(manifest_path: Path, bibtex_key: str) -> Path:
    """manifests/by-publication/<key>.yaml -> data/<key>/, per manifests/README.md."""
    repo_root = manifest_path.resolve().parent.parent.parent
    return repo_root / "data" / bibtex_key


def _resolve_files(
    dataset: dict, data_dir: Path, bibtex_key: str
) -> dict[str, tuple[Path, str]]:
    return {
        role: (data_dir / rel, f"data/{bibtex_key}/{rel}")
        for role, rel in dataset["files"].items()
    }


def cmd_load(args: argparse.Namespace) -> int:
    """Parse + validate + insert every dataset in the manifest.
    Per-dataset transaction; reports success/fail/skip per dataset;
    non-zero exit if any dataset failed.
    """
    manifest = load_manifest(args.manifest)
    bibtex_key = manifest["publication"]["bibtex_key"]
    data_dir = _data_dir(args.manifest, bibtex_key)

    errors = validate_manifest(manifest, data_dir=data_dir)
    if errors:
        for error in errors:
            print(f"INVALID {error}")
        return 1

    pub_row = bib.lookup_publication(bibtex_key)

    conn = db.connect()
    publication_id = db.get_or_create_publication(conn, pub_row)
    source_ids = {
        source["tag"]: db.get_or_create_source(
            conn, source["tag"], source["unit"], source.get("doi")
        )
        for source in manifest["sources"]
    }
    conn.commit()

    results = []
    for dataset in manifest["datasets"]:
        label = dataset["isotopologue"]
        try:
            molecule_id = db.get_or_create_molecule(
                conn, dataset["formula"], dataset["isotopologue"]
            )
            version_id = db.lookup_version(conn, dataset["marvel_version"])
            files = _resolve_files(dataset, data_dir, bibtex_key)

            primary_abs, _ = files.get("input_transitions") or files["output_levels"]
            dataset_hash = db.hash_file(primary_abs)

            existing = db.run_exists(conn, molecule_id, version_id, dataset_hash)
            if existing is not None:
                conn.commit()
                results.append((label, "skip", f"dataset_hash matches run {existing}"))
                continue

            levels = []
            if "output_levels" in files:
                levels = parse_levels(
                    files["output_levels"][0],
                    dataset["level_columns"],
                    dataset["qn_names"],
                )

            transitions = []
            if "input_transitions" in files:
                transitions = parse_transitions(
                    files["input_transitions"][0],
                    dataset["qn_names"],
                    dataset["n_unc_cols"],
                )

            run_id = db.insert_dataset(
                conn,
                molecule_id=molecule_id,
                version_id=version_id,
                publication_id=publication_id,
                dataset_hash=dataset_hash,
                completeness=dataset["completeness"],
                qn_names=dataset["qn_names"],
                description=dataset.get("description"),
                levels=levels,
                transitions=transitions,
                source_ids=source_ids,
                files=files,
            )
            conn.commit()
            results.append(
                (
                    label,
                    "ok",
                    f"run {run_id}: {len(levels)} levels, {len(transitions)} transitions",
                )
            )
        except Exception as e:
            conn.rollback()
            results.append((label, "fail", str(e)))

    conn.close()
    for label, status, msg in results:
        print(f"{status.upper():5} {label}: {msg}")
    return 1 if any(status == "fail" for _, status, _ in results) else 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Same checks as load, no DB writes."""
    manifest = load_manifest(args.manifest)
    bibtex_key = manifest["publication"]["bibtex_key"]
    data_dir = _data_dir(args.manifest, bibtex_key)

    errors = validate_manifest(manifest, data_dir=data_dir)
    try:
        bib.lookup_publication(bibtex_key)
    except KeyError as e:
        errors.append(str(e))

    if errors:
        for error in errors:
            print(f"INVALID {error}")
        return 1
    print(f"OK {args.manifest}: {len(manifest['datasets'])} dataset(s)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """One line per run in the DB."""
    conn = db.connect()
    for run_id, isotopologue, version, completeness, loaded_at in db.list_runs(conn):
        print(f"{run_id}\t{isotopologue}\tv{version}\t{completeness}\t{loaded_at}")
    conn.close()
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Dump one run's load_report (molecule, version, counts, warnings)."""
    conn = db.connect()
    report = db.get_run_report(conn, args.run_id)
    conn.close()
    if report is None:
        print(f"no such run: {args.run_id}")
        return 1
    print(f"isotopologue: {report['isotopologue']}")
    print(f"version:      {report['version']}")
    print(f"completeness: {report['completeness']}")
    print(f"load_report:  {report['load_report']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="loader")
    sub = parser.add_subparsers(dest="command", required=True)

    p_load = sub.add_parser("load")
    p_load.add_argument("manifest", type=Path)
    p_load.set_defaults(func=cmd_load)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("manifest", type=Path)
    p_validate.set_defaults(func=cmd_validate)

    p_list = sub.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show")
    p_show.add_argument("run_id", type=int)
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
