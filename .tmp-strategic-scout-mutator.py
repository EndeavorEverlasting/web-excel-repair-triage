from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = Path(sys.argv[1])
receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
scout_id = receipt["id"]
scout_name = "Repository Strategic Opportunity Scout"

# Strengthen canonical P07 without changing its bounded-execution identity.
prompts_path = ROOT / "docs" / "prompts.json"
prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
p07 = next(p for p in prompts if p["id"] == "P07")
assert p07["type"] == "BUILD"
content = p07["copyContent"]
assert "STRATEGIC FOLLOW-ON — CAPTURE LEVERAGE WITHOUT EXPANDING THE SPRINT" not in content
anchor = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT"
assert content.count(anchor) == 1
section = f'''STRATEGIC FOLLOW-ON — CAPTURE LEVERAGE WITHOUT EXPANDING THE SPRINT
Bounded execution remains the primary contract. A strategic observation discovered during execution does not authorize widening owned scope, delaying required integration, replacing the current fixed-point gate, or beginning a new initiative inside this sprint.

TRIGGER — EMIT ONLY WHEN CURRENT EVIDENCE REVEALS A BROADER OPPORTUNITY
Create a STRATEGIC FOLLOW-ON only when current execution produces concrete evidence of at least one of these:
- RECURRING CONTRACT GAP — the same missing rule, validator, abstraction, workflow, proof obligation, or operator correction recurs across tasks/sprints/paths;
- CROSS-CUTTING LEVERAGE — one bounded capability could remove repeated work or unlock multiple existing systems/workflows/product surfaces;
- ARCHITECTURAL PRESSURE — ownership seams, dependency patterns, duplication, scaling limits, or coupling exceed the present fix;
- LATENT COMBINATION — existing capabilities could create materially greater value if connected by a missing contract or thin integration seam;
- NEWLY FEASIBLE CAPABILITY — completed work makes a previously premature capability realistically investigable;
- SYSTEMATIC EVIDENCE GAP — important decisions repeatedly lack telemetry, evaluation, provenance, tests, or datasets needed to judge them;
- STRATEGIC SIMPLIFICATION — deletion, consolidation, standardization, or replacement could materially reduce long-term complexity.
Do not trigger for another small task, a normal TODO, generic cleanup, an unrelated attractive feature, speculative architecture, or while the current sprint still has unfinished safe owned work. Ordinary continuation belongs in NEXT ACTION / NEXT STEPS.

EVIDENCE GATE
For every surviving candidate record:
`observation | supporting evidence | broader opportunity | why current scope must not absorb it | likely owner / next contract | cheapest discriminating investigation`
Prefer at least one direct repository/runtime/history fact plus one corroborating signal. A single authoritative contract contradiction or structural blocker may suffice when it directly proves the broader issue. Unsupported ideas are speculation, not strategic follow-ons.

DO NOT IMPLEMENT THE FOLLOW-ON HERE
A triggered strategic follow-on is a routing artifact, not additional owned work. Do not mutate unrelated files for it, create its architecture, open a second implementation initiative merely because it is attractive, weaken the current fixed-point gate, delay integration of the bounded green slice, or make the candidate an implicit requirement for current completion. Finish and integrate the current owned work first unless the discovered issue invalidates that work's safety or correctness.

CLASSIFY THE FOLLOW-ON
Classify each surviving opportunity as exactly one: EXISTING OWNER; OWNER STRENGTHENING; NEW CONTRACT CANDIDATE; INVESTIGATE FIRST; REJECT / DEFER. Do not create a new prompt identity merely because an idea sounds novel.

ROUTING
- unresolved internal program/system design -> P95;
- external systems, reusable prior art, or analogues -> P97;
- cheap measured prototype/experiment -> P82;
- Prompt Kit owner strengthening/new behavior -> P79;
- clear bounded implementation after uncertainty is resolved -> P07 or the domain-specific executor;
- repository-wide comparison of multiple long-term opportunities -> {scout_id} {scout_name}.
If an existing domain-specific owner clearly applies, route there instead of forcing a generic owner.

OUTPUT SHAPE — ONLY WHEN THE EVIDENCE GATE IS MET
STRATEGIC FOLLOW-ON
Observation: concrete pattern discovered during execution.
Evidence: repository/runtime/history facts supporting it.
Opportunity: broader capability, contract, simplification, or strategic question exposed.
Why not current scope: why pursuing it now would widen the bounded sprint.
Classification: EXISTING OWNER / OWNER STRENGTHENING / NEW CONTRACT CANDIDATE / INVESTIGATE FIRST / REJECT-DEFER.
Route: current owner or exploration contract that should receive it.
Discriminating next investigation: smallest evidence-producing investigation that would increase or decrease confidence.

CLOSEOUT RULE
STRATEGIC FOLLOW-ON is optional and evidence-triggered. If no qualifying opportunity was exposed, omit the section entirely: do not write `none`, generate hypothetical opportunities for completeness, or perform a strategic survey merely because this contract exists. If emitted, it must not replace or weaken the normal NEXT ACTION / NEXT STEPS for the bounded sprint. The sprint remains incomplete whenever safe owned execution or integration work remains, regardless of whether a strategic follow-on has been identified.

'''
p07["copyContent"] = content.replace(anchor, section + anchor, 1)
follow_on_meta = (
    f" If current execution exposes a qualifying broader opportunity, preserve it only as an evidence-triggered "
    f"STRATEGIC FOLLOW-ON routing artifact; repository-wide multi-opportunity exploration routes to {scout_id} "
    f"{scout_name}, never by widening this sprint."
)
p07["expectedOutput"] += follow_on_meta
p07["nextStep"] += (
    f" A qualifying strategic follow-on does not replace the current executable continuation or integration gate; "
    f"route broad repository opportunity comparison to {scout_id} {scout_name} after current owned work is complete."
)
p07["proofGate"] += (
    " Strategic-follow-on proof requires concrete current evidence, explicit out-of-scope routing, and omission when the evidence gate is not met; "
    "a strategic lead never authorizes unfinished owned work, delayed integration, or open-ended scope expansion."
)
prompts_path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Focused P07 regression.
p07_test_path = ROOT / "tests" / "test_p02_p07_autonomous_iteration.py"
p07_test = p07_test_path.read_text(encoding="utf-8")
p07_marker = '\n\n    def test_effective_prompts_keep_shared_actionability_policy(self) -> None:'
assert p07_marker in p07_test
method = f'''
    def test_p07_strategic_follow_on_captures_leverage_without_expanding_scope(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "BUILD")
        for phrase in (
            "STRATEGIC FOLLOW-ON — CAPTURE LEVERAGE WITHOUT EXPANDING THE SPRINT",
            "does not authorize widening owned scope",
            "RECURRING CONTRACT GAP",
            "CROSS-CUTTING LEVERAGE",
            "ARCHITECTURAL PRESSURE",
            "LATENT COMBINATION",
            "NEWLY FEASIBLE CAPABILITY",
            "SYSTEMATIC EVIDENCE GAP",
            "STRATEGIC SIMPLIFICATION",
            "observation | supporting evidence | broader opportunity | why current scope must not absorb it",
            "DO NOT IMPLEMENT THE FOLLOW-ON HERE",
            "routing artifact, not additional owned work",
            "EXISTING OWNER; OWNER STRENGTHENING; NEW CONTRACT CANDIDATE; INVESTIGATE FIRST; REJECT / DEFER",
            "unresolved internal program/system design -> P95",
            "external systems, reusable prior art, or analogues -> P97",
            "cheap measured prototype/experiment -> P82",
            "Prompt Kit owner strengthening/new behavior -> P79",
            "clear bounded implementation after uncertainty is resolved -> P07",
            "repository-wide comparison of multiple long-term opportunities -> {scout_id} {scout_name}",
            "If no qualifying opportunity was exposed, omit the section entirely",
            "must not replace or weaken the normal NEXT ACTION / NEXT STEPS",
            "The sprint remains incomplete whenever safe owned execution or integration work remains",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("Always emit a STRATEGIC FOLLOW-ON", content)
        self.assertNotIn("Implement the strategic follow-on", content)
        self.assertIn("evidence-triggered", prompt["expectedOutput"])
        self.assertIn("does not replace", prompt["nextStep"])
        self.assertIn("never authorizes unfinished owned work", prompt["proofGate"])
'''
p07_test = p07_test.replace(p07_marker, "\n" + textwrap.dedent(method).rstrip() + p07_marker, 1)
p07_test_path.write_text(p07_test, encoding="utf-8")

