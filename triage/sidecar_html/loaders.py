"""Load sidecar files for HTML embedding."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(path: Optional[str | Path]) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: Optional[str | Path], max_rows: int = 2000) -> List[Dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, Any]] = []
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(dict(row))
        return rows


def safe_embed_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
