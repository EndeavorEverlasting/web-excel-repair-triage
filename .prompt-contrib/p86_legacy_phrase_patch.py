from __future__ import annotations

import json
from pathlib import Path

path = Path("registry/prompts/spec-architecture-prompts.v1.json")
payload = json.loads(path.read_text(encoding="utf-8"))
p86 = next(prompt for prompt in payload["prompts"] if prompt["id"] == "P86")

replacements = (
    (
        "concrete gap; COMPATIBLE/INCOMPATIBLE/NOT NEEDED; RAW CHANGE/SHARED-OWNER CHANGE/NO CHANGE; focused proof.",
        "concrete gap; COMPATIBLE, INCOMPATIBLE, or NOT NEEDED; RAW CHANGE, SHARED-OWNER CHANGE, or NO CHANGE; focused proof.",
    ),
    (
        "Adopt only what strengthens that job; do not transform P03 into those owners.",
        "Adopt only what strengthens that job; do not transform P03 into P07, P13, P48, P76, P83, P84, or P85.",
    ),
)
for old, new in replacements:
    if old not in p86["copyContent"]:
        raise SystemExit(f"P86 compressed legacy phrase not found: {old}")
    p86["copyContent"] = p86["copyContent"].replace(old, new, 1)

if len(p86["copyContent"]) >= 7600:
    raise SystemExit(f"P86 raw copyContent exceeded anti-bloat gate: {len(p86['copyContent'])}")
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"P86_raw_size": len(p86["copyContent"]), "legacy_semantics": ["disposition vocabulary", "P03 role boundary"]}, indent=2))
