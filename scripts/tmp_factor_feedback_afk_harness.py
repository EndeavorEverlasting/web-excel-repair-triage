#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    p = ROOT / path
    return p, json.loads(p.read_text(encoding="utf-8"))


def dump(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_unique(items: list[dict], row: dict, *, key: str = "id") -> None:
    matches = [item for item in items if item.get(key) == row[key]]
    if matches:
        if matches != [row]:
            raise SystemExit(f"existing {key}={row[key]} differs from requested canonical row")
        return
    items.append(row)


cap_path, caps = load("harness/capabilities.v1.json")
append_unique(
    caps["capabilities"],
    {
        "id": "prompt-kit-feedback-afk-routing",
        "version": "1.0.0",
        "status": "canonical",
        "skill": ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md",
        "trigger_ids": ["prompt-kit-actionable-feedback"],
        "operation": "Classify and deduplicate one accepted Prompt Kit feedback signal, create a P115-owned bounded work request, and invoke at most one configured capable worker without polling or promotion authority.",
        "inputs": [
            "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
            "accepted explicit feedback signal or sanitized provider receipt",
            "current Prompt Kit feedback owner evidence",
            "configured worker argv when available"
        ],
        "outputs": [
            "ACTIONABLE_REPAIR or INFORMATION_ONLY disposition",
            "deduplicated prompt-kit-afk-work-request/v1 artifact for actionable feedback",
            "bounded worker result or exact worker-configuration blocker"
        ],
        "implementation": {"kind": "script", "path": "scripts/prompt_kit_afk_signal_router.py"},
        "proof_ceiling": "One-shot repository routing and local work-request proof only; browser loopback behavior, worker quality, provider review, and promotion remain separate."
    },
)
dump(cap_path, caps)

trigger_path, triggers = load("harness/triggers.v1.json")
append_unique(
    triggers["triggers"],
    {
        "id": "prompt-kit-actionable-feedback",
        "capability_id": "prompt-kit-feedback-afk-routing",
        "skill": ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md",
        "workflow": "WORKFLOW.md#i-prompt-kit-feedback-afk-routing",
        "conditions": [
            "accepted Prompt Kit written feedback requires follow-through",
            "accepted Prompt Kit dislike vote requires follow-through",
            "a sanitized prompt-kit-feedback provider wakeup maps to an unconsumed local actionable signal"
        ],
        "forbidden_conditions": [
            "signal is only a like or usage observation",
            "signal is malformed, sensitive, unknown, or already consumed",
            "the next action is only PR promotion or merge; route that gate to P105/pr-floor-integration",
            "routing would require a second polling scheduler"
        ]
    },
)
dump(trigger_path, triggers)

workflow_path, workflows = load("harness/workflows.v1.json")
append_unique(
    workflows["workflows"],
    {
        "id": "prompt-kit-feedback-afk-routing",
        "document": "WORKFLOW.md#i-prompt-kit-feedback-afk-routing",
        "trigger": "Accepted explicit Prompt Kit feedback has an unconsumed actionable signal that should create bounded AFK development work.",
        "focused_contract": "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
        "owned_scope": [
            "single-signal classification and deduplication",
            "private machine-readable P115 work request",
            "bounded invocation of one configured capable worker",
            "private feedback bridge routing boundaries",
            "read-only provider wakeup evidence"
        ],
        "forbidden_scope": [
            "direct PR merge",
            "second scheduler or infinite polling loop",
            "browser or tracked credentials",
            "raw written feedback in provider dispatch payloads",
            "replacement of P99, P115, P07, P32, or P105 ownership"
        ],
        "entry_points": [
            "scripts/prompt_kit_afk_signal_router.py",
            "scripts/validate_prompt_kit_feedback_afk_routing.py",
            "harness/contracts/prompt-kit-feedback-afk-routing.v1.json"
        ],
        "validation_profile": "harness",
        "failure_policy": "Fail closed on malformed/sensitive/duplicate signals, create an exact BLOCKED_WORKER_UNCONFIGURED work request when no capable worker adapter exists, and route validated candidates to P105/pr-floor rather than merging here.",
        "handoff_fields": [
            "signal identity and disposition",
            "P115 work-request path",
            "worker result or exact blocker",
            "focused validator/tests",
            "browser/provider proof ceiling",
            "promotion owner"
        ]
    },
)
dump(workflow_path, workflows)

validator_path, validators = load("harness/validators.v1.json")
new_validators = [
    {
        "id": "prompt-kit-feedback-afk-routing-audit",
        "class": "contract",
        "command": "python scripts/validate_prompt_kit_feedback_afk_routing.py --summary",
        "blocking": True,
        "output": "process log",
        "proof_ceiling": "Static feedback-AFK ownership, privacy, scheduler, workflow, and promotion-boundary proof."
    },
    {
        "id": "prompt-kit-feedback-afk-routing-tests",
        "class": "test",
        "command": "python -m unittest tests.test_prompt_kit_feedback_afk_routing -v",
        "blocking": True,
        "output": "process log",
        "proof_ceiling": "Executable one-shot classification, dedupe, work-request, and routing-boundary regression proof."
    },
]
for row in new_validators:
    append_unique(validators["validators"], row)
for profile_name in ("harness", "pre_push"):
    profile = validators["profiles"][profile_name]
    anchor = "skill-prompt-registry-tests"
    insert_at = profile.index(anchor) + 1 if anchor in profile else len(profile)
    for validator_id in reversed([row["id"] for row in new_validators]):
        if validator_id not in profile:
            profile.insert(insert_at, validator_id)
dump(validator_path, validators)

manifest_path, manifest = load("harness/manifest.v1.json")
manifest["domain_contracts"]["prompt_kit_feedback_afk_routing"] = {
    "contract": "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
    "validator": "scripts/validate_prompt_kit_feedback_afk_routing.py",
    "contract_tests": "tests/test_prompt_kit_feedback_afk_routing.py",
    "workflow": "WORKFLOW.md#i-prompt-kit-feedback-afk-routing",
    "harness_gate": "python scripts/validate_prompt_kit_feedback_afk_routing.py --summary",
    "skill": ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md",
    "router": "scripts/prompt_kit_afk_signal_router.py",
    "feedback_runtime": "docs/prompt-kit-feedback-production.js",
    "provider_hook": ".github/workflows/prompt-kit-feedback-hook.yml",
    "promotion_contract": "harness/contracts/pr-merge-gate.v1.json"
}
skill_path = ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md"
if skill_path not in manifest["skills"]:
    manifest["skills"].append(skill_path)
commands = [row["command"] for row in new_validators]
anchor_command = "python -m unittest tests.test_skill_prompt_registry -v"
insert_at = manifest["validation_order"].index(anchor_command) + 1 if anchor_command in manifest["validation_order"] else len(manifest["validation_order"])
for command in reversed(commands):
    if command not in manifest["validation_order"]:
        manifest["validation_order"].insert(insert_at, command)
dump(manifest_path, manifest)

skills_path = ROOT / "SKILLS.md"
skills = skills_path.read_text(encoding="utf-8")
row = "| Prompt Kit feedback AFK routing | turn accepted explicit feedback into one bounded P115 work request without merge authority | `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md` |\n"
anchor = "| Prompt Kit responsive layout | Prompt Kit overlap/responsive layout work | `.ai/skills/prompt-kit-responsive-layout/SKILL.md` |\n"
if row not in skills:
    if anchor not in skills:
        raise SystemExit("SKILLS.md table anchor missing")
    skills = skills.replace(anchor, anchor + row, 1)
routing = "- Prompt Kit actionable explicit feedback → Prompt Kit feedback AFK routing;\n"
anchor2 = "- prompt wording/audit → Prompt language audit.\n"
if routing not in skills:
    if anchor2 not in skills:
        raise SystemExit("SKILLS.md routing anchor missing")
    skills = skills.replace(anchor2, routing + anchor2, 1)
skills_path.write_text(skills, encoding="utf-8")

caps_md_path = ROOT / "CAPABILITIES.md"
caps_md = caps_md_path.read_text(encoding="utf-8")
cap_row = "| `prompt-kit-feedback-afk-routing` | `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md` | `scripts/prompt_kit_afk_signal_router.py` | One deduplicated P115 work request or information-only disposition; promotion remains P105/pr-floor. |\n"
cap_anchor = "| `prompt-kit-browser-proof-scratch-cleanup` | `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md` | `scripts/Clear-PromptKitBrowserProofScratch.ps1` | Preview/apply cleanup receipt for exact eligible detached browser-proof scratch. |\n"
if cap_row not in caps_md:
    if cap_anchor not in caps_md:
        raise SystemExit("CAPABILITIES.md table anchor missing")
    caps_md = caps_md.replace(cap_anchor, cap_anchor + cap_row, 1)
section = """\n## Prompt Kit feedback AFK routing capability\n\n`prompt-kit-feedback-afk-routing` consumes one accepted explicit feedback signal at a time. P99 owns explicit feedback semantics, P115 owns AFK coordination, P07/P32 own bounded repair lanes, and P105 / `pr-floor-integration` owns promotion. The router may classify, deduplicate, write a private work request, and invoke one configured worker through argv; it must not poll indefinitely, scan provider PR queues, or merge. Raw written feedback remains local and provider wakeups are receipt-only.\n"""
proof_anchor = "\n## Proof boundaries\n"
if "## Prompt Kit feedback AFK routing capability" not in caps_md:
    if proof_anchor not in caps_md:
        raise SystemExit("CAPABILITIES.md proof anchor missing")
    caps_md = caps_md.replace(proof_anchor, section + proof_anchor, 1)
caps_md_path.write_text(caps_md, encoding="utf-8")

triggers_md_path = ROOT / "TRIGGERS.md"
triggers_md = triggers_md_path.read_text(encoding="utf-8")
trigger_row = "| `prompt-kit-actionable-feedback` | Accepted written feedback or a dislike has an unconsumed actionable Prompt Kit signal. | `prompt-kit-feedback-afk-routing` | The signal is like/usage-only, malformed/sensitive/already consumed, requires a second scheduler, or the only remaining gate is P105 promotion. |\n"
trigger_anchor = "| `prompt-kit-browser-proof-temp-path` | An operator supplies a `prompt-kit-browser-proof-*` path under OS Temp or asks to classify/remove detached Prompt Kit browser-proof scratch. | `prompt-kit-browser-proof-scratch-cleanup` | The real request is browser-site data/Favorites deletion, broad Temp cleanup, canonical-repo cleanup, or durable evidence deletion. |\n"
if trigger_row not in triggers_md:
    if trigger_anchor not in triggers_md:
        raise SystemExit("TRIGGERS.md table anchor missing")
    triggers_md = triggers_md.replace(trigger_anchor, trigger_anchor + trigger_row, 1)
rule = """\n## Prompt Kit feedback AFK routing rule\n\nExplicit written feedback and dislikes may create one bounded P115 work request after validation and deduplication. Likes and usage are informational by default. The private bridge may sanitize and transport; it does not schedule or merge. A validated candidate leaves this capability and enters P105 / `pr-floor-integration`. No local infinite poller is authorized.\n"""
routing_anchor = "\n## Routing procedure\n"
if "## Prompt Kit feedback AFK routing rule" not in triggers_md:
    if routing_anchor not in triggers_md:
        raise SystemExit("TRIGGERS.md routing anchor missing")
    triggers_md = triggers_md.replace(routing_anchor, rule + routing_anchor, 1)
triggers_md_path.write_text(triggers_md, encoding="utf-8")

workflow_md_path = ROOT / "WORKFLOW.md"
workflow_md = workflow_md_path.read_text(encoding="utf-8")
workflow_section = """### I. Prompt Kit feedback AFK routing\n\n**Workflow ID:** `prompt-kit-feedback-afk-routing`  \n**Trigger:** `prompt-kit-actionable-feedback`  \n**Capability:** `prompt-kit-feedback-afk-routing`  \n**Skill:** `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md`  \n**Focused contract:** `harness/contracts/prompt-kit-feedback-afk-routing.v1.json`\n\n1. Accept one explicit feedback signal from the current feedback seam; reject malformed or sensitive payloads.\n2. Classify written feedback and dislikes as `ACTIONABLE_REPAIR`; keep likes and usage `INFORMATION_ONLY` unless independent repository evidence creates work.\n3. Deduplicate the stable signal identity before work dispatch.\n4. Create a private P115-owned machine work request that names the smallest capable mutation owner, acceptance condition, forbidden scope, and validation entry point.\n5. Invoke at most one configured worker through argv. No background polling loop or second scheduler belongs here.\n6. Keep the bridge as transport/sanitization only. Raw comments remain local; provider wakeups carry only allow-listed receipt metadata.\n7. When a coherent candidate is ready, leave this workflow and route promotion to P105 / `pr-floor-integration`; never merge from the feedback router.\n8. Run the focused validator/tests and preserve browser-loopback/provider behavior as separate runtime proof.\n\n"""
workflow_anchor = "## 3. Validate before committing\n"
if "### I. Prompt Kit feedback AFK routing" not in workflow_md:
    if workflow_anchor not in workflow_md:
        raise SystemExit("WORKFLOW.md validation anchor missing")
    workflow_md = workflow_md.replace(workflow_anchor, workflow_section + workflow_anchor, 1)
workflow_md_path.write_text(workflow_md, encoding="utf-8")

web_workflow = """name: Prompt Kit web contracts\n\non:\n  pull_request:\n    paths:\n      - 'registry/prompts/**'\n      - 'docs/prompt-kit-*.js'\n      - 'harness/contracts/prompt-kit-*.json'\n      - 'harness/capabilities.v1.json'\n      - 'harness/triggers.v1.json'\n      - 'harness/workflows.v1.json'\n      - 'harness/validators.v1.json'\n      - 'harness/manifest.v1.json'\n      - 'scripts/build_prompt_kit_registry.py'\n      - 'scripts/serve_prompt_kit_portable.py'\n      - 'scripts/validate_prompt_kit_portability.py'\n      - 'scripts/prompt_kit_*.py'\n      - 'scripts/validate_prompt_kit_feedback_afk_routing.py'\n      - 'tests/test_prompt_kit_*.py'\n      - 'web/prompt-kit/index.html'\n      - '.github/workflows/prompt-kit-web.yml'\n  push:\n    branches: [main]\n    paths:\n      - 'registry/prompts/**'\n      - 'docs/prompt-kit-*.js'\n      - 'harness/contracts/prompt-kit-*.json'\n      - 'scripts/build_prompt_kit_registry.py'\n      - 'scripts/serve_prompt_kit_portable.py'\n      - 'scripts/validate_prompt_kit_portability.py'\n      - 'scripts/prompt_kit_*.py'\n      - 'tests/test_prompt_kit_*.py'\n      - 'web/prompt-kit/index.html'\n      - '.github/workflows/prompt-kit-web.yml'\n\npermissions:\n  contents: read\n\nconcurrency:\n  group: prompt-kit-web-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true\n\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout exact candidate\n        uses: actions/checkout@v7\n      - name: Set up Python\n        uses: actions/setup-python@v7\n        with:\n          python-version: '3.11'\n      - name: Validate private feedback AFK factoring\n        run: |\n          python scripts/validate_prompt_kit_feedback_afk_routing.py --summary\n          python -m unittest tests.test_prompt_kit_feedback_afk_routing tests.test_prompt_kit_feedback_production -v\n      - name: Validate canonical Prompt Kit parity\n        run: python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check\n      - name: Build portable Prompt Kit runtime artifact\n        run: python scripts/serve_prompt_kit_portable.py --build-only\n      - name: Validate portable Favorites and harness discipline\n        run: |\n          python scripts/validate_prompt_kit_portability.py --require-artifact --output Outputs/prompt-kit-portability-validation.json --summary\n          python -m unittest tests.test_prompt_kit_portability.py tests.test_prompt_kit_portability_regressions.py tests.test_prompt_kit_portable_health -v\n      - name: Validate patch hygiene\n        run: git diff --check\n      - name: Publish portable runtime proof\n        uses: actions/upload-artifact@v4\n        with:\n          name: prompt-kit-portable-runtime\n          path: Outputs/prompt-kit-portable/\n          if-no-files-found: error\n          retention-days: 14\n"""
(ROOT / ".github" / "workflows" / "prompt-kit-web.yml").write_text(web_workflow, encoding="utf-8")

print(json.dumps({
    "status": "patched",
    "capabilities": len(caps["capabilities"]),
    "triggers": len(triggers["triggers"]),
    "workflows": len(workflows["workflows"]),
    "validators": len(validators["validators"]),
    "validation_order": len(manifest["validation_order"]),
}))
