#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
import tmp_prompt_artifact_risk_path_executor as base

ROOT = Path(__file__).resolve().parents[1]

# Reuse the corrected raw-P50 function without importing v2's executable footer.
v2_path = ROOT / "scripts" / "tmp_prompt_artifact_risk_path_executor_v2.py"
tree = ast.parse(v2_path.read_text(encoding="utf-8"))
patch_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "patch_p50")
namespace = {"json": json, "Path": Path, "ROOT": ROOT}
exec(compile(ast.Module(body=[patch_node], type_ignores=[]), str(v2_path), "exec"), namespace)
base.patch_p50 = namespace["patch_p50"]

original_run = base.run


def run_with_color(*args: str) -> None:
    if "scripts/prompt_registry_ops.py" in args and "add" in args and "--input" in args:
        draft_path = Path(args[args.index("--input") + 1])
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        draft["color"] = "Cyan"
        draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    original_run(*args)


base.run = run_with_color
raise SystemExit(base.main())
