#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
PRIOR_ART = ROOT / "scripts/prompt_registry_external_prior_art.py"
PROMPT_OPS = ROOT / "scripts/prompt_registry_ops.py"
P79_TEST = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"
EXTERNAL_TEST = ROOT / "tests/test_operant_external_resources.py"

P79_COPY = r'''ADD OR STRENGTHEN PROMPT KIT PROMPTS FROM THE RELEVANT CHAT CONTEXT. THE CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION IS THE ANCHOR, NOT THE CONTEXT BOUNDARY. EXECUTE THE REPO WORK; DO NOT ASK ME TO RESTATE CONTEXT THAT IS ALREADY ACCESSIBLE.

MISSION
Turn the request into the smallest complete Prompt Kit contribution set. Strengthen canonical owners before identities. For prompt-like ADD candidates, inspect upstream prior art before authoring, synthesize useful mechanics into the user's bounded use case, use the helper for allocation/proof.

1. WHOLE-CHAT HARVEST — PASS 1
- Recover relevant decisions, examples, corrections, constraints, definitions.
- Build `insight | current owner | action | proof`: STRENGTHEN / ADD / ALREADY COVERED / OUT OF SCOPE.
- No material insight may silently disappear. Do not ask the user to repeat recoverable context.

2. OWNER MAP + UPSTREAM PRIOR-ART BEFORE AUTHORING
Search the combined Prompt Kit for an exact, adjacent, or materially overlapping prompt. Compare trigger, mission, scope, closure—not title alone.
If ADD remains plausible, before drafting run:
`python scripts/prompt_registry_ops.py prior-art --query "<user use case + candidate mechanics>"`
- Require `all_registered_sources_searched=true`; search every current registered upstream exactly once.
- Current examples: `deepseek-harness`, `prompts-chat`, `mattpocock-skills`; not exhaustive. New registered prompt kits/skill sources inherit the gate.
- Build `upstream insight | source | current owner | overlap/residual | adoption`.
- `python scripts/search_operant_external_catalog.py --source prompts-chat --query "..."` may deepen one catalog search, but one source never satisfies the all-source gate.
- `REVIEW_ADD_PROMPT` is evidence, not authoring permission.
- STRENGTHEN when an owner has the core use case but lacks compatible failure/proof/iteration/usability/upstream mechanics.
- ADD only for genuinely missing bounded behavior with distinct trigger/closure and a distinct residual before ADD.
- ALREADY COVERED requires concrete prompt evidence. Do not duplicate an identity because wording differs.

3. COMPLEMENT — DO NOT MERELY TRANSCRIBE / UPSTREAM SYNTHESIS INTO THE USER USE CASE
Preserve user intent, terminology, constraints, closure. From relevant upstream hits extract reusable mechanics—not donor identity/wholesale wording—and classify ADOPT / ADAPT / REFERENCE_ONLY / REJECT.
Construct sound overlapping value only where a discovered mechanic improves the user's given use case; combine it with the current owner's role plus failures, entrypoints, proof, context recovery, iteration, discoverability, or integration seams. Preserve Operant authority/license boundaries. Do not bulk-import donor prompts, auto-author from donors, or manufacture value when no relevant hit exists.

4. IMPLEMENT THE CONTRIBUTION SET
For STRENGTHEN, edit canonical source + closest focused regression.
For ADD, after pre-authoring receipt/synthesis:
- choose closest registry/profile; run `python scripts/prompt_registry_ops.py inspect` only if routing is unclear;
- draft semantic fields only; Do NOT set id, seq, or copySheet;
- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;
- ADD must re-run every registered upstream against the final draft before identity allocation, return `external_prior_art`, allocate identity, reject duplicates, inject shared policy, rebuild, prove parity, and roll back registry/site writes if validation fails;
- compare receipts; if stronger owner appears, residual collapses, or use case no longer matches evidence, abort ADD and STRENGTHEN/rework.
Multiple genuinely distinct prompts may be added from one chat; do not collapse them merely to keep one identity.

5. WHOLE-CHAT HARVEST — PASS 2
Traverse relevant context again from the opposite direction for missed corrections/examples, sources, definitions, upstream insights, neighboring owners. Update ledger; close gaps. Stop at a bounded fixed point.

6. FOCUSED PROOF + CONVERGENCE
Add/extend the closest focused semantic assertion the generic helper cannot prove. For ADD, prove both prior-art receipts cover the registered source set and final prompt explains adopted/adapted mechanics in the user's use case without copying donor authority.
Run `python scripts/prompt_registry_ops.py validate`, focused tests, applicable language/order/discovery checks, generated-site `--check`, and `git diff --check`. Refresh the default-branch floor; then merge the exact green authorized head into main.

FAIL-CLOSED
If upstream coverage is incomplete, pinned floor invalid, or residual not distinct, do not ADD. Do not fall back to loading the entire Prompt Kit architecture, guess identities, bypass parity, weaken a validator, make the operator a context courier/test runner, or substitute one donor search for the all-source gate.

DELIVER
Ledger; upstream synthesis; IDs; receipts; tests; parity; validation; integration; main SHA; blocker.'''

