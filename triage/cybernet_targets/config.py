"""Load Cybernet target sprint JSON contracts from configs/."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_DIR = _REPO_ROOT / "configs"


def _load(name: str) -> Dict[str, Any]:
    path = _CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def targets_schema() -> Dict[str, Any]:
    return _load("cybernet_targets_schema.json")


def load_scope(path: str | Path | None = None) -> Dict[str, Any]:
    if path is None:
        return _load("cybernet_sprint_scope_2026_06.json")
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def normalize_site(site: str, aliases: Dict[str, str]) -> str:
    s = (site or "").strip()
    return aliases.get(s, aliases.get(s.upper(), s))
