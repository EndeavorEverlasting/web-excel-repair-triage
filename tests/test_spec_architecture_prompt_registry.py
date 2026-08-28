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
        self.assertIn("WHEN USER FLOW IS THE UNKNOWN", content)
        self.assertIn("terminal user value", content)
        self.assertIn("semantic completion events", content)
        self.assertIn("must not erase an active query", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_flow_friction_prompt_owns_terminal_actions_and_preference_telemetry(self) -> None:
        prompt = self.full["P99"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["name"], "User-Flow Friction & Preference Telemetry Refiner")
        self.assertEqual(prompt["class"], "PRODUCT / UX FLOW + TELEMETRY")
        self.assertEqual(prompt["profile"], "spec-architecture")
        for phrase in (
            "DEFINE THE TERMINAL USER VALUE",
            "PRESERVE ORTHOGONAL STATE",
            "COLLAPSE REDUNDANT INTERMEDIATE STEPS",
            "REPAIR THE DEFAULT INFORMATION ARCHITECTURE",
            "UNIFY ENTRYPOINTS ON SEMANTIC ACTIONS",
            "INSTRUMENT SEMANTIC USAGE, NOT NOISE",
            "DERIVE THE DASHBOARD FROM EVENTS",
            "active search -> unrelated filter show/hide/toggle",
            "favorite shortcut -> terminal action occurs once",
            "reuse the normal success toast/feedback",
            "Before mutating a shared telemetry/preferences owner",
            "duplicate event dispatch does not double-count one completion",
        ):
            self.assertIn(phrase, content)
        for default_view_phrase in (
            "initial viewport is consumed before primary content",
            "Persistent control density is friction",
            "progressive disclosure -> subordinate choices",
            "A Hide/Show toggle reduces clutter on demand but does not fix a noisy default information architecture",
            "preserve search, keyboard and mobile use, Favorites, and active-state semantics",
        ):
            self.assertIn(default_view_phrase, content)
        self.assertIn(
            "default-view repairs reduce measured first-viewport consumption before primary content instead of only hiding controls behind a toggle",
            prompt["proofGate"],
        )
        self.assertIn("persistent filter/control chrome", prompt["useWhen"])
        self.assertNotEqual(prompt["id"], "P82")
        self.assertNotEqual(prompt["id"], "P94")
        self.assertNotEqual(prompt["id"], "P95")
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_repository_automation_prompts_have_distinct_generation_and_promotion_roles(self) -> None:
        generation = [p for p in self.full.values() if p["name"] == "Repository-Native Code Update Harness Builder"]
        promotion = [p for p in self.full.values() if p["name"] == "Validated CI/CD Promotion Pipeline Builder"]
        self.assertEqual(len(generation), 1)
        self.assertEqual(len(promotion), 1)
        generation = generation[0]
        promotion = promotion[0]
        self.assertNotEqual(generation["id"], promotion["id"])
        self.assertEqual(generation["class"], "HARNESS / REPO-NATIVE CODE GENERATION")
        self.assertEqual(promotion["class"], "HARNESS / CI-CD PROMOTION")
        self.assertEqual(promotion["profile"], "spec-architecture")
        self.assertEqual(promotion["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], promotion["copyContent"])
        for phrase in (
            "SEPARATE AUTHORING, VALIDATION, AND PROMOTION",
            "KEEP HARNESS E2E AND APPLICATION E2E DISTINCT",
            "PIN EVERY GATE TO ONE CANDIDATE IDENTITY",
            "REQUIRED plus SKIP is not green",
            "least-privilege",
            "build-once/promote-the-same-artifact",
            "recursively trigger another writer forever",
            "PROVE POST-PROMOTION CONTAINMENT",
            "provider run ID",
        ):
            self.assertIn(phrase, promotion["copyContent"])
        self.assertLess(
            promotion["copyContent"].index("MCP / SEMANTIC REPOSITORY RETRIEVAL CONTRACT"),
            promotion["copyContent"].index("\nMISSION\n"),
        )
        for phrase in (
            "FIRST EVIDENCE ACTION",
            "Augment Context Engine MCP",
            "Resolve the active MCP server/tool identity from Cursor",
            "promotion authority, validation owners, proof/provenance, and write authority",
            "Do not satisfy this contract with one vague or ceremonial MCP call",
            "MCP maps architecture; it does not prove current SHA/base",
            "MCP_RETRIEVAL_BLOCKED",
            "Do not claim MCP-backed discovery or silently substitute assumptions",
        ):
            self.assertIn(phrase, promotion["copyContent"])
        self.assertIn("augment mcp", promotion["keywords"])
        self.assertIn("code already authored", promotion["copyContent"])
        self.assertIn("repository-owned mechanism", generation["copyContent"])
        self.assertIn("Validated CI/CD Promotion Pipeline Builder", build_prompt_kit_registry.render())

    def test_new_source_prompts_are_intentionally_bounded(self) -> None:
        for prompt_id in ("P78", "P79", "P80", "P81", "P82", "P99"):
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
        self.assertIn("User-Flow Friction & Preference Telemetry Refiner", html)

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
            "P92": ("Canonical Path Prompt", "HARNESS / CANONICAL PATH"),
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

        p92_prompt = self.full["P92"]
        p92 = p92_prompt["copyContent"]
        self.assertEqual(p92_prompt["name"], "Canonical Path Prompt")
        self.assertEqual(p92_prompt["class"], "HARNESS / CANONICAL PATH")
        for phrase in (
            "ESTABLISH AND ENFORCE THE CANONICAL DEVELOPMENT AND PRODUCTION PATH",
            "CANONICAL DEVELOPMENT CHECKOUT",
            "CANONICAL PRODUCTION / USE PATH",
            "Do not standardize a filename across repositories",
            "PREVENT PATH SPRAWL AND COMPUTER BLOAT",
            "REMOTE INTEGRATION IS NOT LOCAL DEPLOYMENT",
            "REMOTE_INTEGRATED",
            "DEV_CHECKOUT_CURRENT",
            "PROD_PATH_CURRENT",
            "ENTRYPOINT_PROVED",
            "UNKNOWN is not permission to guess",
            "MAP BOTH PATHS WHEN TEST PROOF IS INVOLVED",
            "PRODUCTION-ONLY",
            "Green helper tests do not prove a production wrapper",
            "same-entrypoint synthetic proof",
            "Could another agent entering fresh still choose a different directory?",
            "ENVIRONMENT-DERIVED MACHINE / PROFILE PATH RESOLUTION",
            "PATH INPUT RECEIPT",
            "TARGET_FOLDER_REDIRECTED",
            "An installed/running client is not proof",
            "do not assume `%USERPROFILE%\\Desktop`",
            "Ambiguous roots/redirection -> CONFLICT/UNKNOWN",
            "tracked canonical-path/profile contract -> authorized machine/profile override",
            "5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS",
            "A terminal application is not the shell",
            "EXECUTION_CONTEXT=UNKNOWN",
            "5B. DEVELOPMENT MUTATION VS ACTIVE PRODUCTION USE",
            "Production/use path is a consumer path, not the default development mutation target",
            "PROD_USE_STATE",
            "UNKNOWN is not idle",
            "same physical path",
            "Any write is production-impacting",
            "prevents partial candidate state",
        ):
            self.assertIn(phrase, p92)
        self.assertIn("remote merged SHA is never treated as local deployment proof", p92_prompt["proofGate"])
        self.assertIn("production/use path is not the default development mutation target", p92_prompt["proofGate"])
        self.assertIn("UNKNOWN production use state blocks production mutation", p92_prompt["proofGate"])
        self.assertIn("running processes, services, launchers", p92_prompt["inspectFirst"])
        self.assertIn("OneDrive/cloud roots", p92_prompt["inspectFirst"])
        self.assertIn("hard-coded username", p92_prompt["proofGate"])
        self.assertLess(len(self.raw["P92"]["copyContent"]), 12000)
        for synonym in (
            "canonical path",
            "canonical repository path",
            "canonical checkout",
            "development path",
            "production path",
            "local deployment path",
            "path drift",
            "scattered clones",
            "onedrive path",
            "onedrive repository path",
            "known folder redirection",
            "user profile path",
            "os path resolution",
        ):
            self.assertEqual(build_prompt_kit.SYNONYMS[synonym], "P92")

        p01 = self.full["P01"]["copyContent"]
        self.assertIn("CANONICAL PATH CONTRACT", p01)
        self.assertIn("Every app harness must answer where normal development occurs", p01)
        self.assertIn("Do not let a fresh agent choose a new directory from model preference", p01)
        self.assertIn("GitHub merge success alone is not workstation deployment proof", p01)
        self.assertIn("P92 Canonical Path Prompt owns deep repair/audit of this contract", p01)

        p93 = self.full["P93"]["copyContent"]
        self.assertIn("BUILD THE OBLIGATION LEDGER", p93)
        self.assertIn("UNKNOWN is not PASS", p93)
        self.assertIn("FALSIFY CLOSURE", p93)
        self.assertIn("NOT CERTIFIED", p93)
        self.assertIn("CHECK FAITHFULNESS BEFORE FETCHING MORE", p93)
        self.assertIn("FACTUALITY_MISSING_CONTEXT", p93)
        self.assertIn("FAITHFULNESS_CONTEXT_IGNORED", p93)
        self.assertIn("ATTENTION_SATURATION", p93)
        self.assertIn("A confident, plausible, good-faith answer can still fail closure", p93)
        self.assertIn("do not reflexively add more context", p93)

        html = build_prompt_kit_registry.render()
        for _, (name, _) in expected.items():
            self.assertIn(name, html)

    def test_open_source_prior_art_prompt_separates_real_world_baseline_from_local_gap(self) -> None:
        matches = [
            prompt
            for prompt in self.full.values()
            if prompt["name"] == 'Open-Source Prior-Art & Gap Analyst'
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        raw_content = self.raw[prompt["id"]]["copyContent"]
        self.assertEqual(prompt["id"], 'P97')
        self.assertEqual(prompt["seq"], '97')
        self.assertEqual(prompt["copySheet"], 'P97_COPY_SAFE')
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "RESEARCH / REFERENCE ARCHITECTURE")
        self.assertIn(
            "ANALYZE OPEN-SOURCE REPOSITORIES THAT HAVE ALREADY DONE THINGS LIKE THIS SO THAT WE CAN EMULATE THAT",
            content,
        )
        self.assertIn("WHAT IS ALREADY AVAILABLE IN THE REAL WORLD", content)
        self.assertIn("WHAT PROJECT-SPECIFIC GAP IS STILL WORTH DEVELOPING", content)
        self.assertIn("VERIFY IMPLEMENTATION, NOT MARKETING", content)
        self.assertIn("A README can orient the search but cannot by itself prove an implementation claim", content)
        for evidence_state in (
            "OBSERVED_IMPLEMENTED",
            "DOCUMENTED_UNVERIFIED",
            "INFERRED",
            "ABSENT",
        ):
            self.assertIn(evidence_state, content)
        for disposition in ("ADOPT", "ADAPT", "REJECT", "UNKNOWN"):
            self.assertIn(disposition, content)
        for gap_state in (
            "ALREADY_SOLVED_INTERNALLY",
            "AVAILABLE_TO_EMULATE_EXTERNALLY",
            "PROJECT_SPECIFIC_GAP",
            "EVIDENCE_GAP",
        ):
            self.assertIn(gap_state, content)
        self.assertIn("EMULATE MECHANISMS, NOT CODE BLINDLY", content)
        self.assertIn("verify license compatibility", content)
        self.assertIn("Search the current repo before the wider ecosystem", content)
        self.assertIn("fresh current repository", content.lower())
        self.assertIn("refresh the evidence", content.lower())
        self.assertIn("ADVANCE, DON'T END WITH A RESEARCH ESSAY", content)
        self.assertIn("not portfolio ranking", content.lower())
        self.assertIn("do not primarily rank which of our internal repositories", content.lower())
        self.assertIn("do not replace the repository's internal intent routing", content.lower())
        self.assertGreater(len(raw_content), 4500)
        self.assertLess(len(raw_content), 9000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn('Open-Source Prior-Art & Gap Analyst', html)


    def test_p90_command_snippets_preserve_operator_terminal_observability(self) -> None:
        prompt = self.full["P90"]
        content = prompt["copyContent"]
        raw_content = self.raw["P90"]["copyContent"]
        self.assertEqual(prompt["name"], "Lua Flagging + Host Enforcement Repair Loop")
        self.assertEqual(prompt["class"], "HARNESS / LUA HOST ENFORCEMENT")
        self.assertEqual(prompt["profile"], "spec-architecture")
        for phrase in (
            "ARCHITECTURE BOUNDARY — HOST STAYS IN CONTROL",
            "COMMAND CLASSES TO EXERCISE",
            "wrong-shell syntax",
            "HOST ENFORCEMENT",
            "SCAN -> LUA FLAGS -> HOST BLOCK/RAISE -> AGENT REPAIR -> REVALIDATE",
            "CHECKER_FAILURE",
        ):
            self.assertIn(phrase, content)
        for phrase in (
            "OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT",
            "INTERACTIVE_PASTE",
            "TRANSIENT_CONSOLE",
            "CHILD_PROCESS",
            "AUTOMATION_CI",
            "no top-level `exit`",
            "preserve status and keep the parent shell alive",
            "save exit code first",
            "never wait for human input",
            "Waits are inspection aids, not error handling",
        ):
            self.assertIn(phrase, content)
        self.assertIn("terminal", prompt["useWhen"].lower())
        self.assertIn("invocation mode", prompt["inspectFirst"].lower())
        self.assertIn("unattended", prompt["proofGate"].lower())
        self.assertIn("terminal stays open", prompt["keywords"])
        self.assertIn("preserve exit code", prompt["keywords"])
        self.assertGreater(len(raw_content), 5000)
        self.assertLess(len(raw_content), 8000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn("Lua Flagging + Host Enforcement Repair Loop", html)

    def test_p86_supports_bounded_multi_prompt_principle_campaign(self) -> None:
        prompt = self.full["P86"]
        raw = self.raw["P86"]
        content = raw["copyContent"]
        for phrase in (
            "HARDEN ONE OR MORE EXISTING PROMPTS",
            "SINGLE TARGET hardening or a bounded PRINCIPLE PROPAGATION CAMPAIGN",
            "do not stop at the first obvious prompt",
            "NORMALIZE THE SOURCE PRINCIPLE",
            "Distinguish principle from costume",
            "role/competence anchoring",
            "explicit source map",
            "observable definition of done",
            "final self-check against evidence",
            "literal domain wording, invented tenure, emotional urgency",
            "Every material candidate must receive a disposition",
            "CHOOSE THE CANONICAL OWNER",
            "A campaign succeeds by correct coverage, not by number of edited prompts",
        ):
            self.assertIn(phrase, content)
        self.assertIn("one existing Prompt Kit prompt or a bounded family", raw["sprintRole"])
        self.assertIn("every relevant existing prompt", raw["useWhen"])
        self.assertIn("candidate target set", raw["inspectFirst"])
        self.assertIn("targets changed", content)
        self.assertLess(len(content), 7600)
        self.assertEqual(prompt["id"], "P86")
        self.assertEqual(prompt["copySheet"], "P86_COPY_SAFE")
    def test_afk_feedback_executor_connects_real_work_to_existing_owners(self) -> None:
        matches = [p for p in self.full.values() if p.get("name") == 'AFK Feedback-Driven Development Loop Executor']
        self.assertEqual(len(matches), 1)
        owner = matches[0]
        self.assertEqual(owner["id"], 'P115')
        self.assertEqual(owner["class"], "HARNESS / AFK DEVELOPMENT")
        content = owner["copyContent"]
        for phrase in (
            "FEEDBACK IS A WORK QUEUE, NOT A REPORT ENDPOINT",
            "P07-STYLE NONTERMINAL WORK LOOP",
            "REFRESH -> INGEST SIGNALS -> SELECT SAFE HIGHEST-VALUE WORK -> EXECUTE -> VALIDATE -> INGEST NEW FEEDBACK -> CRITIQUE -> IMPROVE -> INTEGRATE -> REFRESH -> REPEAT",
            "A status-only pass is a failed pass when safe agent-capable work exists",
            "developers, scripts, agents, models, PRs",
            "AFK WAKEUPS ARE NOT AFK WORK",
            "COERCE REAL WORK, NOT STATUS THEATER",
            "one writer per mutation surface",
            "Prove the operator did not have to relay ordinary logs",
            "An open PR, green CI, generated report",
        ):
            self.assertIn(phrase, content)
        for neighbor in ("P07", "P32", "P104", "P105", "P112", "P113"):
            self.assertIn(neighbor, content)
        self.assertEqual(self.full["P104"]["class"], "HARNESS / REPO-NATIVE CODE GENERATION")
        self.assertEqual(self.full["P105"]["class"], "HARNESS / CI-CD PROMOTION")
        self.assertEqual(self.full["P112"]["class"], "HARNESS / AUTOMATED TESTING")
        self.assertEqual(self.full["P113"]["class"], "HARNESS / TEST EVOLUTION")

    def test_p105_failed_gate_routes_to_afk_repair_without_gaining_authoring(self) -> None:
        owner = [p for p in self.full.values() if p.get("name") == 'AFK Feedback-Driven Development Loop Executor'][0]
        promotion = self.full["P105"]
        self.assertIn(owner["id"], promotion["nextStep"])
        self.assertIn(owner["id"], promotion["copyContent"])
        self.assertIn("FAILED PROMOTION GATES FEED DEVELOPMENT", promotion["copyContent"])
        content = promotion["copyContent"]
        self.assertIn("This pipeline remains promotion-only", content)
        self.assertIn("Emit candidate SHA/base, failing job/check/command", content)
        self.assertIn("artifact/log or review-thread identity", content)
        self.assertIn("owning surface, required acceptance condition, and proof ceiling", content)
        self.assertIn("hand that exact signal to P115", content)
        self.assertIn("keep promotion blocked", content)
        self.assertIn("The repair owner must create a new exact candidate", content)
        self.assertIn("re-enter this P105 pipeline from the beginning", content)
        self.assertIn("never reuse proof from the failed candidate", content)

    def test_p113_evolution_covers_crlf_second_sink_and_built_output_release_check(self) -> None:
        prompt = self.full["P113"]
        raw = self.raw["P113"]
        content = prompt["copyContent"]
        raw_content = raw["copyContent"]
        self.assertEqual(prompt["id"], "P113")
        self.assertEqual(prompt["class"], "HARNESS / TEST EVOLUTION")
        for phrase in (
            "CRLF-normalized mutation fixtures",
            "second-sink",
            "built-output",
            "release:check",
            "mutation fixture",
            "Normalize line endings in fixtures",
            "CRLF vs LF",
        ):
            self.assertIn(phrase, content)
            self.assertIn(phrase, raw_content)
        for kw in ("CRLF-normalized", "second-sink", "built-output", "release:check"):
            self.assertIn(kw, prompt["keywords"])
            self.assertIn(kw, raw["keywords"])
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_p122_web_contact_form_semantic_validation_and_mutation_release_guard(self) -> None:
        prompt = self.full["P122"]
        raw = self.raw["P122"]
        content = prompt["copyContent"]
        raw_content = raw["copyContent"]
        self.assertEqual(prompt["seq"], "122")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "WEB / FORM SECURITY & VALIDATION")
        self.assertEqual(prompt["name"], "Web Contact Form Semantic Validation & Mutation-Hardened Release Guard")
        self.assertEqual(raw["id"], "P122")
        for phrase in (
            "form=\"contact-form\"",
            "SEMANTIC FORM-CONTROL ASSOCIATION",
            "UNNAMED AND EXTERNAL NATIVE-SUBMIT REJECTION",
            "required-attribute",
            "COMPUTED AND ALIASED REQUEST ACCESS",
            "ALL-CONSOLE DENIAL",
            "SEMANTIC RESEND PAYLOAD",
            "SECOND-SINK",
            "CRLF-NORMALIZED MUTATION FIXTURES",
            "CRLF",
            "HTML-AWARE TAG BOUNDARIES",
            "COMMENT-SAFE",
            "TEMPLATE-INTERPOLATION",
            "TURNSTILE",
            "passive Turnstile-resource",
            "release:check",
            "built-output",
        ):
            self.assertIn(phrase, content)
            self.assertIn(phrase, raw_content)
        for kw in ("contact form", "Resend payload", "second-sink", "CRLF-normalized", "mutation fixture", "release:check"):
            self.assertIn(kw, prompt["keywords"])
        self.assertIn("HARDEN THE WEB CONTACT FORM", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn("P122", html)
        self.assertIn("Web Contact Form Semantic Validation", html)
        self.assertIn("contact-form", html)

if __name__ == "__main__":
    unittest.main()
