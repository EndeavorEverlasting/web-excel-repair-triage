"""triage/harness/doctor.py
--------------------------
Health-check command: verifies that the harness infrastructure is wired correctly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from triage.harness.registry import (
    load_artifact_registry,
    load_workflow_registry,
    _ai_dir,
)
from triage.path_policy import repo_root


def run_doctor() -> Dict[str, Any]:
    """Check harness health: schemas, registries, packages, directories."""
    checks: list[Dict[str, Any]] = []
    root = repo_root()
    ai = _ai_dir()

    # 1. .ai directory exists
    checks.append({
        "name": "ai_directory_exists",
        "status": "PASS" if ai.is_dir() else "FAIL",
        "message": str(ai),
    })

    # 2. Schemas exist
    schema_names = ["run-context", "validation-report", "roster-workbook-diagnostic-report"]
    for name in schema_names:
        p = ai / "schemas" / f"{name}.json"
        checks.append({
            "name": f"schema_{name}",
            "status": "PASS" if p.exists() else "FAIL",
            "message": str(p),
        })

    # 3. Registries loadable
    try:
        ar = load_artifact_registry()
        artifact_count = len(ar.get("artifacts", {}))
        checks.append({
            "name": "artifact_registry",
            "status": "PASS",
            "message": f"{artifact_count} artifacts registered",
        })
    except Exception as e:
        checks.append({"name": "artifact_registry", "status": "FAIL", "message": str(e)})

    try:
        wr = load_workflow_registry()
        wf_count = len(wr.get("workflows", {}))
        checks.append({
            "name": "workflow_registry",
            "status": "PASS",
            "message": f"{wf_count} workflows registered",
        })
    except Exception as e:
        checks.append({"name": "workflow_registry", "status": "FAIL", "message": str(e)})

    # 4. triage.harness package importable
    try:
        import triage.harness.cli  # noqa: F401
        checks.append({"name": "harness_package_importable", "status": "PASS"})
    except Exception as e:
        checks.append({"name": "harness_package_importable", "status": "FAIL", "message": str(e)})

    # 5. Outputs directory
    outputs = root / "Outputs"
    checks.append({
        "name": "outputs_directory",
        "status": "PASS" if outputs.is_dir() else "WARN",
        "message": str(outputs),
    })

    # 6. triage package importable
    try:
        import triage  # noqa: F401
        checks.append({"name": "triage_package_importable", "status": "PASS"})
    except Exception as e:
        checks.append({"name": "triage_package_importable", "status": "FAIL", "message": str(e)})

    ok = all(c["status"] in ("PASS", "WARN") for c in checks)
    return {"status": "OK" if ok else "FAIL", "checks": checks}
