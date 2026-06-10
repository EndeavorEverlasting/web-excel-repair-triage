"""One Marcus path guards — re-export shared output policy."""
from __future__ import annotations

from triage.output_policy import (  # noqa: F401
    SourcePathWriteForbiddenError,
    assert_not_overwriting_emulator,
    assert_output_path_allowed,
    assert_out_dir_allowed,
)

__all__ = [
    "SourcePathWriteForbiddenError",
    "assert_output_path_allowed",
    "assert_not_overwriting_emulator",
    "assert_out_dir_allowed",
]
