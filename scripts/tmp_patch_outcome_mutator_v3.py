from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "tmp_apply_prompt_kit_outcome_tutorial_exec_context.py"
text = TARGET.read_text(encoding="utf-8")

old_donor = '''    donor_text = subprocess.check_output(
        ["git", "show", "origin/feat/p114-canary-network-20260826:registry/prompts/spec-architecture-prompts.v1.json"],
        cwd=ROOT,
        text=True,
    )
    donor = json.loads(donor_text)
    donor_p114 = next(p for p in donor["prompts"] if p.get("id") == "P114")
    if donor_p114.get("name") != "Conversation Context Canary & Handoff Guard":
        raise SystemExit("P114 donor identity mismatch")

    p114 = by_id["P114"]
    identity = {k: p114[k] for k in ("id", "seq", "name", "type", "class", "progress", "color", "copySheet", "category", "profile")}
    p114.clear()
    p114.update(donor_p114)
    p114.update(identity)
'''
new_donor = '''    # Preserve the reviewed P114 network semantics from PR #313 without trusting
    # a mutable feature-branch tip as current authority. The network patch is pinned
    # to the exact reviewed head and may be transplanted only while the current P114
    # record still exactly matches that PR's recorded base owner.
    network_base_sha = "24ca96c57a7a9c706e43f7037d98caa79fb14fce"
    network_patch_sha = "67f76da78c5ee798b5d920a9db6c7e0344d2d387"

    def p114_at(ref: str) -> dict:
        source = subprocess.check_output(
            ["git", "show", f"{ref}:registry/prompts/spec-architecture-prompts.v1.json"],
            cwd=ROOT,
            text=True,
        )
        record = next(p for p in json.loads(source)["prompts"] if p.get("id") == "P114")
        if record.get("name") != "Conversation Context Canary & Handoff Guard":
            raise SystemExit(f"P114 identity mismatch at {ref}")
        return record

    p114 = by_id["P114"]
    base_p114 = p114_at(network_base_sha)
    donor_p114 = p114_at(network_patch_sha)
    if p114 != base_p114:
        raise SystemExit(
            "P114 current owner moved since PR #313 base; refuse stale donor transplant and reconcile current authority explicitly"
        )
    expected_network_fields = {
        "sprintRole", "useWhen", "inspectFirst", "expectedOutput", "nextStep",
        "proofGate", "copyContent", "keywords",
    }
    actual_network_fields = {
        key for key in set(base_p114) | set(donor_p114)
        if base_p114.get(key) != donor_p114.get(key)
    }
    if actual_network_fields != expected_network_fields:
        raise SystemExit(
            "P114 pinned network patch changed unexpected fields: "
            + repr(sorted(actual_network_fields ^ expected_network_fields))
        )
    identity = {k: p114[k] for k in ("id", "seq", "name", "type", "class", "progress", "color", "copySheet", "category", "profile")}
    p114.clear()
    p114.update(donor_p114)
    p114.update(identity)
'''
if old_donor not in text:
    raise SystemExit("mutable P114 donor block not found")
text = text.replace(old_donor, new_donor, 1)

old_buffer = "const registry=JSON.parse(cp.execFileSync(py,['-c',\"from scripts import build_prompt_kit_registry; import json; print(json.dumps(build_prompt_kit_registry.load_prompt_kit_registry()))\"],{cwd:root,encoding:'utf8'}));"
new_buffer = "const registry=JSON.parse(cp.execFileSync(py,['-c',\"from scripts import build_prompt_kit_registry; import json; print(json.dumps(build_prompt_kit_registry.load_prompt_kit_registry()))\"],{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024}));"
if old_buffer not in text:
    raise SystemExit("Prompt Finder validator child-process buffer anchor not found")
text = text.replace(old_buffer, new_buffer, 1)

old_p92_phrase = "remote merge is never local deployment proof;"
new_p92_phrase = "remote merged SHA is never treated as local deployment proof;"
if old_p92_phrase not in text:
    raise SystemExit("P92 deployment-proof phrase anchor not found")
text = text.replace(old_p92_phrase, new_p92_phrase, 1)

old_discovery_mutation = '''    text = require_replace(text, marker, marker_new, "discovery outcome assertions")
    path.write_text(text, encoding="utf-8")
'''
new_discovery_mutation = '''    text = require_replace(text, marker, marker_new, "discovery outcome assertions")
    text = require_replace(
        text,
        "    def test_guided_questionnaire_uses_shared_search_and_no_prompt_id_router(self) -> None:\\n",
        "    def test_guided_questionnaire_uses_outcome_owner_and_shared_search_followons(self) -> None:\\n",
        "discovery outcome-owner method",
    )
    text = require_replace(
        text,
        """            "slice(0,3)",
            "copyPrompt(",
""",
        """            "slice(0,2)",
            "resolvePromptFinderOutcome",
            "promptFinderRouteIsActionable",
            "ownerId:'P79'",
            "ownerId:'P23'",
            "copyPrompt(",
""",
        "discovery retired weighted-primary assertion",
    )
    text = require_replace(
        text,
        '        self.assertIn("slice(0,3)", guided)\\n',
        '        self.assertIn("slice(0,2)", guided)\\n',
        "operator docs context-followon count",
    )
    text = require_replace(
        text,
        '        self.assertIn("search **`P83`**", guide)\\n',
        '        self.assertIn("**Verify work another agent says is complete**", guide)\\n        self.assertIn("resolves directly to **P83**", guide)\\n',
        "operator docs explicit P83 outcome",
    )
    text = require_replace(
        text,
        '        self.assertIn("Another agent claims work is complete or partially complete", tutorial)\\n',
        '        self.assertIn("Inherited-completion verification is now an explicit terminal outcome", tutorial)\\n        self.assertIn("**Verify work another agent says is complete** to route directly to P83", tutorial)\\n',
        "tutorial explicit P83 outcome",
    )
    path.write_text(text, encoding="utf-8")
'''
if old_discovery_mutation not in text:
    raise SystemExit("discovery mutation seam not found")
text = text.replace(old_discovery_mutation, new_discovery_mutation, 1)

TARGET.write_text(text, encoding="utf-8")
print("patched temporary mutator: pinned P114 authority + large-registry buffer + outcome regression reconciliation")
