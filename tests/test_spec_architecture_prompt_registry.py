from __future__ import annotations

import json
import unittest
from pathlib import Path

import build_prompt_kit
from scripts import build_prompt_kit_registry
from scripts import prompt_registry_ops


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"


class SpecArchitecturePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operational = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.full = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        raw_prompts = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        cls.raw = {prompt["id"]: prompt for prompt in raw_prompts}

    def test_p76_is_operational_and_distinct_from_general_context_engineering(self) -> None:
        prompt = self.operational["P76"]
        self.assertEqual(prompt["seq"], "76")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / SPEC ARCHITECTURE")
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], prompt["copyContent"])
        self.assertEqual(self.operational["P68"]["class"], "AI ENGINEERING / CONTEXT")
        self.assertNotEqual(self.operational["P68"]["class"], prompt["class"])

    def test_prompt_encodes_three_zoom_levels_and_demand_loaded_ground_detail(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("50,000 FT — ORIENTATION", content)
        self.assertIn("30,000 FT — DOMAIN / CAPABILITY", content)
        self.assertIn("15,000 FT — WORKFLOW / SPEC", content)
        self.assertIn("Target <= 1,000 approximate tokens", content)
        self.assertIn("Target <= 2,000 additional approximate tokens", content)
        self.assertIn("Target <= 4,000 additional approximate tokens", content)
        self.assertIn("Large code files, historical reports, full schemas, fixtures", content)
        self.assertIn("remain on-demand", content)

    def test_prompt_factors_authority_instead_of_summarizing_everything(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("`AGENTS.md`: governance, precedence, universal safety/operating law", content)
        self.assertIn("skills: repeatable procedure and judgment only", content)
        self.assertIn("Preserve one canonical owner and lightweight references elsewhere", content)
        self.assertIn("Do not preload every skill, nested AGENTS file, tool schema", content)
        self.assertIn("IMPLEMENT, DON'T JUST RECOMMEND", content)
        self.assertIn("no unique rule or authority disappeared", content)

    def test_prompt_requires_measured_before_after_retrieval_cost(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("MEASURE BEFORE MODIFYING", content)
        self.assertIn("What is this app and how is it organized?", content)
        self.assertIn("Record which files and approximate tokens/bytes", content)
        self.assertIn("measured default context falls meaningfully", content)
        self.assertIn("representative tasks still succeed", content)

    def test_glossary_prompt_reduces_prose_without_creating_competing_truth(self) -> None:
        prompt = self.full["P78"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "78")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / KNOWLEDGE ARCHITECTURE")
        self.assertIn("DIET THE REPOSITORY DOCUMENTATION DOWN TO A LEAN GLOSSARY", content)
        self.assertIn("glossary may explain vocabulary", content)
        self.assertIn("must not become a second specification", content)
        self.assertIn("KEEP-AUTHORITY, KEEP-OPERATIONAL, COLLAPSE-INTO-GLOSSARY", content)
        self.assertIn("Do not create a new tutorial", content)
        self.assertIn("current code plus its contracts/tests/validators", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_prompt_adder_uses_low_friction_helper_without_losing_semantic_proof(self) -> None:
        prompt = self.full["P79"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "79")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "PROMPT KIT / REGISTRY OPERATIONS")
        self.assertIn("CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION", content)
        self.assertIn("DO NOT ASK ME TO RESTATE CONTEXT", content)
        self.assertIn("scripts/prompt_registry_ops.py add", content)
        self.assertIn("Do NOT set id, seq, or copySheet", content)
        self.assertIn("roll back registry/site writes if validation fails", content)
        self.assertIn("focused semantic assertion", content)
        self.assertIn("materially overlapping prompt", content)
        self.assertIn("genuinely missing bounded behavior", content)
        self.assertIn("Do not fall back to loading the entire Prompt Kit architecture", content)
        self.assertIn("merge the exact green authorized head", content)
        self.assertLess(len(self.raw["P79"]["copyContent"]), 5000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_prompt_registry_ops_exposes_compact_current_routing_and_auto_identity(self) -> None:
        state = prompt_registry_ops.inspect_state()
        self.assertRegex(state["next_id"], r"^P\d+$")
        self.assertEqual(state["next_id"][1:], state["next_seq"])
        self.assertIn("id", state["auto_fields"])
        self.assertIn("seq", state["auto_fields"])
        self.assertIn("copySheet", state["auto_fields"])
        ids = {item["registry_id"] for item in state["registries"]}
        self.assertIn("spec-architecture-prompts", ids)
        self.assertGreaterEqual(len(ids), 6)

    def test_prompt_registry_ops_dry_run_builds_complete_record_without_mutation(self) -> None:
        draft = {
            "name": "Prompt Ops Test Fixture",
            "type": "MAINTENANCE",
            "class": "PROMPT KIT / TEST",
            "sprintRole": "Exercise low-friction prompt contribution",
            "useWhen": "A deterministic helper regression is required.",
            "inspectFirst": "Current registry truth.",
            "expectedOutput": "A complete dry-run prompt record.",
            "nextStep": "Validate the dry-run record.",
            "proofGate": "No tracked source is mutated by dry-run.",
            "copyContent": "EXECUTE A DETERMINISTIC PROMPT REGISTRY HELPER TEST. " * 12,
            "keywords": ["prompt ops fixture", "registry helper fixture"],
            "profile": "spec-architecture",
            "color": "Cyan",
        }
        result = prompt_registry_ops.add_prompt(
            draft, "spec-architecture-prompts", dry_run=True
        )
        record = result["record"]
        self.assertEqual(result["status"], "dry-run")
        self.assertRegex(record["id"], r"^P\d+$")
        self.assertEqual(record["copySheet"], f"{record['id']}_COPY_SAFE")
        self.assertEqual(record["profile"], "spec-architecture")
        self.assertEqual(record["color"], "Cyan")
        self.assertEqual(record["category"], "standard")

    def test_p07_requires_repeated_evidence_passes_until_fixed_point(self) -> None:
        p07 = self.full["P07"]
        content = p07["copyContent"]
        self.assertIn("ITERATIVE SPRINT FIXED-POINT", content)
        self.assertIn("IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE", content)
        self.assertIn("at least one deliberate second-pass review", content)
        self.assertIn("Continue until a bounded fixed point", content)
        self.assertIn("Do not manufacture churn", content)
        self.assertIn("Each pass must either create/repair an owned artifact", content)
        self.assertIn("ITERATION EVIDENCE", content)
        self.assertIn("fixed-point reason", content)
        self.assertIn("only then stop", content)

    def test_client_prompt_pack_builds_local_overlay_without_global_mutation(self) -> None:
        prompt = self.full["P80"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "80")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["class"], "PROMPT KIT / LOCAL PROFILE")
        self.assertIn("GLOBAL VS LOCAL BOUNDARY", content)
        self.assertIn("JSON file upload", content)
        self.assertIn("paste-JSON/text area", content)
        self.assertIn("type/color chips", content)
        self.assertIn("local:<profile_id>:<prompt_id>", content)
        self.assertIn("same search index", content)
        self.assertIn("Favorites", content)
        self.assertIn("export -> clear -> re-import", content)
        self.assertIn("Treat uploaded/pasted JSON as hostile input", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_cache_prompt_covers_invalidation_and_production_failure_modes(self) -> None:
        prompt = self.full["P81"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "81")
        self.assertEqual(prompt["class"], "SOFTWARE ARCHITECTURE / CACHING")
        self.assertIn("Client browser", content)
        self.assertIn("Distributed L2", content)
        self.assertIn("TTL / PASSIVE INVALIDATION", content)
        self.assertIn("EVENT-DRIVEN / ACTIVE INVALIDATION", content)
        self.assertIn("CACHE VERSIONING / KEY NAMESPACING", content)
        self.assertIn("CACHE STAMPEDE / THUNDERING HERD", content)
        self.assertIn("CACHE PENETRATION", content)
        self.assertIn("CACHE AVALANCHE", content)
        self.assertIn("TTL jitter", content)
        self.assertIn("Bloom filter", content)
        self.assertIn("negative caching", content)
        self.assertIn("probabilistic early expiration", content)
        self.assertIn("REDIS VS MEMCACHED", content)
        self.assertIn("L1 + L2 COHERENCE", content)
        self.assertIn("benchmark the actual runtime", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_prototyping_prompt_enforces_measured_iteration_to_final(self) -> None:
        prompt = self.full["P82"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "82")
        self.assertEqual(prompt["class"], "ENGINEERING / PROTOTYPING")
        self.assertIn("PROTOTYPE LADDER", content)
        self.assertIn("HYPOTHESIS -> BUILD -> MEASURE -> CRITIQUE -> DECIDE", content)
        self.assertIn("Do not present a prototype as final", content)
        self.assertIn("Preserve the last known-good candidate", content)
        self.assertIn("SAME acceptance rubric", content)
        self.assertIn("USE FEEDBACK WITHOUT TURNING THE USER INTO THE TEST RUNNER", content)
        self.assertIn("REMOVE PROTOTYPE DEBT BEFORE FINAL", content)
        self.assertIn("FINAL PROOF IS STRICTER THAN PROTOTYPE PROOF", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_new_source_prompts_are_intentionally_bounded(self) -> None:
        for prompt_id in ("P78", "P79", "P80", "P81", "P82"):
            content = self.raw[prompt_id]["copyContent"]
            self.assertLess(len(content), 8000)
            self.assertGreater(len(content), 1800)

    def test_raw_p76_prompt_is_itself_bounded(self) -> None:
        content = self.raw["P76"]["copyContent"]
        self.assertLess(len(content), 7000)
        self.assertGreater(len(content), 2500)

    def test_discovery_aliases_route_spec_bloat_queries_to_p76(self) -> None:
        self.assertEqual(build_prompt_kit.SYNONYMS["spec driven development"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["progressive disclosure"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["harness bloat"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["50000 ft"], "P76")

    def test_render_contains_spec_profile_and_extended_architecture_prompts(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("prompt-kit-spec-architecture-styles", html)
        self.assertIn("spec-architecture", html)
        self.assertIn("◎ Spec Layers", html)
        self.assertIn("Progressive-Disclosure Spec & Harness Factorer", html)
        self.assertIn("Repository Glossary & Documentation Diet", html)
        self.assertIn("Prompt Registry Prompt Adder", html)
        self.assertIn("Client Prompt Pack & Local Profile Builder", html)
        self.assertIn("Multi-Tier Cache Architecture & Invalidation Hardener", html)
        self.assertIn("Prototype-Measure-Refine Delivery Loop", html)

    def test_prompt_semantic_hardener_selectively_integrates_stronger_principles(self) -> None:
        matches = [
            prompt
            for prompt in self.full.values()
            if prompt["name"] == "Prompt Semantic Hardener & Principle Integrator"
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        raw_content = self.raw[prompt["id"]]["copyContent"]
        self.assertEqual(prompt["id"], "P86")
        self.assertEqual(prompt["seq"], "86")
        self.assertEqual(prompt["copySheet"], "P86_COPY_SAFE")
        self.assertEqual(prompt["category"], "standard")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "PROMPT KIT / PROMPT ARCHITECTURE")
        self.assertIn("RAW VS EFFECTIVE PROMPT", content)
        self.assertIn("PRINCIPLE APPLICABILITY MATRIX", content)
        self.assertIn("COMPATIBLE, INCOMPATIBLE, or NOT NEEDED", content)
        self.assertIn("P03 REFERENCE CASE", content)
        for donor in ("P07", "P13", "P48", "P76", "P83", "P84", "P85"):
            self.assertIn(donor, content)
        self.assertIn(
            "do not transform P03 into P07, P13, P48, P76, P83, P84, or P85",
            content,
        )
        self.assertIn("Do not copy every strong rule into every prompt", content)
        self.assertIn("shared policy", content.lower())
        self.assertIn("Extend the closest existing focused test", content)
        self.assertIn("one deliberate second pass", content)
        self.assertIn(
            "Refresh again immediately before final exact-head conclusions", content
        )
        self.assertLess(len(raw_content), 7600)
        self.assertGreater(len(raw_content), 3000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn("Prompt Semantic Hardener & Principle Integrator", html)


    def test_bidirectional_use_case_hook_routes_intent_and_reverse_ownership(self) -> None:
        matches = [
            prompt
            for prompt in self.full.values()
            if prompt["name"] == 'Bidirectional Use-Case Hook & Repository Route Builder'
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        raw_content = self.raw[prompt["id"]]["copyContent"]
        self.assertEqual(prompt["id"], 'P87')
        self.assertEqual(prompt["seq"], '87')
        self.assertEqual(prompt["copySheet"], 'P87_COPY_SAFE')
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / ROUTING ARCHITECTURE")
        self.assertIn("BIDIRECTIONAL ROUTE CONTRACT", content)
        self.assertIn("USER INTENT -> TRIGGER / HOOK -> CAPABILITY", content)
        self.assertIn("SCRIPT / MANIFEST / VALIDATOR / PROMPT / WORKFLOW / CAPABILITY RECORD", content)
        self.assertIn("INTENT OVER FILENAME", content)
        self.assertIn("REVERSE-OWNERSHIP QUESTIONS", content)
        self.assertIn("Why does this resource exist?", content)
        self.assertIn("What capability or supported use case owns it?", content)
        self.assertIn("PROVE BOTH DIRECTIONS", content)
        self.assertIn("A. INTENT-FIRST", content)
        self.assertIn("B. IMPLEMENTATION-FIRST", content)
        self.assertIn("without a pre-supplied implementation filename", content)
        self.assertIn("Do not create a second capabilities registry", content)
        self.assertIn("Harness Builder may create or repair general harness infrastructure", content)
        self.assertIn("Progressive-Disclosure factoring may reduce default context", content)
        self.assertGreater(len(raw_content), 3500)
        self.assertLess(len(raw_content), 9000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn('Bidirectional Use-Case Hook & Repository Route Builder', html)


    def test_lua_flagging_host_enforcement_prompt_preserves_host_control_and_repair_loop(self) -> None:
        matches = [
            prompt
            for prompt in self.full.values()
            if prompt["name"] == "Lua Flagging + Host Enforcement Repair Loop"
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        raw_content = self.raw[prompt["id"]]["copyContent"]
        self.assertEqual(prompt["id"], "P90")
        self.assertEqual(prompt["seq"], "90")
        self.assertEqual(prompt["copySheet"], "P90_COPY_SAFE")
        self.assertEqual(prompt["category"], "standard")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / LUA HOST ENFORCEMENT")
        self.assertIn("Lua detects and classifies command defects", content)
        self.assertIn("host language validates the finding schema", content)
        self.assertIn("Lua error, malformed Lua result, or checker failure", content)
        self.assertIn("wrong-shell syntax", content)
        self.assertIn("Bash constructs emitted for a PowerShell or CMD operator path", content)
        self.assertIn("CHECKER_FAILURE", content)
        self.assertIn("SCAN -> LUA FLAGS -> HOST BLOCK/RAISE -> AGENT REPAIR -> REVALIDATE", content)
        self.assertIn("Pass 2 must inspect the repaired command plus nearby failure classes", content)
        self.assertIn("Do not ask the user to choose between technically equivalent safe implementations", content)
        self.assertIn("Escalate only when progress truly requires user-controlled credentials", content)
        self.assertIn("Do not claim command safety from Lua-only tests", content)
        self.assertGreater(len(raw_content), 5000)
        self.assertLess(len(raw_content), 8000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn("Lua Flagging + Host Enforcement Repair Loop", html)

    def test_failure_suite_prompts_cover_class_path_and_closure_without_collapsing_roles(self) -> None:
        expected = {
            "P91": ("Failure-Class Generalization & Repository Audit", "TESTING / FAILURE GENERALIZATION"),
            "P92": ("Production-Path Proof Gap Auditor", "TESTING / PRODUCTION PATH"),
            "P93": ("Use-Case Closure Certification", "VERIFICATION / USE-CASE CLOSURE"),
        }
        for prompt_id, (name, prompt_class) in expected.items():
            prompt = self.full[prompt_id]
            self.assertEqual(prompt["id"], prompt_id)
            self.assertEqual(prompt["seq"], prompt_id[1:])
            self.assertEqual(prompt["copySheet"], f"{prompt_id}_COPY_SAFE")
            self.assertEqual(prompt["category"], "standard")
            self.assertEqual(prompt["profile"], "spec-architecture")
            self.assertEqual(prompt["color"], "Cyan")
            self.assertEqual(prompt["name"], name)
            self.assertEqual(prompt["class"], prompt_class)
            self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
            self.assertIn(self.policy["marker"], prompt["copyContent"])

        p91 = self.full["P91"]["copyContent"]
        self.assertIn("BUILD A FAILURE-STATE MATRIX", p91)
        self.assertIn("UNKNOWN is not PASS", p91)
        self.assertIn("Do not blanket-replace", p91)
        self.assertIn("What adjacent state could still fail for the same underlying reason?", p91)

        p92 = self.full["P92"]["copyContent"]
        self.assertIn("MAP BOTH PATHS", p92)
        self.assertIn("PRODUCTION-ONLY", p92)
        self.assertIn("Green helper tests do not prove a production wrapper", p92)
        self.assertIn("same-entrypoint synthetic proof", p92)

        p93 = self.full["P93"]["copyContent"]
        self.assertIn("BUILD THE OBLIGATION LEDGER", p93)
        self.assertIn("UNKNOWN is not PASS", p93)
        self.assertIn("FALSIFY CLOSURE", p93)
        self.assertIn("NOT CERTIFIED", p93)

        html = build_prompt_kit_registry.render()
        for _, (name, _) in expected.items():
            self.assertIn(name, html)

if __name__ == "__main__":
    unittest.main()