# Focused scout regression after helper identity allocation.
spec_test_path = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
spec_test = spec_test_path.read_text(encoding="utf-8")
spec_marker = '\n\nif __name__ == "__main__":'
assert spec_marker in spec_test
scout_method = f'''
    def test_{scout_id.lower()}_strategic_scout_falsifies_theses_and_routes_without_execution(self) -> None:
        prompt = self.full["{scout_id}"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["name"], "{scout_name}")
        self.assertEqual(prompt["type"], "ANALYZE")
        self.assertEqual(prompt["class"], "REPOSITORY STRATEGY / OPPORTUNITY DISCOVERY")
        self.assertEqual(prompt["profile"], "spec-architecture")
        for phrase in (
            "3-5 COMPETING STRATEGIC THESES",
            "FALSIFY EACH THESIS BEFORE RANKING",
            "SURVIVES",
            "WEAKENED",
            "REJECTED",
            "DEFERRED",
            "SELECT EXACTLY ONE NEXT THESIS TO INVESTIGATE",
            "CHEAPEST DISCRIMINATING INVESTIGATION",
            "P95 Program Design & Call-Stack Prototype Architect",
            "P97 Open-Source Prior-Art & Gap Analyst",
            "P82 prototyping owner",
            "P79 Prompt Registry Prompt Adder",
            "P07 Repo Sprint Executor",
            "use only when strategic uncertainty is resolved",
            "NEW CONTRACT CANDIDATE",
            "PRESERVE THE EXPLORATION / EXECUTION BOUNDARY",
            "Do not continue into bounded execution",
            "P20 executes an already-selected Opportunity_Discovery row",
            "P22/P23 rank which repository should move first across a portfolio",
        ):
            self.assertIn(phrase, content)
        self.assertLess(content.index("FALSIFY EACH THESIS BEFORE RANKING"), content.index("COMPARE SURVIVING THESES"))
        self.assertLess(content.index("COMPARE SURVIVING THESES"), content.index("SELECT EXACTLY ONE NEXT THESIS TO INVESTIGATE"))
        self.assertIn("at least 3 and no more than 5", content)
        self.assertIn("No selected initiative is implemented", prompt["expectedOutput"])
        self.assertIn("Do not implement that routed contract", prompt["nextStep"])
        self.assertIn("P07 is selected only after strategic uncertainty is resolved", prompt["proofGate"])
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        for existing in ("P03", "P20", "P22", "P23", "P79", "P82", "P95", "P97"):
            self.assertNotEqual(prompt["id"], existing)
'''
spec_test = spec_test.replace(spec_marker, "\n" + textwrap.dedent(scout_method).rstrip() + spec_marker, 1)
spec_test_path.write_text(spec_test, encoding="utf-8")

print(json.dumps({"scout_id": scout_id, "p07_strengthened": True, "tests_added": 2}, indent=2))
