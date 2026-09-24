#!/usr/bin/env python3
"""Render the standalone campaign pack from canonical semantic prompt sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render() -> tuple[Path, str]:
    contract = json.loads((ROOT / "harness/ad-campaign/campaign.v1.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / contract["registry_path"]).read_text(encoding="utf-8"))
    prompts = {p["name"]: p for p in registry["prompts"] if p.get("profile") == contract["profile"]}
    if set(prompts) != set(contract["prompt_names"]):
        raise ValueError("Campaign prompt names do not match the canonical domain contract")
    parts = ["# Ad campaign prompt pack\n",
             "Generated from the canonical campaign registry. Run the first incomplete stage: doctrine, harness, planning, creative production, launch review, then results analysis. Copy the relevant prompt and supply your existing campaign context. No repository is required to use these prompts.\n",
             "[Domain guide](README.md) · [Campaign doctrine](../../harness/ad-campaign/DOCTRINE.md)\n"]
    for name in contract["prompt_names"]:
        prompt = prompts[name]
        parts.extend([f"## {prompt['id']} — {name}\n", prompt["useWhen"] + "\n",
                      "```text\n" + prompt["copyContent"].strip() + "\n```\n"])
    return ROOT / contract["prompt_pack"], "\n".join(parts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    output, expected = render()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            print("Campaign pack is stale; run python scripts/build_ad_campaign_pack.py")
            return 1
        print("Campaign pack parity PASS (6 canonical prompts)")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
