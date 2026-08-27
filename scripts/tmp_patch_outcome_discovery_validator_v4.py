from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "tmp_apply_prompt_kit_outcome_tutorial_exec_context.py"
text = TARGET.read_text(encoding="utf-8")

old = '''def strengthen_automation() -> None:
    path = ROOT / "harness" / "test-floor.v1.json"
'''
new = '''def strengthen_automation() -> None:
    discovery_validator = ROOT / "scripts" / "validate_prompt_kit_discovery.py"
    validator_text = discovery_validator.read_text(encoding="utf-8")
    validator_text = require_replace(
        validator_text,
        """        "slice(0,3)",
        "promptFinderBtn",
""",
        """        "slice(0,2)",
        "resolvePromptFinderOutcome",
        "promptFinderRouteIsActionable",
        "PROMPT_FINDER_OUTCOMES",
        "ownerId:'P79'",
        "ownerId:'P23'",
        "promptFinderBtn",
""",
        "discovery validator outcome-owner markers",
    )
    discovery_validator.write_text(validator_text, encoding="utf-8")

    path = ROOT / "harness" / "test-floor.v1.json"
'''
if old not in text:
    raise SystemExit("strengthen_automation seam not found")
text = text.replace(old, new, 1)

verify_anchor = '''    pages = (ROOT / ".github" / "workflows" / "prompt-kit-pages.yml").read_text(encoding="utf-8")
    assert "Prompt Finder terminal-outcome gate" in pages
    assert "node scripts/validate_prompt_finder_outcomes.js" in pages
'''
verify_new = '''    pages = (ROOT / ".github" / "workflows" / "prompt-kit-pages.yml").read_text(encoding="utf-8")
    assert "Prompt Finder terminal-outcome gate" in pages
    assert "node scripts/validate_prompt_finder_outcomes.js" in pages
    discovery_validator = (ROOT / "scripts" / "validate_prompt_kit_discovery.py").read_text(encoding="utf-8")
    for marker in ("slice(0,2)", "resolvePromptFinderOutcome", "promptFinderRouteIsActionable", "PROMPT_FINDER_OUTCOMES", "ownerId:'P79'", "ownerId:'P23'"):
        assert marker in discovery_validator, marker
'''
if verify_anchor not in text:
    raise SystemExit("fixed-point discovery validator seam not found")
text = text.replace(verify_anchor, verify_new, 1)

TARGET.write_text(text, encoding="utf-8")
print("patched temporary mutator: discovery validator now recognizes terminal outcome ownership")