P79_FIELDS = {
    "sprintRole": "Harvest the relevant conversation, map canonical owners, research every registered upstream before authoring any new prompt identity, synthesize compatible prior-art mechanics into the user's bounded use case, and use the repo helper only for genuinely missing identities",
    "useWhen": "The current chat contains reusable prompt/workflow insights and the operator wants them represented in the Prompt Kit without restating context, duplicating owners, or ignoring registered upstream prompt/skill prior art.",
    "inspectFirst": "Relevant accessible conversation; refreshed Triage main/PR floor; combined Prompt Kit ownership; registered external-resource contract/index and pinned source floors; pre-authoring all-source prior-art receipt; focused semantic tests; helper routing only when needed.",
    "expectedOutput": "A whole-chat contribution ledger plus upstream-source coverage/synthesis dispositions, strengthened canonical owners, only genuinely missing helper-added prompts whose final ADD receipt rechecks every registered upstream, focused proof, exact site parity, and mainline convergence.",
    "nextStep": "Harvest context, map owners, run the all-source `prior-art` helper before drafting any ADD candidate, adapt useful upstream mechanics to the user's use case, implement STRENGTHEN/ADD actions, then repeat the context/upstream coverage pass before final validation.",
    "proofGate": "The request is an anchor rather than a context boundary; every material insight is dispositioned; any ADD has a pre-authoring receipt with all_registered_sources_searched=true plus an upstream synthesis ledger, then a final helper receipt that rechecks the current registered source set before identity allocation; donor authority is not copied; focused semantic and exact-site-parity proof pass.",
    "copyContent": P79_COPY,
    "keywords": [
        "prompt registry adder", "add prompt", "prompt kit contribution", "whole chat harvest",
        "strengthen prompt", "prompt overlap", "upstream prompt prior art", "external prompt prior art",
        "deepseek harness", "matt pocock skills", "prompt synthesis", "all registered sources"
    ],
}

PRIOR_ART_INSERT = '''\n\ndef review_external_prior_art(query_text: str) -> dict[str, Any]:\n    \"\"\"Search every registered upstream before semantic prompt authoring begins.\"\"\"\n    query = str(query_text).strip()\n    if not query:\n        raise PriorArtGateError(\"pre-authoring external prior-art query is empty\")\n    return require_external_prior_art({\"name\": query, \"keywords\": []})\n'''
PRIOR_ART_ANCHOR = "\ndef require_external_prior_art(draft: dict[str, Any]) -> dict[str, Any]:\n"

