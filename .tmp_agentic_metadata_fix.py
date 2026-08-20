#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

registry_path = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
payload = json.loads(registry_path.read_text(encoding="utf-8"))
p83 = next(item for item in payload["prompts"] if item.get("id") == "P83")
p83["nextStep"] = (
    "Resolve the exact prior work and current repository floor, build a claim-to-evidence matrix, "
    "execute the highest-value unproven or incorrect in-scope item, validate it, critique the new evidence, "
    "integrate any independently verified green slice, refresh main/evidence, and repeat until the bounded "
    "fixed point or a genuine user-only gate is reached."
)
registry_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

docs_path = ROOT / "docs" / "prompts.json"
docs = json.loads(docs_path.read_text(encoding="utf-8"))
p07 = next(item for item in docs if item.get("id") == "P07")
p07["nextStep"] = (
    "Run the next bounded IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE pass on the "
    "highest-value executable gate; when a coherent bounded green slice is independently valid, integrate it, "
    "refresh main/evidence, and continue until the fixed-point gate or an exact external blocker is reached."
)
docs_path.write_text(json.dumps(docs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

subprocess.run(
    ["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"],
    cwd=ROOT,
    check=True,
)
