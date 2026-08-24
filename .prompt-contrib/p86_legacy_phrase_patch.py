from __future__ import annotations

import json
from pathlib import Path

path = Path("registry/prompts/spec-architecture-prompts.v1.json")
payload = json.loads(path.read_text(encoding="utf-8"))
p86 = next(prompt for prompt in payload["prompts"] if prompt["id"] == "P86")
old = "concrete gap; COMPATIBLE/INCOMPATIBLE/NOT NEEDED; RAW CHANGE/SHARED-OWNER CHANGE/NO CHANGE; focused proof."
new = "concrete gap; COMPATIBLE, INCOMPATIBLE, or NOT NEEDED; RAW CHANGE, SHARED-OWNER CHANGE, or NO CHANGE; focused proof."
if old not in p86["copyContent"]:
    raise SystemExit("P86 compressed applicability phrase not found")
p86["copyContent"] = p86["copyContent"].replace(old, new, 1)
if len(p86["copyContent"]) >= 7600:
    raise SystemExit(f"P86 raw copyContent exceeded anti-bloat gate: {len(p86['copyContent'])}")
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"P86_raw_size": len(p86["copyContent"]), "legacy_disposition_semantics": "preserved"}, indent=2))
