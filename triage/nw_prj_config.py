"""
Load NW PRJ dashboard v6 JSON contracts from configs/.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _REPO_ROOT / "configs"


def _load(name: str) -> Dict[str, Any]:
    path = _CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def dashboard_schema() -> Dict[str, Any]:
    return _load("nw_prj_dashboard_v6_schema.json")


@lru_cache(maxsize=1)
def cf_palette() -> Dict[str, Any]:
    return _load("cf_palette_v1.json")


@lru_cache(maxsize=1)
def status_values() -> Dict[str, Any]:
    return _load("status_values_v1.json")


@lru_cache(maxsize=1)
def team_scope_values() -> Dict[str, Any]:
    return _load("team_scope_values_v1.json")


@lru_cache(maxsize=1)
def stop_ship_tokens() -> Dict[str, Any]:
    return _load("web_excel_stop_ship_tokens.json")


def resolved_review_statuses() -> frozenset[str]:
    return frozenset(status_values()["review_status"]["resolved_green"])


def skipped_review_statuses() -> frozenset[str]:
    return frozenset(status_values()["review_status"]["skipped_gray"])


def is_repair_filename(name: str) -> bool:
    low = name.lower()
    for marker in stop_ship_tokens()["filename_markers"]:
        if marker.lower() in low:
            return True
    return False
