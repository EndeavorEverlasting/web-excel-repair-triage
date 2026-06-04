"""Output path guards — operator source folders are read-only inputs."""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_READONLY_ROOTS = ("Candidates", "Active")


class SourcePathWriteForbiddenError(ValueError):
    """Raised when engine output would overwrite or write into read-only input zones."""


def assert_output_path_allowed(input_path: str, output_path: str) -> None:
    """Fail closed if output equals input or targets Candidates/ or Active/."""
    inp = Path(input_path).resolve()
    out = Path(output_path).resolve()

    if inp == out:
        raise SourcePathWriteForbiddenError(
            "output path must not equal input path; write delivery artifacts under Outputs/"
        )

    try:
        rel = out.relative_to(_REPO_ROOT.resolve())
    except ValueError:
        return

    if rel.parts and rel.parts[0] in _READONLY_ROOTS:
        raise SourcePathWriteForbiddenError(
            f"output path must not be under {rel.parts[0]}/; "
            "Candidates/ and Active/ are read-only operator inputs"
        )
