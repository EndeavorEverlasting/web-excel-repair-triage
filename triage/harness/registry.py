"""Workflow and artifact registry loaders for the local harness."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from triage.path_policy import repo_root

_AI_DIR = repo_root() / ".ai"


def get_workflow_registry_path() -> Path:
    return _AI_DIR / "workflow-registry.json"


def get_artifact_registry_path() -> Path:
    return _AI_DIR / "artifact-registry.json"


def load_workflows() -> List[Dict[str, Any]]:
    path = get_workflow_registry_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("workflows") or []
    except json.JSONDecodeError:
        return []


def load_artifacts() -> List[Dict[str, Any]]:
    path = get_artifact_registry_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("artifacts") or []
    except json.JSONDecodeError:
        return []


def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    for wf in load_workflows():
        if wf.get("id") == workflow_id:
            return wf
    return None

