from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "tmp_apply_prompt_kit_outcome_tutorial_exec_context.py"
text = TARGET.read_text(encoding="utf-8")

# P92 has advanced on main since this temporary materializer was authored. Do not
# transplant the older P92 wording over a stronger current owner. Replace the stale
# mutation block with a fail-closed verification that current P92 already carries the
# execution-context invariant this lane originally intended to add.
p92_start = '    p92 = by_id["P92"]\n'
p92_end = '    donor_text = subprocess.check_output(\n'
start = text.find(p92_start)
end = text.find(p92_end, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("P92 materializer block boundaries not found")
current_p92_block = text[start:end]
if "missing anchor: P92 execution context" not in current_p92_block and "P92 execution context" not in current_p92_block:
    raise SystemExit("P92 materializer block no longer matches the expected stale mutation lane")
verified_p92_block = '''    p92 = by_id["P92"]
    if p92["name"] != "Canonical Path Prompt":
        raise SystemExit("P92 identity mismatch")
    p92_required = (
        (p92.get("sprintRole", ""), "terminal/shell/kernel/runtime", "P92 sprintRole execution context"),
        (p92.get("inspectFirst", ""), "terminal host, actual shell/interpreter, kernel/OS/runtime boundary, execution target", "P92 inspection execution context"),
        (p92.get("expectedOutput", ""), "EXECUTION CONTEXT RECEIPT", "P92 receipt output"),
        (p92.get("proofGate", ""), "fails closed instead of guessing shell/path semantics", "P92 fail-closed proof"),
        (p92.get("copyContent", ""), "5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS", "P92 execution-context section"),
        (p92.get("copyContent", ""), "EXECUTION_CONTEXT=UNKNOWN", "P92 unknown execution context"),
        (p92.get("copyContent", ""), "A terminal application is not the shell", "P92 terminal-host distinction"),
    )
    for haystack, needle, label in p92_required:
        if needle not in haystack:
            raise SystemExit(f"current P92 no longer subsumes intended execution-context invariant: {label}")
    for keyword in ("terminal context", "shell context", "kernel context", "runtime context"):
        if keyword not in p92.get("keywords", []):
            raise SystemExit(f"current P92 missing execution-context discovery keyword: {keyword}")

'''
text = text[:start] + verified_p92_block + text[end:]

old_verify_phrase = '"EXECUTION CONTEXT RECEIPT BEFORE COMMANDS OR AGENT SELECTION"'
new_verify_phrase = '"5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS"'
if text.count(old_verify_phrase) != 2:
    raise SystemExit(
        f"expected exactly two stale P92 proof headings, found {text.count(old_verify_phrase)}"
    )
text = text.replace(old_verify_phrase, new_verify_phrase, 2)

# The old P92 regression also encoded Windows-Terminal-specific wording that current
# P92 intentionally generalized. Require the current causal invariants instead.
for old_phrase, new_phrase in (
    ("Windows Terminal can host PowerShell", "shell prompt does not prove the kernel/runtime or target"),
    ("do not emit a guessed shell-specific mutation command", "do not emit a guessed shell-specific or target-specific write command"),
):
    if text.count(old_phrase) != 1:
        raise SystemExit(f"expected exactly one stale P92 regression phrase {old_phrase!r}, found {text.count(old_phrase)}")
    text = text.replace(old_phrase, new_phrase, 1)

old_size_guard = '''    assert len(next(p for p in json.loads(REG.read_text(encoding="utf-8"))["prompts"] if p["id"] == "P92")["copyContent"]) < 9000
'''
new_size_guard = '''    raw_p92 = next(p for p in json.loads(REG.read_text(encoding="utf-8"))["prompts"] if p["id"] == "P92")
    main_registry = json.loads(subprocess.check_output(
        ["git", "show", "origin/main:registry/prompts/spec-architecture-prompts.v1.json"],
        cwd=ROOT,
        text=True,
    ))
    main_p92 = next(p for p in main_registry["prompts"] if p["id"] == "P92")
    assert raw_p92 == main_p92, "P92 must remain identical to the refreshed current-main owner"
'''
if text.count(old_size_guard) != 1:
    raise SystemExit(f"expected exactly one stale P92 size guard, found {text.count(old_size_guard)}")
text = text.replace(old_size_guard, new_size_guard, 1)

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
new_donor = '''    network_base_sha = "24ca96c57a7a9c706e43f7037d98caa79fb14fce"
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
print("patched temporary mutator: preserve current-main P92 exactly + align current P92 regressions + pin P114 authority + outcome regression reconciliation")
