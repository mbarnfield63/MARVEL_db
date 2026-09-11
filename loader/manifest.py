"""Load and validate a per-publication manifest YAML.

See manifests/README.md for the format. Deliberately no JSON Schema (#5) —
missing/bad fields are the loader's job to catch.
"""

from pathlib import Path

import yaml

REQUIRED_DATASET_FIELDS = [
    "formula",
    "isotopologue",
    "marvel_version",
    "completeness",
    "n_unc_cols",
    "qn_names",
]

# Files required per completeness state — manifests/README.md's table.
COMPLETENESS_FILES = {
    "complete": ["input_transitions", "output_levels", "segment"],
    "missing_segment": ["input_transitions", "output_levels"],
    "output_only": ["output_levels"],
}


def load_manifest(path: Path) -> dict:
    """Read the YAML, merge `defaults:` into each dataset, resolve
    `level_colmap` into a full `level_columns` list where needed.

    Returns the manifest dict with each item in `datasets` fully resolved
    (no more defaults lookup needed downstream).
    """
    raw = yaml.safe_load(Path(path).read_text())
    defaults = raw.get("defaults", {})

    datasets = []
    for ds in raw.get("datasets", []):
        merged = {**defaults, **ds}
        merged["files"] = {**defaults.get("files", {}), **ds.get("files", {})}

        if "level_columns" not in merged:
            merged["level_columns"] = (
                list(merged.get("qn_names", []))
                + ["energy", "uncertainty"]
                + list(merged.get("level_colmap", []))
            )
        datasets.append(merged)

    return {
        "publication": raw.get("publication", {}),
        "sources": raw.get("sources", []),
        "datasets": datasets,
    }


def validate_manifest(manifest: dict, data_dir: Path | None = None) -> list[str]:
    """Check required fields are present after defaults merge (see the
    Fields table in manifests/README.md) and, if `data_dir` is given (the
    publication's data directory, `data/<bibtex_key>/`), that referenced
    files exist there.

    Returns a list of error strings; empty list means valid.
    """
    errors = []
    publication = manifest.get("publication", {})
    if not publication.get("bibtex_key"):
        errors.append("publication.bibtex_key is required")

    for source in manifest.get("sources", []):
        if not source.get("tag"):
            errors.append(f"source entry missing tag: {source}")
        if not source.get("unit"):
            errors.append(f"source {source.get('tag')!r} missing unit")

    for i, dataset in enumerate(manifest.get("datasets", [])):
        label = dataset.get("isotopologue", f"datasets[{i}]")

        for field in REQUIRED_DATASET_FIELDS:
            if dataset.get(field) in (None, ""):
                errors.append(f"{label}: missing required field {field!r}")

        completeness = dataset.get("completeness")
        if completeness not in COMPLETENESS_FILES:
            errors.append(f"{label}: invalid completeness {completeness!r}")
            continue

        files = dataset.get("files", {})
        for role in COMPLETENESS_FILES[completeness]:
            rel_path = files.get(role)
            if not rel_path:
                errors.append(
                    f"{label}: completeness={completeness!r} requires files.{role}"
                )
            elif data_dir is not None:
                full_path = data_dir / rel_path
                if not full_path.is_file():
                    errors.append(f"{label}: files.{role} not found at {full_path}")

    return errors
