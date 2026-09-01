#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(path: str, payload):
    (ROOT / path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_unique(rows, row, key="id"):
    if not any(item.get(key) == row[key] for item in rows):
        rows.append(row)


# Builder: embed only the lazy runtime, never the resource catalog.
path = ROOT / "scripts/build_prompt_kit_registry.py"
text = path.read_text(encoding="utf-8")
anchor = 'ONTOLOGY_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-ontology.js"\n'
addition = anchor + 'EXTERNAL_RESOURCES_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-external-resources.js"\n'
if "EXTERNAL_RESOURCES_RUNTIME" not in text:
    if anchor not in text:
        raise SystemExit("builder runtime constant anchor missing")
    text = text.replace(anchor, addition, 1)
anchor = '    ontology_script = _read_runtime(\n        ONTOLOGY_RUNTIME, "Prompt Kit ontology lens behavior"\n    )\n'
addition = anchor + '    external_resources_script = _read_runtime(\n        EXTERNAL_RESOURCES_RUNTIME, "Operant external resource browsing behavior"\n    )\n'
if "external_resources_script =" not in text:
    if anchor not in text:
        raise SystemExit("builder runtime read anchor missing")
    text = text.replace(anchor, addition, 1)
anchor = '        f"<script>\\n{ontology_script}\\n</script>\\n"\n'
addition = anchor + '        f"<script>\\n{external_resources_script}\\n</script>\\n"\n'
if "{external_resources_script}" not in text:
    if anchor not in text:
        raise SystemExit("builder supplemental anchor missing")
    text = text.replace(anchor, addition, 1)
path.write_text(text, encoding="utf-8")

# Capability + trigger.
capabilities = load("harness/capabilities.v1.json")
append_unique(capabilities["capabilities"], {
    "id": "operant-external-resource-intake",
    "version": "1.0.0",
    "status": "canonical",
    "skill": ".ai/skills/operant-external-resource-intake/SKILL.md",
    "trigger_ids": ["operant-external-resource-refresh-needed"],
    "operation": "Refresh approved public donor skill inventories, project compact commit-pinned metadata, classify existing Operant coverage first, and emit external pointers plus grounded prompt-review gaps without copying donor bodies into the Prompt Kit.",
    "inputs": [
        "harness/contracts/operant-external-resource-intake.v1.json",
        "live public GitHub donor metadata",
        "current Operant prompt registry",
        "current local skill inventory"
    ],
    "outputs": [
        "web/prompt-kit/resources.v1.json",
        "registry/resources/operant-external-resource-gaps.v1.json",
        "POINT_TO_EXISTING_PROMPT / POINT_TO_EXISTING_SKILL / POINT_TO_EXTERNAL disposition",
        "REVIEW_ADD_PROMPT queue routed to P79 when internal coverage is absent"
    ],
    "implementation": {"kind": "script", "path": "scripts/sync_operant_external_resources.py"},
    "proof_ceiling": "Live public donor source-SHA resolution plus repository metadata projection, deterministic coverage routing, size-budget, lazy-load, CI drift, and generated-site proof; no donor quality, license-adaptation, browser-network, or automatic prompt-quality proof."
})
save("harness/capabilities.v1.json", capabilities)

triggers = load("harness/triggers.v1.json")
append_unique(triggers["triggers"], {
    "id": "operant-external-resource-refresh-needed",
    "capability_id": "operant-external-resource-intake",
    "skill": ".ai/skills/operant-external-resource-intake/SKILL.md",
    "workflow": "WORKFLOW.md#c-harness-infrastructure-change",
    "conditions": [
        "approved donor repository resource inventory may have changed",
        "scheduled Operant external-resource drift proof fails",
        "user asks whether an existing open-source skill/resource already covers a task",
        "prompt-gap maintenance needs current donor evidence"
    ],
    "forbidden_conditions": [
        "donor content would be copied into PROMPTS merely for search",
        "scheduled automation would write directly to the default branch",
        "private or credentialed donor access is required",
        "prompt addition would occur without P79 strategic strengthen-before-add review"
    ]
})
save("harness/triggers.v1.json", triggers)

# Manifest registration.
manifest = load("harness/manifest.v1.json")
manifest["domain_contracts"].setdefault("operant_external_resource_intake", {
    "contract": "harness/contracts/operant-external-resource-intake.v1.json",
    "validator": "scripts/validate_operant_external_resources.py",
    "contract_tests": "tests/test_operant_external_resources.py",
    "workflow": "WORKFLOW.md#c-harness-infrastructure-change",
    "harness_gate": "python scripts/validate_operant_external_resources.py --summary",
    "skill": ".ai/skills/operant-external-resource-intake/SKILL.md",
    "sync": "scripts/sync_operant_external_resources.py",
    "public_index": "web/prompt-kit/resources.v1.json",
    "gap_ledger": "registry/resources/operant-external-resource-gaps.v1.json",
    "provider_refresh": ".github/workflows/operant-external-resource-refresh.yml"
})
skill = ".ai/skills/operant-external-resource-intake/SKILL.md"
if skill not in manifest["skills"]:
    manifest["skills"].append(skill)
for command in (
    "python scripts/validate_operant_external_resources.py --summary",
    "python -m unittest tests.test_operant_external_resources -v",
):
    if command not in manifest["validation_order"]:
        insert_at = manifest["validation_order"].index("python tests/test_prompt_kit_header_contract.py")
        manifest["validation_order"].insert(insert_at, command)
save("harness/manifest.v1.json", manifest)

# Validator registry + profiles.
validators = load("harness/validators.v1.json")
append_unique(validators["validators"], {
    "id": "operant-external-resource-audit",
    "class": "contract",
    "command": "python scripts/validate_operant_external_resources.py --summary",
    "blocking": True,
    "output": "process log",
    "proof_ceiling": "Static/current tracked resource projection, source pin, coverage routing, size-budget, lazy-load, and generated-site containment proof."
})
append_unique(validators["validators"], {
    "id": "operant-external-resource-tests",
    "class": "test",
    "command": "python -m unittest tests.test_operant_external_resources -v",
    "blocking": True,
    "output": "process log",
    "proof_ceiling": "Executable deterministic resource projection and lazy-loading regression proof."
})
for profile_name in ("harness", "pre_push"):
    profile = validators["profiles"][profile_name]
    insert_at = profile.index("prompt-kit-header-contract")
    for validator_id in ("operant-external-resource-audit", "operant-external-resource-tests"):
        if validator_id not in profile:
            profile.insert(insert_at, validator_id)
            insert_at += 1
save("harness/validators.v1.json", validators)

# Artifact registry.
artifacts = load("harness/artifacts.v1.json")
append_unique(artifacts["artifacts"], {
    "id": "operant-external-resource-index",
    "kind": "tracked",
    "canonical_path": "web/prompt-kit/resources.v1.json",
    "producer": "python scripts/sync_operant_external_resources.py",
    "validator": "operant-external-resource-audit",
    "naming": "Stable metadata-only sidecar next to the generated Prompt Kit website.",
    "tracking_policy": "Tracked deterministic projection of approved public donors pinned to exact commits; donor bodies are not copied.",
    "proof_ceiling": "Donor inventory metadata, pinning, and projection proof; no donor content quality or browser-network proof."
})
append_unique(artifacts["artifacts"], {
    "id": "operant-external-resource-gap-ledger",
    "kind": "tracked",
    "canonical_path": "registry/resources/operant-external-resource-gaps.v1.json",
    "producer": "python scripts/sync_operant_external_resources.py",
    "validator": "operant-external-resource-audit",
    "naming": "Stable deterministic donor-to-Operant coverage ledger.",
    "tracking_policy": "Tracked maintenance input. REVIEW_ADD_PROMPT routes to P79; it is not prompt publication authority.",
    "proof_ceiling": "Deterministic lexical coverage classification and maintenance routing only; strategic prompt quality remains separate."
})
save("harness/artifacts.v1.json", artifacts)

# Human indexes: add compact pointers, not duplicated procedure.
skills_path = ROOT / "SKILLS.md"
skills = skills_path.read_text(encoding="utf-8")
row = "| Operant external resource intake | discover/refresh approved open-source skills and route existing coverage before prompt gaps | `.ai/skills/operant-external-resource-intake/SKILL.md` |\n"
if row not in skills:
    marker = "| Prompt Kit feedback AFK routing | turn accepted explicit feedback into one bounded P115 work request without merge authority | `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md` |\n"
    if marker not in skills:
        raise SystemExit("SKILLS index marker missing")
    skills = skills.replace(marker, marker + row, 1)
route = "- Operant/open-source donor resource discovery or drift → Operant external resource intake;\n"
if route not in skills:
    marker = "- Prompt Kit actionable explicit feedback → Prompt Kit feedback AFK routing;\n"
    if marker not in skills:
        raise SystemExit("SKILLS routing marker missing")
    skills = skills.replace(marker, marker + route, 1)
skills_path.write_text(skills, encoding="utf-8")

for filename, block in (
    ("CAPABILITIES.md", "\n## Operant external resource intake\n\n`operant-external-resource-intake` uses `scripts/sync_operant_external_resources.py` to inventory approved public donor skill roots at exact commits, publish the metadata-only `web/prompt-kit/resources.v1.json` sidecar, and route deterministic coverage gaps through P79 rather than copying donor bodies or auto-authoring prompts.\n"),
    ("TRIGGERS.md", "\n## Operant external resource refresh\n\n`operant-external-resource-refresh-needed` routes scheduled donor drift, open-source resource lookup, and donor-backed prompt-gap maintenance to `.ai/skills/operant-external-resource-intake/SKILL.md`. Existing Operant coverage wins; external-only resources remain directly usable; prompt publication stays behind P79 strategic review.\n"),
):
    doc = ROOT / filename
    content = doc.read_text(encoding="utf-8")
    if block.strip() not in content:
        content = content.rstrip() + "\n" + block
    doc.write_text(content, encoding="utf-8")

readme = ROOT / "web/README.md"
content = readme.read_text(encoding="utf-8")
block = "\n### External resources\n\nThe **Resources** control uses `docs/prompt-kit-external-resources.js` and lazily fetches the compact `prompt-kit/resources.v1.json` sidecar only after the user opens it. Donor skill bodies are never embedded in the main generated page; results are paged and existing Operant prompt coverage is preferred before upstream links.\n"
if block.strip() not in content:
    content = content.rstrip() + "\n" + block
readme.write_text(content, encoding="utf-8")

print("OPERANT_EXTERNAL_RESOURCE_REGISTRATION_APPLIED=1")
