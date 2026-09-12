"""triage/harness/output_policy.py
----------------------------------
Output-run allocation and source immutability enforcement.

Ensures:
- Outputs only land under Outputs/ (specifically Outputs/runs/<run_id>/).
- No writes into Candidates/, Active/, References/, ArtifactIntake/.
- No --output equals --input.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from triage.path_policy import repo_root

# Directories that are read-only operator inputs.
SOURCE_DIRS = ("Candidates", "Active", "References", "ArtifactIntake")

# Top-level directories where output is allowed.
OUTPUT_DIRS = ("Outputs",)


def is_source_path(path: str | Path) -> bool:
    """True if *path* falls under any read-only source directory."""
    root = repo_root()
    p = Path(path)
    if not p.is_absolute():
        p = (root / p).resolve(strict=False)
    for d in SOURCE_DIRS:
        source_root = (root / d).resolve(strict=False)
        try:
            if p.is_relative_to(source_root):
                return True
        except AttributeError:
            if str(p).lower().startswith(str(source_root).lower()):
                return True
    return False


def is_output_path(path: str | Path) -> bool:
    """True if *path* falls under Outputs/."""
    root = repo_root()
    p = Path(path)
    if not p.is_absolute():
        p = (root / p).resolve(strict=False)
    out_root = (root / "Outputs").resolve(strict=False)
    try:
        return p.is_relative_to(out_root)
    except AttributeError:
        return str(p).lower().startswith(str(out_root).lower())


def validate_output_allocation(
    output_dir: str | Path,
    input_paths: List[str] | None = None,
) -> List[str]:
    """Return a list of policy violations. Empty means OK."""
    root = repo_root()
    out = Path(output_dir)
    if not out.is_absolute():
        out = (root / out).resolve(strict=False)

    violations: List[str] = []

    # Output must be under Outputs/
    if not is_output_path(out):
        violations.append(
            f"output_dir '{out}' is not under Outputs/ — "
            "all generated artifacts must go under Outputs/"
        )

    # Output must not overlap a source directory
    if is_source_path(out):
        violations.append(
            f"output_dir '{out}' overlaps a read-only source directory"
        )

    # Output must not equal any input
    if input_paths:
        for inp in input_paths:
            inp_full = Path(inp)
            if not inp_full.is_absolute():
                inp_full = (root / inp).resolve(strict=False)
            if out.resolve(strict=False) == inp_full.resolve(strict=False):
                violations.append(
                    f"output_dir equals input path '{inp}' — "
                    "output must not be the same as input"
                )

    return violations


def refuse_source_writes(paths: List[str | Path]) -> List[str]:
    """Return violations for any paths that attempt to write into source dirs."""
    violations: List[str] = []
    for p in paths:
        if is_source_path(p):
            violations.append(
                f"refusing to write into source directory: {p}"
            )
    return violations
