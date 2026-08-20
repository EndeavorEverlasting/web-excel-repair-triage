#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
path = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
payload = json.loads(path.read_text(encoding="utf-8"))
prompt = next(item for item in payload["prompts"] if item.get("id") == "P83")
marker = "CONTINUOUS AGENTIC LOOP INVARIANT"
base = prompt["copyContent"].split("\n\n" + marker, 1)[0].rstrip()
compact = """CONTINUOUS AGENTIC LOOP INVARIANT
- Each pass must correct/advance state, produce new evidence, integrate a verified bounded green slice, or prove an exact blocker; status alone is not progress.
- If inherited work is green/current/authorized, merge it now; after integrating verified inherited work, refresh main/evidence and continue from the next unproven gate. Commit/push/PR/green CI/merge-ready are intermediate states.
- Preserve atomic correctness and separately owned work.
"""
prompt["copyContent"] = base + "\n\n" + compact
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
subprocess.run(["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"], cwd=ROOT, check=True)
