#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
AI = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
LEDGER = ROOT / "registry/prompts/repository-work-ledger-prompts.v1.json"
SPEC_TEST = ROOT / "tests/test_spec_architecture_prompt_registry.py"
AI_TEST = ROOT / "tests/test_ai_engineering_level_up.py"
LEDGER_TEST = ROOT / "tests/test_repository_work_ledger_prompt.py"
SITE = ROOT / "web/prompt-kit/index.html"
HELPER = ROOT / "scripts/prompt_registry_ops.py"


def run(*args: str, capture: bool = False) -> str:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=capture)
    if capture:
        print(result.stdout, end="", flush=True)
        return result.stdout
    return ""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prompt(payload: dict, prompt_id: str) -> dict:
    matches = [p for p in payload["prompts"] if p.get("id") == prompt_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {prompt_id}, got {len(matches)}")
    return matches[0]


def append_once(value: str, addition: str) -> str:
    return value if addition in value else value + addition


def add_keyword(item: dict, value: str) -> None:
    if value not in item["keywords"]:
        item["keywords"].append(value)


def insert_before_once(content: str, marker: str, section: str, section_key: str) -> str:
    if section_key in content:
        return content
    if content.count(marker) != 1:
        raise RuntimeError(f"anchor mismatch for {section_key}: {content.count(marker)}")
    return content.replace(marker, section + marker, 1)


def strengthen_existing() -> dict[str, int]:
    spec = load(SPEC)
    p93 = prompt(spec, "P93")
    p93_before = len(p93["copyContent"])
    p93["inspectFirst"] = append_once(
        p93["inspectFirst"],
        " For agent-authored claims, recover the relevant information available to the generating agent so missing-context factuality can be separated from present-but-ignored faithfulness.",
    )
    p93["expectedOutput"] = append_once(
        p93["expectedOutput"],
        " When an agent-generated claim misses source truth, include a factuality/faithfulness/attention classification and the matched repair.",
    )
    p93["proofGate"] = append_once(
        p93["proofGate"],
        " A material contradiction or omission of authoritative information already available in generation context is a faithfulness hallucination and reopens closure; do not repair it by blindly adding more context.",
    )
    p93_section = """

2A. CHECK FAITHFULNESS BEFORE FETCHING MORE
When an agent authored the claim, pin the authoritative truth and the relevant generation context when recoverable. Classify a material mismatch as FACTUALITY_MISSING_CONTEXT (needed truth absent), FAITHFULNESS_CONTEXT_IGNORED (truth/instruction present but ignored, contradicted, or materially underused), ATTENTION_SATURATION (required truth present inside distracting/overgrown context), MIXED, or UNKNOWN.
A confident, plausible, good-faith answer can still fail closure. Missing context calls for targeted retrieval/grounding. If the correct information was already available, do not reflexively add more context: re-anchor to the smallest authoritative sources, compact stale/distracting material, rebuild the affected obligations, and rerun certification.
"""
    p93["copyContent"] = insert_before_once(
        p93["copyContent"], "\n\n3. FALSIFY CLOSURE", p93_section, "2A. CHECK FAITHFULNESS BEFORE FETCHING MORE"
    )
    for keyword in ("faithfulness hallucination", "faith hallucination", "factuality hallucination", "ignored context"):
        add_keyword(p93, keyword)
    save(SPEC, spec)

    ledger = load(LEDGER)
    p83 = prompt(ledger, "P83")
    p83_before = len(p83["copyContent"])
    p83["inspectFirst"] = append_once(
        p83["inspectFirst"],
        " For a materially wrong prior result, recover the relevant context/source material that agent had so missing-context and ignored-context failures are not conflated.",
    )
    p83["proofGate"] = append_once(
        p83["proofGate"],
        " If authoritative information was already available but the prior output contradicted or materially omitted it, classify that faithfulness failure explicitly and re-anchor before retrieving more context.",
    )
    p83_section = """

2A. CHECK SOURCE FAITHFULNESS
For a materially wrong confident result, compare the claim with authoritative information actually available to that agent when recoverable. Missing truth is a factuality gap; present-but-ignored or contradicted truth is a faithfulness hallucination. For faithfulness, re-anchor/compact the authoritative context before fetching more; for factuality, retrieve the missing source. Then rerun the claim-to-evidence check.
"""
    p83["copyContent"] = insert_before_once(
        p83["copyContent"], "\n\n3. ESTABLISH THE CURRENT FLOOR", p83_section, "2A. CHECK SOURCE FAITHFULNESS"
    )
    for keyword in ("faithfulness hallucination", "ignored provided context"):
        add_keyword(p83, keyword)
    if len(p83["copyContent"]) >= 8000:
        raise RuntimeError(f"P83 anti-bloat ceiling exceeded: {len(p83['copyContent'])}")
    save(LEDGER, ledger)

    ai = load(AI)
    p67 = prompt(ai, "P67")
    p67_before = len(p67["copyContent"])
    p67["expectedOutput"] = append_once(
        p67["expectedOutput"],
        " For hallucination-prone tasks, include paired factuality/faithfulness cases and score whether the system chose the repair that matches the cause.",
    )
    p67["proofGate"] = append_once(
        p67["proofGate"],
        " Hallucination evals distinguish missing-context factuality from present-but-ignored faithfulness rather than scoring every wrong answer as the same failure.",
    )
    p67_section = """

3A. EVALUATE HALLUCINATION DIAGNOSIS, NOT JUST THE FINAL ANSWER
Add paired cases where required truth is absent versus explicitly present in context. The missing-context case should trigger targeted grounding; the present-but-ignored case should trigger re-anchoring/compaction rather than blindly adding context. Include exact IDs, API/schema signatures, and tool-call parameters that deterministic validators can reject. Score both the failure classification and whether remediation matches the cause.
"""
    p67["copyContent"] = insert_before_once(
        p67["copyContent"], "\n\n4. MAKE SCORING REPRODUCIBLE", p67_section, "3A. EVALUATE HALLUCINATION DIAGNOSIS"
    )
    for keyword in ("factuality eval", "faithfulness eval", "hallucination eval"):
        add_keyword(p67, keyword)

    p68 = prompt(ai, "P68")
    p68_before = len(p68["copyContent"])
    p68["inspectFirst"] = append_once(
        p68["inspectFirst"],
        " Include evidence of attention degradation: required facts already present but ignored as history, logs, schemas, or retrieved material accumulate.",
    )
    p68["expectedOutput"] = append_once(
        p68["expectedOutput"],
        " When attention saturation is observed, include a provenance-preserving compaction or fresh-session handoff and prove critical constraints survive it.",
    )
    p68["proofGate"] = append_once(
        p68["proofGate"],
        " If required truth is already present but ignored, the first repair reduces/reprioritizes context rather than adding more; compaction must preserve authoritative constraints and provenance.",
    )
    p68_section = """

4A. RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE
Treat long context as a failure surface when required information is present but no longer followed reliably. Use a measured or system-defined budget threshold rather than a universal percentage. Compact CLI noise to decision-relevant signatures; replace large raw files with source-pinned AST/schema/outlines when safe; preserve decisions, unresolved constraints, and provenance in a structured mission brief; use rolling/sliding compaction; and hand bounded subtasks to a fresh session when that reduces distraction without losing authority. If correct information is already present but ignored, do not add more context first. Prove the compacted/fresh context still contains the critical constraints and preserves representative task quality.
"""
    p68["copyContent"] = insert_before_once(
        p68["copyContent"], "\n\n5. TEST CONTEXT SELECTION", p68_section, "4A. RECOVER FROM ATTENTION SATURATION"
    )
    for keyword in ("attention saturation", "dumb zone", "context compaction", "fresh session handoff", "sliding window compaction"):
        add_keyword(p68, keyword)
    save(AI, ai)

    return {
        "P93_before": p93_before,
        "P93_after": len(p93["copyContent"]),
        "P83_before": p83_before,
        "P83_after": len(p83["copyContent"]),
        "P67_before": p67_before,
        "P67_after": len(p67["copyContent"]),
        "P68_before": p68_before,
        "P68_after": len(p68["copyContent"]),
    }


DIAG_DRAFT = {
    "name": "Factuality vs Faithfulness Hallucination Diagnoser",
    "type": "DIAGNOSE + REPAIR",
    "class": "AI ENGINEERING / HALLUCINATION DIAGNOSIS",
    "sprintRole": "Classify a plausible but wrong agent result by whether required truth was missing, ignored despite being present, or lost inside attention-saturating context, then apply the repair matched to that cause",
    "useWhen": "An LLM or agent confidently produced a wrong, incomplete, contradictory, or invented answer/code/plan/report and the next step depends on knowing whether the source truth was absent from context or already present but not followed.",
    "inspectFirst": "The exact failed claim/output; authoritative truth; relevant generation-time prompt/context when recoverable; retrieved sources and tool results; system/user instructions; context size/composition; validation failures; and whether the disputed fact or constraint was actually available before generation.",
    "expectedOutput": "An evidence-linked classification of FACTUALITY_MISSING_CONTEXT, FAITHFULNESS_CONTEXT_IGNORED, ATTENTION_SATURATION, MIXED, or UNKNOWN; matched remediation; a rerun of the same bounded case; and a proof ceiling that does not infer internal attention from output alone.",
    "nextStep": "Pin one concrete false claim, search the recoverable generation context for the authoritative fact/constraint, classify the failure from that evidence, apply the matched retrieval or compaction/re-anchoring repair, and rerun the same case plus one counterexample.",
    "proofGate": "The diagnosis proves whether the needed truth was absent or present in recoverable context; remediation matches that classification; UNKNOWN remains explicit when historical context cannot be recovered; a counterexample prevents labeling every error as one class; and the repaired case passes without claiming access to hidden model reasoning.",
    "color": "Teal",
    "category": "standard",
    "copyContent": """DIAGNOSE THE HALLUCINATION BEFORE TRYING TO FIX IT. MISSING KNOWLEDGE AND IGNORED KNOWLEDGE REQUIRE DIFFERENT FIRST RESPONSES.\n\nAgent/model surface: xyz_agent_or_model_surface\nFailed output / claim: xyz_failed_output\nAuthoritative truth: xyz_source_of_truth\nGeneration context: recover when available\n\nMISSION\nTurn `the agent hallucinated` into an evidence-backed failure classification. Determine whether the model lacked the required information, had the information but failed to follow it, or was operating in context so noisy/large that present constraints were not reliably reflected in the output. Then repair the cause and rerun the same bounded case. Do not diagnose hidden chain-of-thought or pretend output text reveals internal attention directly.\n\n1. PIN THE FAILURE AND TRUTH\nSelect one concrete wrong, invented, contradictory, or materially incomplete claim, code decision, identifier, parameter, or completion assertion. Pin the authoritative source that establishes the expected result. Separate correctness from style or preference.\n\n2. RECOVER WHAT WAS ACTUALLY AVAILABLE\nReconstruct the relevant generation-time context when possible: system/user instructions, source excerpts, retrieved files, tool results, schemas, prior summaries, and other material that could reasonably govern the disputed output. Search it directly for the required fact/constraint. Do not assume the model `must have known` something merely because it exists in training data or elsewhere in the repository.\n\n3. CLASSIFY THE FAILURE\nUse exactly one primary state, with secondary causes recorded when needed:\n- FACTUALITY_MISSING_CONTEXT — the required authoritative information was not supplied/retrieved into the relevant context.\n- FAITHFULNESS_CONTEXT_IGNORED — the required information/instruction was present and clear enough to govern the output, but the result contradicted, omitted, or materially underused it.\n- ATTENTION_SATURATION — the required information was present, while excessive/stale/competing context plausibly created an attention-selection failure; this is an operational diagnosis, not a claim to inspect hidden cognition.\n- MIXED — more than one evidenced cause materially contributed.\n- UNKNOWN — generation context or authority is insufficient to distinguish the classes.\nConfidence, fluency, or good faith does not lower the severity of a wrong result.\n\n4. MATCH THE REPAIR TO THE CAUSE\nFor FACTUALITY_MISSING_CONTEXT: retrieve the smallest authoritative source, inject exact signatures/records needed for the task, and preserve source identity.\nFor FAITHFULNESS_CONTEXT_IGNORED: do not reflexively add more context. Re-anchor the task to the smallest authoritative constraints, remove/deprioritize distractors, make precedence explicit, and regenerate.\nFor ATTENTION_SATURATION: compact or partition context with provenance; reduce raw logs/history/schema noise; preserve a structured mission brief; use a fresh bounded session/subtask when safe.\nFor MIXED: repair missing truth first, then compact/re-anchor.\nFor UNKNOWN: state the missing evidence and run the smallest safe probe that can distinguish the classes.\n\n5. VERIFY THE DIAGNOSIS\nRerun the same bounded case after the matched repair. Add at least one counterexample: a factuality fixture should not be `fixed` only by compaction, and a faithfulness fixture should not require invented new source truth. Record before/after context identity and observable result. A successful retry supports the diagnosis but does not prove hidden model mechanics.\n\n6. ROUTE SYSTEMIC FOLLOW-UP\nIf many cases show missing retrieval, route context/retrieval architecture to the context-engineering owner. If failures recur despite correct context, add paired eval cases and source-faithfulness checks. If exact APIs/IDs/schemas/tool calls are the risk, route to the deterministic grounding gate. If the failure invalidates a `done/closed` claim, reopen closure certification.\n\nDELIVER\nReport the failed claim; authoritative truth; recoverable generation-context evidence; classification and confidence boundary; matched repair; before/after result; counterexample; systemic owner if recurrence is proven; and exact remaining UNKNOWN or proof ceiling.""",
    "keywords": [
        "hallucination diagnosis",
        "factuality hallucination",
        "faithfulness hallucination",
        "faith hallucination",
        "missing context",
        "ignored context",
        "attention saturation",
        "dumb zone",
        "hallucination classifier",
        "context failure diagnosis",
    ],
}

GROUND_DRAFT = {
    "name": "Grounded Agent Output & Tool-Call Gate",
    "type": "BUILD + VALIDATE",
    "class": "AI ENGINEERING / GROUNDING",
    "sprintRole": "Prevent exactness-critical agent outputs and side effects from relying on lossy parametric recall by injecting current deterministic structure just in time and rejecting unsourced, contradictory, stale, or schema-invalid generations before execution",
    "useWhen": "An agent must generate exact API signatures, internal identifiers, repository contracts, SQL/tool-call parameters, schemas, commands, or other details where a plausible invented value can cause failure or unsafe side effects.",
    "inspectFirst": "The exactness-critical output fields; canonical types/OpenAPI/AST/database/tool schemas/manifests/contracts; current source/version identity; agent prompt and tool adapter; validation/execution boundary; existing parsers/typecheckers/schema validators; stale-schema behavior; and side-effect authority.",
    "expectedOutput": "A JIT grounding packet with provenance, deterministic pre-execution validator/interceptor, bounded attribution for critical claims/parameters, fail-closed gate states, positive/negative/stale-source fixtures, and integration proof that no protected side effect occurs before grounding validation passes.",
    "nextStep": "Choose the highest-risk exact field or tool call, extract its current authoritative schema/signature into a compact source-pinned grounding packet, intercept the generated output before execution, reject one hallucinated and one stale value, then prove a valid value reaches the existing side-effect boundary exactly once.",
    "proofGate": "Exactness-critical values are validated against current authoritative structure rather than model recall; grounding/checker failure blocks execution; stale source identity fails or refreshes explicitly; critical attribution is verifiable without forcing citations on decorative prose; side effects remain behind the gate; and tests prove valid, absent, contradictory, malformed, and stale cases.",
    "color": "Purple",
    "category": "standard",
    "copyContent": """GROUND EXACT AGENT OUTPUTS BEFORE THEY CAN EXECUTE. TREAT MODEL MEMORY AS LOSSY; USE CURRENT DETERMINISTIC STRUCTURE FOR DETAILS THAT MUST BE EXACT.\n\nRepo/system: xyz_repo_or_system\nAgent/tool boundary: xyz_agent_tool_boundary\nExactness-critical fields: xyz_exact_fields\nCanonical structure: resolve from current source\n\nMISSION\nBuild a narrow prevention layer for hallucinated exact details. Just before generation or tool execution, extract the smallest authoritative structural facts the task needs, attach provenance/version identity, and validate the proposed output deterministically. Do not ask the model to remember an API signature, identifier, schema, or repository contract that code can retrieve and check exactly.\n\n1. MARK THE EXACTNESS-CRITICAL SURFACE\nIdentify fields where plausible-but-wrong output is unacceptable: function/type signatures, enum values, internal IDs, hostnames/paths governed by manifests, OpenAPI operations, database columns, tool names/arguments, command syntax, versioned contracts, or other repository-owned exact facts. Keep subjective prose and open-ended design outside this gate.\n\n2. BUILD JUST-IN-TIME GROUNDING\nPrefer current machine-readable sources: TypeScript/type metadata, OpenAPI/JSON Schema, AST/symbol outlines, database introspection, tool schemas, manifests/registries, generated contracts, or exact source slices. Produce a compact grounding packet containing source identity/version and only the signatures/constraints needed now. This is dynamic grounding, not wholesale context loading.\n\nWhen research and synthesis are materially different jobs, a gathering stage may build the verified dossier and a synthesis stage may consume it; the dossier remains the authority boundary between them.\n\n3. REQUIRE VERIFIABLE ATTRIBUTION WHERE IT MATTERS\nFor critical claims and parameters, retain a source key/span/schema path that a validator can resolve back to the grounding packet. Do not require noisy citations for every formatting choice or ordinary connective prose. Untethered exact values must be rejected or explicitly downgraded to non-executable output.\n\n4. INSTALL THE FAIL-CLOSED INTERCEPTOR\nBefore any protected tool call or side effect, validate generated output against the current grounding packet and canonical schema. Use repository-native parsers/typecheckers/schema validators rather than model judgment where possible. Suggested outcomes:\n- GROUNDED_PASS\n- UNSOURCED_BLOCK\n- CONTRADICTION_BLOCK\n- SCHEMA_MISMATCH\n- GROUNDING_FAILURE\nMalformed grounding data, checker failure, missing provenance, or stale source identity is never silent PASS. The host/runtime owns execution authority.\n\n5. TEST THE ZERO-ENTROPY BOUNDARY\nAt minimum exercise:\n- hallucinated identifier absent from the authoritative schema -> BLOCK;\n- value contradicting an in-context constraint -> BLOCK;\n- malformed or unavailable grounding/checker -> GROUNDING_FAILURE;\n- stale schema/version -> refresh or BLOCK;\n- valid exact signature/parameter -> PASS and existing side-effect path executes once.\nUse deterministic checks before model-as-judge checks. Do not weaken the validator to bless model output.\n\n6. ADVERSARIAL CONSISTENCY PASS\nAfter generation, compare critical proposed facts/actions with the grounding dossier again. This may be a deterministic checker or a bounded critic when semantics cannot be expressed mechanically. The critic cannot override a deterministic schema failure. Repair and regenerate until the bounded gate passes or an exact source/authority blocker remains.\n\n7. KEEP CONTEXT LEAN\nDo not solve grounding by dumping entire repositories or API catalogs into the prompt. Retrieve only the needed structures, cache with explicit invalidation when safe, and route systemic context-budget/attention problems to the context-engineering owner. Route eval-suite design to the eval owner and retries/idempotency after a valid tool call to the agent-reliability owner.\n\nDELIVER\nReport exactness-critical fields; authoritative sources and version IDs; grounding-packet shape; interceptor/gate owner; blocked and passing fixtures; side-effect proof; stale/checker-failure behavior; residual semantic judgments; proof ceiling; and exact implementation/integration state.""",
    "keywords": [
        "agent grounding",
        "dynamic knowledge grounding",
        "jit schema injection",
        "zero entropy grounding",
        "source grounding checker",
        "tool call validation",
        "schema grounded agent",
        "hallucinated identifiers",
        "verifiable attribution",
        "research synthesize agents",
    ],
}


def add_new_prompts() -> list[dict]:
    current = load(AI)
    names = {p.get("name") for p in current["prompts"]}
    receipts: list[dict] = []
    for draft in (DIAG_DRAFT, GROUND_DRAFT):
        if draft["name"] in names:
            existing = next(p for p in load(AI)["prompts"] if p.get("name") == draft["name"])
            receipts.append({"status": "already-present", "id": existing["id"], "name": draft["name"]})
            continue
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(draft, handle, indent=2, ensure_ascii=False)
            draft_path = handle.name
        try:
            out = run(
                sys.executable,
                str(HELPER.relative_to(ROOT)),
                "add",
                "--input",
                draft_path,
                "--registry",
                "ai-engineering-level-up-prompts",
                capture=True,
            )
            receipt = json.loads(out)
            receipts.append(receipt)
            names.add(draft["name"])
        finally:
            Path(draft_path).unlink(missing_ok=True)
    return receipts


def strengthen_tests() -> None:
    spec_test = SPEC_TEST.read_text(encoding="utf-8")
    anchor = '        self.assertIn("NOT CERTIFIED", p93)\n'
    insert = anchor + (
        '        self.assertIn("CHECK FAITHFULNESS BEFORE FETCHING MORE", p93)\n'
        '        self.assertIn("FACTUALITY_MISSING_CONTEXT", p93)\n'
        '        self.assertIn("FAITHFULNESS_CONTEXT_IGNORED", p93)\n'
        '        self.assertIn("ATTENTION_SATURATION", p93)\n'
        '        self.assertIn("A confident, plausible, good-faith answer can still fail closure", p93)\n'
        '        self.assertIn("do not reflexively add more context", p93)\n'
    )
    if 'self.assertIn("CHECK FAITHFULNESS BEFORE FETCHING MORE", p93)' not in spec_test:
        if spec_test.count(anchor) != 1:
            raise RuntimeError("P93 focused-test anchor mismatch")
        spec_test = spec_test.replace(anchor, insert, 1)
    SPEC_TEST.write_text(spec_test, encoding="utf-8")

    ledger_test = LEDGER_TEST.read_text(encoding="utf-8")
    anchor = '            "TREAT CLAIMS AS HYPOTHESES",\n'
    insert = anchor + (
        '            "CHECK SOURCE FAITHFULNESS",\n'
        '            "faithfulness hallucination",\n'
        '            "re-anchor/compact the authoritative context before fetching more",\n'
    )
    if '"CHECK SOURCE FAITHFULNESS"' not in ledger_test:
        if ledger_test.count(anchor) != 1:
            raise RuntimeError("P83 focused-test anchor mismatch")
        ledger_test = ledger_test.replace(anchor, insert, 1)
    LEDGER_TEST.write_text(ledger_test, encoding="utf-8")

    ai_test = AI_TEST.read_text(encoding="utf-8")
    method_anchor = "    def test_prompt_finder_and_search_route_the_five_tracks(self) -> None:\n"
    new_method = '''    def test_hallucination_failure_modes_have_diagnostic_grounding_and_context_owners(self) -> None:\n        prompts = build_prompt_kit_registry.load_prompt_registry()\n        by_id = {item["id"]: item for item in prompts}\n        p67 = by_id["P67"]["copyContent"]\n        for phrase in (\n            "EVALUATE HALLUCINATION DIAGNOSIS",\n            "required truth is absent versus explicitly present",\n            "targeted grounding",\n            "re-anchoring/compaction",\n        ):\n            self.assertIn(phrase, p67)\n        p68 = by_id["P68"]["copyContent"]\n        for phrase in (\n            "RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE",\n            "measured or system-defined budget threshold",\n            "rolling/sliding compaction",\n            "fresh session",\n            "do not add more context first",\n        ):\n            self.assertIn(phrase, p68)\n\n        by_name = {item["name"]: item for item in prompts}\n        diagnostic = by_name["Factuality vs Faithfulness Hallucination Diagnoser"]\n        grounding = by_name["Grounded Agent Output & Tool-Call Gate"]\n        self.assertNotEqual(diagnostic["id"], grounding["id"])\n        self.assertEqual(diagnostic["seq"], diagnostic["id"][1:])\n        self.assertEqual(grounding["seq"], grounding["id"][1:])\n        self.assertEqual(diagnostic["copySheet"], f"{diagnostic['id']}_COPY_SAFE")\n        self.assertEqual(grounding["copySheet"], f"{grounding['id']}_COPY_SAFE")\n        self.assertEqual(diagnostic["class"], "AI ENGINEERING / HALLUCINATION DIAGNOSIS")\n        self.assertEqual(grounding["class"], "AI ENGINEERING / GROUNDING")\n        for phrase in (\n            "FACTUALITY_MISSING_CONTEXT",\n            "FAITHFULNESS_CONTEXT_IGNORED",\n            "ATTENTION_SATURATION",\n            "MATCH THE REPAIR TO THE CAUSE",\n            "counterexample",\n        ):\n            self.assertIn(phrase, diagnostic["copyContent"])\n        for phrase in (\n            "BUILD JUST-IN-TIME GROUNDING",\n            "REQUIRE VERIFIABLE ATTRIBUTION WHERE IT MATTERS",\n            "FAIL-CLOSED INTERCEPTOR",\n            "GROUNDING_FAILURE",\n            "hallucinated identifier",\n            "critic cannot override a deterministic schema failure",\n        ):\n            self.assertIn(phrase, grounding["copyContent"])\n        policy = build_prompt_kit_registry.load_actionability_policy()\n        for item in (diagnostic, grounding):\n            self.assertEqual(item["actionabilityPolicy"], policy["policy_id"])\n            self.assertIn(policy["marker"], item["copyContent"])\n        raw = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))\n        raw_by_name = {item["name"]: item for item in raw["prompts"]}\n        self.assertLess(len(raw_by_name[diagnostic["name"]]["copyContent"]), 8000)\n        self.assertLess(len(raw_by_name[grounding["name"]]["copyContent"]), 8000)\n\n'''
    if "test_hallucination_failure_modes_have_diagnostic_grounding_and_context_owners" not in ai_test:
        if ai_test.count(method_anchor) != 1:
            raise RuntimeError("AI focused-test anchor mismatch")
        ai_test = ai_test.replace(method_anchor, new_method + method_anchor, 1)
    AI_TEST.write_text(ai_test, encoding="utf-8")


def main() -> int:
    print("=== HELPER INSPECT ===", flush=True)
    run(sys.executable, str(HELPER.relative_to(ROOT)), "inspect")
    sizes = strengthen_existing()
    print(json.dumps({"strengthened_raw_sizes": sizes}, indent=2), flush=True)
    receipts = add_new_prompts()
    print(json.dumps({"helper_receipts": receipts}, indent=2), flush=True)
    strengthen_tests()

    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", str(SITE.relative_to(ROOT)))
    run(sys.executable, str(HELPER.relative_to(ROOT)), "validate")
    run(sys.executable, "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
    run(sys.executable, "-m", "unittest", "tests.test_repository_work_ledger_prompt", "-v")
    run(sys.executable, "-m", "unittest", "tests.test_ai_engineering_level_up", "-v")
    run(sys.executable, "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "tests.test_prompt_language_audit", "-v")
    run(sys.executable, "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "tests.test_prompt_kit_order_navigation_product", "-v")
    run(sys.executable, "scripts/evaluate_prompt_language.py", "--output", "Outputs/prompt-language-audit.json", "--summary")
    run(sys.executable, "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(sys.executable, "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--output", "Outputs/prompt-kit-order-navigation-audit.json", "--summary")
    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", str(SITE.relative_to(ROOT)), "--check")
    run("git", "diff", "--check")

    all_prompts = build_all = None
    # Resolve final helper-owned identities without hard-coding them in source/tests.
    ai = load(AI)
    final = {
        p["name"]: {"id": p["id"], "seq": p["seq"], "copySheet": p["copySheet"]}
        for p in ai["prompts"]
        if p.get("name") in {DIAG_DRAFT["name"], GROUND_DRAFT["name"]}
    }
    print(json.dumps({"final_new_prompt_identities": final}, indent=2), flush=True)

    run("git", "add",
        str(SPEC.relative_to(ROOT)),
        str(AI.relative_to(ROOT)),
        str(LEDGER.relative_to(ROOT)),
        str(SPEC_TEST.relative_to(ROOT)),
        str(AI_TEST.relative_to(ROOT)),
        str(LEDGER_TEST.relative_to(ROOT)),
        str(SITE.relative_to(ROOT)),
    )
    run("git", "diff", "--cached", "--check")
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged.returncode != 0:
        run("git", "commit", "-m", "feat(prompt-kit): diagnose and prevent agent hallucinations")
    else:
        print("No durable semantic changes to commit", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
