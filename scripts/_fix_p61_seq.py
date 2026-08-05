#!/usr/bin/env python3
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
path = root / "docs" / "prompts.json"
items = json.loads(path.read_text(encoding="utf-8"))
matches = [p for p in items if p.get("id") == "P61"]
if len(matches) != 1:
    raise SystemExit(f"Expected exactly one P61, found {len(matches)}")
matches[0]["seq"] = "61"
path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
subprocess.run(["python", "build_prompt_kit.py", "--output", "web/prompt-kit/index.html"], cwd=root, check=True)
assert json.loads(path.read_text(encoding="utf-8"))[-1]["seq"] == "61"
print("P61 sequence corrected and web prompt kit regenerated")
