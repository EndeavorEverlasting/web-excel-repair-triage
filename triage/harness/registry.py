"""triage/harness/registry.py
---------------------------
Load and query the artifact-registry.json and workflow-registry.json files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _ai_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".ai"


def load_artifact_registry() -> Dict[str, Any]:
    p = _ai_dir() / "artifact-registry.json"
    if not p.exists():
        raise FileNotFoundError(f"artifact-registry.json not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_workflow_registry() -> Dict[str, Any]:
    p = _ai_dir() / "workflow-registry.json"
    if not p.exists():
        raise FileNotFoundError(f"workflow-registry.json not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_schema(name: str) -> Dict[str, Any]:
    p = _ai_dir() / "schemas" / f"{name}.json"
    if not p.exists():
        raise FileNotFoundError(f"Schema {name!r} not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    reg = load_workflow_registry()
    return reg.get("workflows", {}).get(workflow_id)


def get_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    reg = load_artifact_registry()
    return reg.get("artifacts", {}).get(artifact_id)


def list_workflows() -> Dict[str, Dict[str, Any]]:
    reg = load_workflow_registry()
    return dict(reg.get("workflows", {}))


def list_artifacts() -> Dict[str, Dict[str, Any]]:
    reg = load_artifact_registry()
    return dict(reg.get("artifacts", {}))
