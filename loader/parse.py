"""MRT transitions parser and output-levels parser.

Transitions parser is a copy-and-adapt of
MARVEL5/src/marvel5/parse.py::parse_mrt_transitions (sibling repo, read-only
reference) — see loader/DESIGN.md "Parser reuse" for the deltas: no
solve-state fields, tag located by regex + known position (not assumed to be
the last token — files here carry a trailing note after it), the QN split
point comes from the manifest's `qn_names` rather than being inferred, and
freq is the first token (real MARVEL input files, unlike MARVEL5's, carry no
leading Iso/Name columns before it).
"""

import re
from dataclasses import dataclass
from pathlib import Path

TAG_RE = re.compile(r"^(.+?)\.?(\d+)$")


@dataclass
class ParsedTransition:
    source_tag: str
    source_number: int
    obs_freq: float
    og_unc_freq: float | None
    used_unc_freq: float | None
    upper_qn: tuple[str, ...]
    lower_qn: tuple[str, ...]
    note: str | None


@dataclass
class ParsedLevel:
    qn: tuple[str, ...]
    energy: float
    uncertainty: float
    extra: dict  # keyed by level_columns entries other than qn_names/energy/uncertainty


def _data_lines(path: Path) -> list[str]:
    """Lines after the last '----...' CDS divider, or the whole file if
    there isn't one (output-levels files don't have a header divider)."""
    lines = Path(path).read_text().splitlines()
    dividers = [i for i, l in enumerate(lines) if l.startswith("-" * 40)]
    return lines[dividers[-1] + 1 :] if dividers else lines


def _parse_unc(token: str) -> float | None:
    try:
        value = float(token)
    except ValueError:
        return None  # e.g. an unresolved "REQUIRES" placeholder
    return None if value == 0.0 else value


def parse_transitions(
    path: Path,
    qn_names: list[str],
    n_unc_cols: int,
    numeric_field_widths: list[int] | None = None,
) -> list[ParsedTransition]:
    """Parse a MARVEL transitions file: `freq <unc...> <upper QNs>
    <lower QNs> Tag [note...]`.

    nqn = len(qn_names), known from the manifest — not inferred. Hard-fails
    (raises ValueError) if the token at the position the tag is expected
    doesn't match TAG_RE, which is what an asymmetric/odd QN split looks
    like from here. TAG_RE splits at the tag's trailing run of digits (with
    an optional dot before it) rather than assuming a fixed shape — covers
    `49HeNa.1`, `06DiShWa1` (no dot), and synthetic/pseudo-transition tags
    like `PGOPHER-95LiCoxx-0-0.1`.

    `numeric_field_widths` (manifest field, optional): fixed character
    widths for the leading `freq` + uncertainty column(s) — `len ==
    1 + n_unc_cols` — sliced instead of whitespace-split before splitting
    the QN/tag remainder normally. Needed when a paper's file right-justifies
    these columns without a guaranteed separator, so a short uncertainty
    value can butt directly against the frequency with no space (seen in
    20YiOwTe: `15961.7230.0246092`, freq width 14 + unc width 12). Whichever
    columns aren't glued in a given file still parse fine sliced this way —
    slicing then stripping is equivalent to splitting when a real space
    separates the fields.
    """
    nqn = len(qn_names)
    qn_start = 1 + n_unc_cols
    tag_idx = qn_start + 2 * nqn

    out = []
    for line in _data_lines(path):
        if numeric_field_widths:
            pos = 0
            numeric_tokens = []
            for width in numeric_field_widths:
                numeric_tokens.append(line[pos : pos + width].strip())
                pos += width
            tokens = numeric_tokens + line[pos:].split()
        else:
            tokens = line.split()
        if not tokens or not tokens[0]:
            continue
        if len(tokens) <= tag_idx:
            raise ValueError(
                f"expected >= {tag_idx + 1} tokens for qn_names={qn_names}, "
                f"n_unc_cols={n_unc_cols}, got {len(tokens)}: {line!r}"
            )
        tag = tokens[tag_idx]
        tag_match = TAG_RE.match(tag)
        if not tag_match:
            raise ValueError(
                f"expected a source tag at token {tag_idx}, got {tag!r} — "
                f"QN count mismatch? line: {line!r}"
            )
        source_tag, number_s = tag_match.group(1), tag_match.group(2)

        qn_tokens = tokens[qn_start:tag_idx]
        upper_qn = tuple(qn_tokens[:nqn])
        lower_qn = tuple(qn_tokens[nqn:])

        if n_unc_cols == 2:
            og_unc = _parse_unc(tokens[1])
            used_unc = _parse_unc(tokens[2])
        else:
            unc = _parse_unc(tokens[1])
            og_unc = used_unc = unc

        note_tokens = tokens[tag_idx + 1 :]

        out.append(
            ParsedTransition(
                source_tag=source_tag,
                source_number=int(number_s),
                obs_freq=float(tokens[0]),
                og_unc_freq=og_unc,
                used_unc_freq=used_unc,
                upper_qn=upper_qn,
                lower_qn=lower_qn,
                note=" ".join(note_tokens) if note_tokens else None,
            )
        )
    return out


def parse_levels(
    path: Path, level_columns: list[str], qn_names: list[str]
) -> list[ParsedLevel]:
    """Parse an output-levels file against a fully-resolved column layout.

    Caller resolves `level_colmap` into `level_columns` first (see
    loader/DESIGN.md "Parser reuse") — this function takes no defaults.
    `qn_names` picks the QN columns out of `level_columns`; whatever's left
    besides `energy`/`uncertainty` becomes `extra`.
    """
    qn_set = set(qn_names)
    out = []
    for line in _data_lines(path):
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) != len(level_columns):
            raise ValueError(
                f"expected {len(level_columns)} tokens for level_columns="
                f"{level_columns}, got {len(tokens)}: {line!r}"
            )
        row = dict(zip(level_columns, tokens))
        extra = {}
        for key, value in row.items():
            if key in qn_set or key in ("energy", "uncertainty"):
                continue
            try:
                extra[key] = int(value)
            except ValueError:
                extra[key] = value

        out.append(
            ParsedLevel(
                qn=tuple(row[name] for name in qn_names),
                energy=float(row["energy"]),
                uncertainty=float(row["uncertainty"]),
                extra=extra,
            )
        )
    return out