OPS_INSERT = '''\n\ndef review_prior_art(query_text: str) -> dict[str, Any]:\n    \"\"\"Expose the all-registered-source gate before a semantic ADD draft exists.\"\"\"\n    try:\n        return prior_art.review_external_prior_art(query_text)\n    except prior_art.PriorArtGateError as exc:\n        raise SystemExit(\n            f\"Prompt pre-authoring external prior-art review failed closed: {exc}\"\n        ) from exc\n'''
OPS_ANCHOR = "\ndef add_prompt(\n    draft: dict[str, Any], explicit_registry: str | None, dry_run: bool\n) -> dict[str, Any]:\n"

ARGPARSE_OLD = '''    sub.add_parser("inspect", help="Print next identity and compact registry routing choices as JSON.")\n    add = sub.add_parser(\n        "add",\n        help="Search registered external prior art, then add one prompt draft, allocate identity, rebuild, and validate.",\n    )\n'''
ARGPARSE_NEW = '''    sub.add_parser("inspect", help="Print next identity and compact registry routing choices as JSON.")\n    prior = sub.add_parser(\n        "prior-art",\n        help="Search every registered upstream before authoring a semantic ADD draft.",\n    )\n    prior.add_argument(\n        "--query",\n        required=True,\n        help="User use case plus candidate mechanics to compare with internal owners and registered upstreams.",\n    )\n    add = sub.add_parser(\n        "add",\n        help="Recheck every registered upstream, then add one prompt draft, allocate identity, rebuild, and validate.",\n    )\n'''
DISPATCH_OLD = '''    if args.command == "inspect":\n        result = inspect_state()\n    elif args.command == "add":\n        result = add_prompt(_read_json(args.input), args.registry, args.dry_run)\n    else:\n        result = validate_current()\n'''
DISPATCH_NEW = '''    if args.command == "inspect":\n        result = inspect_state()\n    elif args.command == "prior-art":\n        result = review_prior_art(args.query)\n    elif args.command == "add":\n        result = add_prompt(_read_json(args.input), args.registry, args.dry_run)\n    else:\n        result = validate_current()\n'''

P79_TEST_NEEDLE = '            "distinct residual before ADD",\n'
P79_TEST_INSERT = '''            "UPSTREAM PRIOR-ART BEFORE AUTHORING",\n            "prompt_registry_ops.py prior-art --query",\n            "all_registered_sources_searched=true",\n            "deepseek-harness",\n            "mattpocock-skills",\n            "UPSTREAM SYNTHESIS INTO THE USER USE CASE",\n            "upstream insight | source | current owner | overlap/residual | adoption",\n            "Construct sound overlapping value",\n            "Do not bulk-import donor prompts",\n            "re-run every registered upstream against the final draft",\n'''

