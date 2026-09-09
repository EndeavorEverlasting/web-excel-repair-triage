#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TEST = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"


def load_base_p79() -> dict:
    raw = subprocess.check_output(
        ["git", "show", "origin/main:registry/prompts/spec-architecture-prompts.v1.json"],
        cwd=ROOT,
        text=True,
    )
    payload = json.loads(raw)
    return next(item for item in payload["prompts"] if item["id"] == "P79")


def apply() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    index = next(i for i, item in enumerate(payload["prompts"]) if item["id"] == "P79")
    p79 = dict(load_base_p79())

    p79["sprintRole"] = (
        p79["sprintRole"]
        + ", researching every registered upstream before authoring a new identity and synthesizing compatible prior-art mechanics into the user's bounded use case"
    )
    p79["useWhen"] = p79["useWhen"].rstrip(".") + ", while requiring registered upstream prior art to shape any plausible ADD candidate."
    p79["inspectFirst"] = p79["inspectFirst"].rstrip(".") + "; for plausible ADDs, also the registered external-resource contract/index, pinned source floors, and a pre-authoring all-source prior-art receipt."
    p79["expectedOutput"] = p79["expectedOutput"].rstrip(".") + ", with upstream-source coverage/synthesis dispositions and a final ADD receipt that rechecks every registered upstream."
    p79["nextStep"] = (
        "Sweep the whole relevant chat and map owners; if ADD remains plausible, run the all-source `prior-art` helper before semantic drafting, adapt useful upstream mechanics to the user's use case, then implement strengthen/add actions and sweep the chat again before validation and mainline convergence."
    )
    p79["proofGate"] = p79["proofGate"].rstrip(".") + "; any ADD also has a pre-authoring receipt with `all_registered_sources_searched=true`, an upstream synthesis ledger, and a final helper receipt that rechecks the current registered source set before identity allocation without copying donor authority."

    content = p79["copyContent"]
    old_owner = (
        "2. OWNER MAP BEFORE NEW IDS\n"
        "Search the combined Prompt Kit for an exact, adjacent, or materially overlapping prompt. Compare trigger, mission, scope, and closure—not title alone.\n"
        "For prompt-like use cases, also search registered external sources/catalogs (for example `python scripts/search_operant_external_catalog.py --source prompts-chat --query \"...\"`), extract commonality with current owners, and prove a distinct residual before ADD. `REVIEW_ADD_PROMPT` is a candidate for that comparison, not authoring permission."
    )
    new_owner = (
        "2. OWNER MAP + UPSTREAM PRIOR-ART BEFORE AUTHORING\n"
        "Search the combined Prompt Kit for an exact, adjacent, or materially overlapping prompt. Compare trigger, mission, scope, and closure—not title alone.\n"
        "For prompt-like ADD candidates, before drafting run `python scripts/prompt_registry_ops.py prior-art --query \"<user use case + candidate mechanics>\"`; require `all_registered_sources_searched=true` so every registered upstream is searched exactly once (current examples: `deepseek-harness`, `prompts-chat`, `mattpocock-skills`; future registered sources inherit the gate). Build `upstream insight | source | current owner | overlap/residual | adoption`. `python scripts/search_operant_external_catalog.py --source prompts-chat --query \"...\"` may deepen one source but never replaces the all-source gate. `REVIEW_ADD_PROMPT` is evidence, not authoring permission. Extract commonality and prove a distinct residual before ADD."
    )
    if old_owner not in content:
        raise SystemExit("base P79 owner-map anchor missing")
    content = content.replace(old_owner, new_owner, 1)

    old_comp = "3. COMPLEMENT — DO NOT MERELY TRANSCRIBE\nPreserve explicit user intent and terminology, then expand compatible utility revealed by chat/repo evidence: useful failure states, entrypoints, proof levels, context recovery, user-only gates, iteration, discoverability, or integration seams. Expansion must make the requested workflow more executable, reusable, testable, or failure-resistant. Do not invent unrelated requirements or universal checklists."
    new_comp = old_comp.replace(
        "3. COMPLEMENT — DO NOT MERELY TRANSCRIBE",
        "3. COMPLEMENT — DO NOT MERELY TRANSCRIBE / UPSTREAM SYNTHESIS INTO THE USER USE CASE",
    ) + "\nFor relevant upstream hits, classify ADOPT / ADAPT / REFERENCE_ONLY / REJECT and Construct sound overlapping value only when the mechanic improves the user's given use case. Adapt mechanics, not donor authority or wholesale wording; Do not bulk-import donor prompts or auto-author from donors."
    if old_comp not in content:
        raise SystemExit("base P79 complement anchor missing")
    content = content.replace(old_comp, new_comp, 1)

    old_add = (
        "For ADD:\n"
        "- choose the closest existing registry/profile; run `python scripts/prompt_registry_ops.py inspect` only if routing is unclear;\n"
        "- draft semantic fields only; Do NOT set id, seq, or copySheet;\n"
        "- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;\n"
        "- let the helper allocate identity, reject obvious duplicates, inject shared policy, rebuild the site, prove parity, and roll back registry/site writes if validation fails."
    )
    new_add = (
        "For ADD:\n"
        "- use the pre-authoring receipt above to shape the semantic draft; choose the closest existing registry/profile; run `python scripts/prompt_registry_ops.py inspect` only if routing is unclear;\n"
        "- draft semantic fields only; Do NOT set id, seq, or copySheet;\n"
        "- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;\n"
        "- let ADD re-run every registered upstream against the final draft before identity allocation and return `external_prior_art`, then allocate identity, reject obvious duplicates, inject shared policy, rebuild the site, prove parity, and roll back registry/site writes if validation fails."
    )
    if old_add not in content:
        raise SystemExit("base P79 ADD anchor missing")
    content = content.replace(old_add, new_add, 1)

    p79["copyContent"] = content
    for keyword in (
        "upstream prompt prior art",
        "deepseek harness",
        "matt pocock skills",
        "prompt synthesis",
        "all registered sources",
    ):
        if keyword not in p79["keywords"]:
            p79["keywords"].append(keyword)

    if len(content) >= 5000:
        raise SystemExit(f"additive P79 copyContent too large: {len(content)}")

    payload["prompts"][index] = p79
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    anchor = '            "re-run every registered upstream against the final draft",\n'
    additions = (
        '            "CANONICAL REPO",\n'
        '            "Recover approved/rejected wording",\n'
        '            "Look for missed `also`, `another`, `we skipped`",\n'
        '            "roll back registry/site writes if validation fails",\n'
        '            "Verify new prompts remain distinct and strengthened prompts retain their original role",\n'
    )
    if additions not in test:
        if anchor not in test:
            raise SystemExit("P79 regression insertion anchor missing")
        test = test.replace(anchor, anchor + additions, 1)
        TEST.write_text(test, encoding="utf-8")

    print(f"P79_ADDITIVE_UPSTREAM_REPAIR_PASS chars={len(content)}")


if __name__ == "__main__":
    apply()