EXTERNAL_TEST_METHOD = r'''\n    def test_prompt_adder_exposes_predraft_all_registered_source_review(self) -> None:\n        query = "prompt registry upstream synthesis zeta"\n        configured = {item["id"] for item in self.contract["sources"]}\n        receipt = {\n            "schema_version": add_prior_art.RECEIPT_SCHEMA,\n            "query": query,\n            "sources": [{"source_id": source_id} for source_id in sorted(configured)],\n            "all_registered_sources_searched": True,\n            "distinct_residual_terms": ["synthesis"],\n            "automatic_prompt_authoring": False,\n        }\n        with mock.patch.object(\n            add_prior_art, "review_external_prior_art", return_value=receipt\n        ) as review:\n            result = prompt_ops.review_prior_art(query)\n        review.assert_called_once_with(query)\n        self.assertTrue(result["all_registered_sources_searched"])\n        self.assertEqual({row["source_id"] for row in result["sources"]}, configured)\n\n        with mock.patch.object(prompt_ops, "review_prior_art", return_value=receipt) as cli_review, \\\n             mock.patch("builtins.print"):\n            self.assertEqual(prompt_ops.main(["prior-art", "--query", query]), 0)\n        cli_review.assert_called_once_with(query)\n\n'''
EXTERNAL_TEST_ANCHOR = "    def test_prompt_adder_binds_external_gate_before_identity_allocation(self) -> None:\n"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"{label} anchor missing: {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def apply() -> None:
    payload = load_json(REGISTRY)
    p79 = next((item for item in payload["prompts"] if item.get("id") == "P79"), None)
    if p79 is None:
        raise SystemExit("P79 missing from spec-architecture registry")
    p79.update(P79_FIELDS)
    write_json(REGISTRY, payload)

    text = PRIOR_ART.read_text(encoding="utf-8")
    if "def review_external_prior_art(" not in text:
        if PRIOR_ART_ANCHOR not in text:
            raise SystemExit("prior-art function anchor missing")
        PRIOR_ART.write_text(text.replace(PRIOR_ART_ANCHOR, PRIOR_ART_INSERT + PRIOR_ART_ANCHOR, 1), encoding="utf-8")

    text = PROMPT_OPS.read_text(encoding="utf-8")
    if "def review_prior_art(" not in text:
        if OPS_ANCHOR not in text:
            raise SystemExit("prompt-ops review function anchor missing")
        text = text.replace(OPS_ANCHOR, OPS_INSERT + OPS_ANCHOR, 1)
    if '"prior-art"' not in text:
        if ARGPARSE_OLD not in text:
            raise SystemExit("prompt-ops argparse anchor missing")
        text = text.replace(ARGPARSE_OLD, ARGPARSE_NEW, 1)
    if 'elif args.command == "prior-art":' not in text:
        if DISPATCH_OLD not in text:
            raise SystemExit("prompt-ops dispatch anchor missing")
        text = text.replace(DISPATCH_OLD, DISPATCH_NEW, 1)
    PROMPT_OPS.write_text(text, encoding="utf-8")

    text = P79_TEST.read_text(encoding="utf-8")
    if '"UPSTREAM PRIOR-ART BEFORE AUTHORING"' not in text:
        if P79_TEST_NEEDLE not in text:
            raise SystemExit("P79 semantic-test anchor missing")
        text = text.replace(P79_TEST_NEEDLE, P79_TEST_NEEDLE + P79_TEST_INSERT, 1)
    P79_TEST.write_text(text, encoding="utf-8")

    text = EXTERNAL_TEST.read_text(encoding="utf-8")
    if "test_prompt_adder_exposes_predraft_all_registered_source_review" not in text:
        if EXTERNAL_TEST_ANCHOR not in text:
            raise SystemExit("external-resource test anchor missing")
        text = text.replace(EXTERNAL_TEST_ANCHOR, EXTERNAL_TEST_METHOD + EXTERNAL_TEST_ANCHOR, 1)
    EXTERNAL_TEST.write_text(text, encoding="utf-8")
    verify()


def verify() -> None:
    payload = load_json(REGISTRY)
    p79 = next((item for item in payload["prompts"] if item.get("id") == "P79"), None)
    if p79 is None:
        raise SystemExit("P79 missing during verification")
    for key, expected in P79_FIELDS.items():
        if p79.get(key) != expected:
            raise SystemExit(f"P79 mismatch: {key}")
    if len(p79["copyContent"]) >= 5000:
        raise SystemExit(f"P79 raw copyContent too large: {len(p79['copyContent'])}")
    prior_text = PRIOR_ART.read_text(encoding="utf-8")
    ops_text = PROMPT_OPS.read_text(encoding="utf-8")
    tests = P79_TEST.read_text(encoding="utf-8") + EXTERNAL_TEST.read_text(encoding="utf-8")
    required = [
        "def review_external_prior_art(", "def review_prior_art(", '"prior-art"',
        'elif args.command == "prior-art":', "UPSTREAM PRIOR-ART BEFORE AUTHORING",
        "all_registered_sources_searched=true", "Construct sound overlapping value",
        "test_prompt_adder_exposes_predraft_all_registered_source_review",
    ]
    haystack = prior_text + ops_text + tests + p79["copyContent"]
    missing = [item for item in required if item not in haystack]
    if missing:
        raise SystemExit(f"P79 upstream synthesis verification missing: {missing}")
    print("P79_UPSTREAM_SYNTHESIS_VERIFY_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
    else:
        apply()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
