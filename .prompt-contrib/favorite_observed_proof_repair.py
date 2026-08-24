from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} anchor(s), found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


# Product behavior: Favorite shortcuts reveal the card and copy canonical content.
polish = "docs/prompt-kit-polish.js"
old_fn = """function openPromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!isFavoritePrompt(promptId)){showToast(promptId+' is no longer a Favorite');return false}
  showPromptDetail(promptId,null);
  return true
}
"""
new_fn = """function revealPromptShortcutTarget(promptId){
  activeCat='all';
  activeSection=null;
  clearTransientPromptFilters();
  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.dataset.cat==='all')});
  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__all__')});
  renderTypes();
  render();
  var selector='[data-prompt-id=\"'+String(promptId||'').replace(/\"/g,'')+'\"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  try{card.scrollIntoView({behavior:hotkeyScrollBehavior(),block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}

function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!isFavoritePrompt(promptId)){showToast(promptId+' is no longer a Favorite');return false}
  if(!revealPromptShortcutTarget(promptId)){showToast(promptId+' could not be revealed');return false}
  copyPrompt(promptId);
  return true
}
"""
replace_exact(polish, old_fn, new_fn)
replace_exact(polish, "openPromptShortcutTarget(exact);return true", "activatePromptShortcutTarget(exact);return true", expected=2)
replace_exact(
    polish,
    "var label=document.createElement('span');label.textContent='Open '+promptId;",
    "var label=document.createElement('span');label.textContent='Copy + reveal '+promptId;",
)

# Keep executable seam faithful to the intended product behavior.
proto = "docs/prompt-kit-hotkey-prototype.js"
prototype_replacements = [
    ("if (binding.command !== 'OPEN_PROMPT') throw new HotkeyError('UNKNOWN_COMMAND', binding.command);", "if (binding.command !== 'COPY_REVEAL_PROMPT') throw new HotkeyError('UNKNOWN_COMMAND', binding.command);"),
    ("else if (binding.command === 'OPEN_PROMPT') result = this.promptNavigator.openPrompt(binding.promptId);", "else if (binding.command === 'COPY_REVEAL_PROMPT') result = this.promptNavigator.copyAndReveal(binding.promptId);"),
    (
        "class PromptNavigatorFake {\n  constructor(trace) { this.trace = trace; this.opened = []; }\n  openPrompt(promptId) {\n    this.opened.push(promptId);\n    this.trace.push({layer: 'navigator', event: 'prompt_opened', promptId});\n    return {promptId};\n  }\n}",
        "class PromptNavigatorFake {\n  constructor(trace) { this.trace = trace; this.copied = []; this.revealed = []; this.detailOpened = false; }\n  copyAndReveal(promptId) {\n    this.copied.push(promptId);\n    this.revealed.push(promptId);\n    this.trace.push({layer: 'navigator', event: 'prompt_copied_and_revealed', promptId});\n    return {promptId, copied: true, revealed: true, detailOpened: false};\n  }\n}",
    ),
    ("program.registry.configure({gesture: 'p95', command: 'OPEN_PROMPT', promptId: 'p95'});", "program.registry.configure({gesture: 'p95', command: 'COPY_REVEAL_PROMPT', promptId: 'p95'});"),
    ("assert(program.promptNavigator.opened[0] === 'P95', 'P95 target');", "assert(program.promptNavigator.copied[0] === 'P95', 'P95 copied automatically');\n  assert(program.promptNavigator.revealed[0] === 'P95', 'P95 revealed');\n  assert(program.promptNavigator.detailOpened === false, 'P95 must not open detail');"),
    ("program.registry.configure({gesture: 'p14', command: 'OPEN_PROMPT', promptId: 'p14'});", "program.registry.configure({gesture: 'p14', command: 'COPY_REVEAL_PROMPT', promptId: 'p14'});"),
    ("assert(program.promptNavigator.opened[1] === 'P14', 'P14 target');", "assert(program.promptNavigator.copied[1] === 'P14', 'P14 copied');\n  assert(program.promptNavigator.revealed[1] === 'P14', 'P14 revealed');"),
    ("command: 'OPEN_PROMPT', promptId: 'P95'", "command: 'COPY_REVEAL_PROMPT', promptId: 'P95'"),
    ("command: 'OPEN_PROMPT', promptId: 'P999'", "command: 'COPY_REVEAL_PROMPT', promptId: 'P999'"),
    ("success_paths: ['HOTKEY_HELP_TOGGLE', 'FILTER_HIDE', 'FILTER_SHOW', 'FILTER_TOGGLE', 'OPEN_PROMPT(P95)', 'OPEN_PROMPT(P14)', 'VIEW_DOCTRINE']", "success_paths: ['HOTKEY_HELP_TOGGLE', 'FILTER_HIDE', 'FILTER_SHOW', 'FILTER_TOGGLE', 'COPY_REVEAL_PROMPT(P95)', 'COPY_REVEAL_PROMPT(P14)', 'VIEW_DOCTRINE']"),
]
for old, new in prototype_replacements:
    count = (ROOT / proto).read_text(encoding="utf-8").count(old)
    if count == 0:
        raise SystemExit(f"{proto}: missing prototype anchor {old[:100]!r}")
    replace_exact(proto, old, new, expected=count)

hotkey_test = "tests/test_prompt_kit_hotkey_completion.py"
replace_exact(
    hotkey_test,
    '"showPromptDetail(promptId,null)",',
    '"function activatePromptShortcutTarget(promptId)",\n            "revealPromptShortcutTarget(promptId)",\n            "renderTypes();",\n            "copyPrompt(promptId)",',
)
replace_exact(
    hotkey_test,
    '"OPEN_PROMPT(P95)",\n            "OPEN_PROMPT(P14)",',
    '"COPY_REVEAL_PROMPT(P95)",\n            "COPY_REVEAL_PROMPT(P14)",',
)
replace_exact(
    hotkey_test,
    'self.assertTrue(any(item.get("promptId") == "P14" for item in proof["trace"]))',
    'self.assertTrue(any(item.get("promptId") == "P14" for item in proof["trace"]))\n        self.assertTrue(any(item.get("event") == "prompt_copied_and_revealed" for item in proof["trace"]))',
)
replace_exact(
    hotkey_test,
    'self.assertIn("opens canonical prompt detail immediately", design)',
    'self.assertIn("copies the canonical prompt and scrolls its card into view without opening prompt detail", design)',
)
replace_exact(
    "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md",
    "opens canonical prompt detail immediately",
    "copies the canonical prompt and scrolls its card into view without opening prompt detail",
)

# Fail-closed observed-outcome harness.
observed_dir = ROOT / "harness/observed-proof"
observed_dir.mkdir(parents=True, exist_ok=True)
(observed_dir / "CONTRACT.md").write_text(
    """# Observed Behavior Proof Contract

Runtime behavior is UNKNOWN until the required event sequence has actually occurred in an evidence-producing runtime.

## Claim law

- Source inspection, a diff, a static validator, a build, a unit test, a mock, or a synthetic model may prove only its own layer. None may be promoted to browser/runtime observation.
- A behavior claim may be `PASS` only when every observation required by that claim is present in a receipt, has `occurred: true`, and has `passed: true`.
- Evidence tiers are ordered. Browser observation cannot satisfy a target-runtime or production requirement; stronger tiers may satisfy weaker requirements.
- Missing artifacts, stale subjects, skipped events, or weaker evidence yield `UNKNOWN`/`UNPROVEN`, never an inferred pass.
- Every receipt pins the exact commit, artifact path/hash, environment, scenario, claims, and observations.
- If the commit, generated artifact, relevant dependency, or scenario changes, the prior receipt is stale for the changed claim.
- CI/browser proof is representative runtime proof, not operator workstation or production proof. Raise the proof ceiling only when that stronger target was actually observed.

## UI interaction minimum

A UI claim must observe the user-visible sequence that matters, including side effects and focus/keyboard state when they are part of the bug. For clipboard/navigation behavior, prove the exact clipboard payload, the intended target visibility/scroll result, and the absence of the destructive or contradictory focus/modal outcome.

## Completion guard

Agents and reports must not say `works`, `fixed`, `passes`, `successful`, or equivalent for a runtime claim unless a current receipt supports that claim at the required evidence class. Otherwise report the claim as `UNKNOWN` or `UNPROVEN` and name the missing observation.
""",
    encoding="utf-8",
    newline="\n",
)
(observed_dir / "manifest.v1.json").write_text(
    json.dumps(
        {
            "schema_version": "observed-behavior-proof-harness/v1",
            "contract": "harness/observed-proof/CONTRACT.md",
            "validator": "scripts/validate_observed_behavior_receipt.py",
            "contract_tests": "tests/test_observed_behavior_proof_harness.py",
            "browser_proof": "tests/prompt_kit_favorite_browser_proof.py",
            "ci": ".github/workflows/prompt-kit-observed-browser-proof.yml",
            "receipt_schema": "observed-behavior-proof/v1",
            "pass_requires_observed_events": True,
            "missing_artifact_fails_closed": True,
            "evidence_tiers_are_ordered": True,
            "stale_on_subject_or_artifact_change": True,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
    newline="\n",
)
(observed_dir / "validators.v1.json").write_text(
    json.dumps(
        {
            "schema_version": "observed-behavior-proof-validators/v1",
            "validators": [
                {
                    "id": "observed-behavior-receipt",
                    "command": "python scripts/validate_observed_behavior_receipt.py <receipt> --summary",
                    "fails_closed": True,
                    "purpose": "Reject PASS claims without current artifacts, sufficient evidence tier, and observations that actually occurred and passed.",
                }
            ],
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
    newline="\n",
)

validator = r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_RANK = {
    "source": 0,
    "build": 1,
    "synthetic": 1,
    "browser_runtime_observed": 2,
    "target_runtime_observed": 3,
    "production_observed": 4,
}


def validate(receipt: dict, expected_sha: str | None = None) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "observed-behavior-proof/v1":
        errors.append("unsupported schema_version")
    subject = receipt.get("subject") or {}
    sha = str(subject.get("commit_sha") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        errors.append("subject.commit_sha must be an exact 40-character SHA")
    if expected_sha and sha != expected_sha:
        errors.append(f"receipt SHA {sha} does not match expected {expected_sha}")
    artifact = subject.get("artifact") or {}
    rel = artifact.get("path")
    digest = str(artifact.get("sha256") or "")
    if not rel or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("subject.artifact path and sha256 are required")
    else:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"artifact does not exist: {rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append("artifact hash does not match current file")
    evidence_class = receipt.get("evidence_class")
    if evidence_class not in EVIDENCE_RANK:
        errors.append("unknown evidence_class")
    observations = {
        item.get("id"): item
        for item in receipt.get("observations", [])
        if isinstance(item, dict) and item.get("id")
    }
    claims = receipt.get("claims", [])
    if not claims:
        errors.append("receipt must contain claims")
    for claim in claims:
        cid = claim.get("id", "<missing>")
        status = claim.get("status")
        required = claim.get("required_evidence_class")
        refs = claim.get("observation_ids") or []
        if status == "PASS":
            if required not in EVIDENCE_RANK:
                errors.append(f"{cid}: unknown required_evidence_class {required}")
            elif evidence_class in EVIDENCE_RANK and EVIDENCE_RANK[evidence_class] < EVIDENCE_RANK[required]:
                errors.append(f"{cid}: PASS requires {required}, got weaker {evidence_class}")
            if not refs:
                errors.append(f"{cid}: PASS has no observation_ids")
            for ref in refs:
                observation = observations.get(ref)
                if not observation:
                    errors.append(f"{cid}: missing observation {ref}")
                    continue
                if observation.get("occurred") is not True:
                    errors.append(f"{cid}: observation {ref} did not occur")
                if observation.get("passed") is not True:
                    errors.append(f"{cid}: observation {ref} did not pass")
        elif status not in {"UNKNOWN", "UNPROVEN", "FAIL"}:
            errors.append(f"{cid}: invalid status {status}")
    if receipt.get("verdict") == "PASS" and any(c.get("status") != "PASS" for c in claims):
        errors.append("overall PASS requires every claim to PASS")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt")
    parser.add_argument("--expected-sha")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    errors = validate(receipt, args.expected_sha)
    if errors:
        print("Observed behavior proof: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Observed behavior proof: PASS" if args.summary else json.dumps({"verdict": "PASS", "receipt": args.receipt}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
(ROOT / "scripts/validate_observed_behavior_receipt.py").write_text(validator, encoding="utf-8", newline="\n")

harness_test = r'''from __future__ import annotations
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("observed_proof_validator", ROOT / "scripts/validate_observed_behavior_receipt.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class ObservedBehaviorProofHarnessTests(unittest.TestCase):
    def base_receipt(self):
        artifact = ROOT / "web/prompt-kit/index.html"
        return {
            "schema_version": "observed-behavior-proof/v1",
            "verdict": "PASS",
            "evidence_class": "browser_runtime_observed",
            "subject": {
                "commit_sha": "1" * 40,
                "artifact": {
                    "path": "web/prompt-kit/index.html",
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                },
            },
            "claims": [
                {
                    "id": "ui",
                    "status": "PASS",
                    "required_evidence_class": "browser_runtime_observed",
                    "observation_ids": ["event"],
                }
            ],
            "observations": [{"id": "event", "occurred": True, "passed": True}],
        }

    def test_observed_pass_is_accepted(self):
        self.assertEqual(MOD.validate(self.base_receipt()), [])

    def test_pass_without_occurrence_fails_closed(self):
        receipt = self.base_receipt()
        receipt["observations"][0]["occurred"] = False
        self.assertTrue(any("did not occur" in e for e in MOD.validate(receipt)))

    def test_static_or_synthetic_evidence_cannot_be_promoted_to_runtime_pass(self):
        for evidence_class in ("source", "build", "synthetic"):
            receipt = self.base_receipt()
            receipt["evidence_class"] = evidence_class
            self.assertTrue(any("weaker" in e for e in MOD.validate(receipt)))

    def test_lower_observed_tier_cannot_satisfy_higher_required_tier(self):
        receipt = self.base_receipt()
        receipt["claims"][0]["required_evidence_class"] = "production_observed"
        self.assertTrue(any("requires production_observed" in e for e in MOD.validate(receipt)))

    def test_missing_artifact_is_rejected(self):
        receipt = self.base_receipt()
        receipt["subject"]["artifact"]["path"] = "does/not/exist.html"
        receipt["subject"]["artifact"]["sha256"] = "a" * 64
        self.assertTrue(any("artifact does not exist" in e for e in MOD.validate(receipt)))

    def test_prompt_owners_require_observed_outcome_gate(self):
        registry = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))
        diagnostic = next(p for p in registry["prompts"] if p["name"] == "Factuality vs Faithfulness Hallucination Diagnoser")
        for phrase in ("OBSERVED-OUTCOME CLAIM GATE", "UNKNOWN/UNPROVEN", "actual interaction", "clipboard"):
            self.assertIn(phrase, diagnostic["copyContent"])
        base = json.loads((ROOT / "docs/prompts.json").read_text(encoding="utf-8"))
        p08 = next(p for p in base if p["id"] == "P08")
        for phrase in ("OBSERVED OUTCOME BEFORE PASS", "runtime claim is UNKNOWN", "exact interaction sequence"):
            self.assertIn(phrase, p08["copyContent"])


if __name__ == "__main__":
    unittest.main()
'''
(ROOT / "tests/test_observed_behavior_proof_harness.py").write_text(harness_test, encoding="utf-8", newline="\n")

browser_proof = r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "web/prompt-kit/index.html"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def observe(port: int, screenshot: Path):
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations = []
    expected = ""
    actual = ""
    after_enter = ""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                reduced_motion="reduce",
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
            expected = page.evaluate("PROMPTS.find(p => p.id === 'P79').copyContent")

            # Configure the Favorite through the actual product UI, not closure internals.
            card = page.locator('[data-prompt-id="P79"]')
            card.locator('.prompt-favorite-btn').click()
            page.locator('#hotkeyHelpToggle').click()
            page.locator('#promptShortcutPromptId').fill('P79')
            page.get_by_role('button', name='Save favorite prompt keyboard shortcut').click()
            page.wait_for_timeout(100)
            setup_saved = 'Shortcut p79 saved' in page.locator('#toast').inner_text()
            page.locator('.hotkey-help-close').click()

            # Enter another scope so the shortcut must restore navigation and reveal P79.
            page.locator('.cat-tab[data-cat="doctrine"]').click()
            page.wait_for_timeout(100)
            before_present = page.locator('[data-prompt-id="P79"]').count() > 0
            page.evaluate("document.activeElement && document.activeElement.blur()")

            page.keyboard.press('p')
            page.keyboard.press('7')
            page.keyboard.press('9')
            page.wait_for_timeout(250)
            toast_text = page.locator('#toast').inner_text()
            shortcut_copied = 'Copied' in toast_text
            try:
                actual = page.evaluate('navigator.clipboard.readText()')
                clipboard_read = True
            except Exception:
                actual = ''
                clipboard_read = False

            target = page.locator('[data-prompt-id="P79"]')
            target_present = target.count() > 0
            visible = False
            if target_present:
                visible = page.evaluate("""() => {
                  const r=document.querySelector('[data-prompt-id="P79"]').getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }""")
            modal_closed = page.evaluate("""() => {
              const o=document.getElementById('promptDetailOverlay');
              return !o || !o.classList.contains('open');
            }""")
            close_focused = page.evaluate("""() => !!(
              document.activeElement &&
              (document.activeElement.classList.contains('pd-close') || document.activeElement.id==='promptDetailClose')
            )""")

            page.keyboard.press('Enter')
            page.wait_for_timeout(100)
            enter_modal_closed = page.evaluate("""() => {
              const o=document.getElementById('promptDetailOverlay');
              return !o || !o.classList.contains('open');
            }""")
            try:
                after_enter = page.evaluate('navigator.clipboard.readText()')
            except Exception:
                after_enter = ''

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)
            observations = [
                {"id": "favorite_setup_saved", "event": "P79 favorited and p79 shortcut saved through product UI", "occurred": True, "passed": bool(setup_saved)},
                {"id": "alternate_scope_precondition", "event": "P79 absent from Doctrine scope before shortcut", "occurred": True, "passed": not before_present, "present_before": bool(before_present)},
                {"id": "favorite_shortcut_dispatched", "event": "typed favorite shortcut p79", "occurred": True, "passed": bool(shortcut_copied), "toast": toast_text},
                {"id": "prompt_card_scrolled_visible", "event": "P79 card exists and intersects viewport after shortcut", "occurred": True, "passed": bool(target_present and visible), "present": bool(target_present), "visible": bool(visible)},
                {"id": "clipboard_exact_match", "event": "clipboard equals canonical P79 copyContent", "occurred": bool(clipboard_read), "passed": bool(clipboard_read and actual == expected), "actual_length": len(actual), "expected_length": len(expected)},
                {"id": "detail_modal_closed", "event": "favorite shortcut does not open detail modal or focus its close control", "occurred": True, "passed": bool(modal_closed and not close_focused), "modal_closed": bool(modal_closed), "close_focused": bool(close_focused)},
                {"id": "enter_does_not_close_prompt", "event": "Enter after shortcut leaves detail modal closed and clipboard intact", "occurred": True, "passed": bool(enter_modal_closed and after_enter == expected)},
            ]
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--screenshot', required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    screenshot = Path(args.screenshot)
    observations = observe(args.port, screenshot)
    by_id = {item['id']: item for item in observations}
    auto_copy = all(by_id[item]['passed'] for item in ('favorite_setup_saved', 'favorite_shortcut_dispatched', 'clipboard_exact_match'))
    reveal = all(by_id[item]['passed'] for item in ('alternate_scope_precondition', 'favorite_shortcut_dispatched', 'prompt_card_scrolled_visible'))
    focus_safe = all(by_id[item]['passed'] for item in ('detail_modal_closed', 'enter_does_not_close_prompt'))
    verdict = 'PASS' if all(item['passed'] for item in observations) else 'FAIL'
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": {
            "commit_sha": sha,
            "artifact": {
                "path": "web/prompt-kit/index.html",
                "sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            },
        },
        "environment": {"kind": "github_actions_headless_browser", "engine": "chromium", "scenario": "favorite-shortcut-copy-reveal-focus"},
        "claims": [
            {"id": "favorite_auto_copy", "statement": "Typing configured Favorite P79 automatically copies canonical prompt content", "status": "PASS" if auto_copy else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["favorite_setup_saved", "favorite_shortcut_dispatched", "clipboard_exact_match"]},
            {"id": "favorite_scroll", "statement": "Typing configured Favorite P79 exits an alternate scope and scrolls the P79 card into view", "status": "PASS" if reveal else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["alternate_scope_precondition", "favorite_shortcut_dispatched", "prompt_card_scrolled_visible"]},
            {"id": "non_destructive_focus", "statement": "Shortcut does not open detail with close focused; Enter cannot immediately close the prompt", "status": "PASS" if focus_safe else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["detail_modal_closed", "enter_does_not_close_prompt"]},
        ],
        "observations": observations,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({"verdict": verdict, "receipt": str(receipt_path), "screenshot": str(screenshot), "observations": observations}))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
'''
(ROOT / "tests/prompt_kit_favorite_browser_proof.py").write_text(browser_proof, encoding="utf-8", newline="\n")

permanent_workflow = """name: Prompt Kit observed browser proof

on:
  pull_request:
    paths:
      - docs/prompt-kit-polish.js
      - docs/prompt-kit-hotkey-prototype.js
      - docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md
      - docs/prompts.json
      - registry/prompts/ai-engineering-level-up-prompts.v1.json
      - harness/observed-proof/**
      - scripts/validate_observed_behavior_receipt.py
      - tests/prompt_kit_favorite_browser_proof.py
      - tests/test_observed_behavior_proof_harness.py
      - tests/test_prompt_kit_hotkey_completion.py
      - web/prompt-kit/index.html
      - .github/workflows/prompt-kit-observed-browser-proof.yml
  push:
    branches: [main]
    paths:
      - docs/prompt-kit-polish.js
      - docs/prompt-kit-hotkey-prototype.js
      - docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md
      - docs/prompts.json
      - registry/prompts/ai-engineering-level-up-prompts.v1.json
      - harness/observed-proof/**
      - scripts/validate_observed_behavior_receipt.py
      - tests/prompt_kit_favorite_browser_proof.py
      - tests/test_observed_behavior_proof_harness.py
      - tests/test_prompt_kit_hotkey_completion.py
      - web/prompt-kit/index.html
      - .github/workflows/prompt-kit-observed-browser-proof.yml

permissions:
  contents: read

jobs:
  observed-browser-proof:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Validate harness and deterministic contracts
        run: |
          python -m unittest tests.test_observed_behavior_proof_harness tests.test_prompt_kit_hotkey_completion tests.test_ai_engineering_level_up -v
          node --check docs/prompt-kit-polish.js
          node --check docs/prompt-kit-hotkey-prototype.js
          python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
      - name: Install browser proof runtime
        run: |
          python -m pip install --disable-pip-version-check playwright==1.55.0
          python -m playwright install --with-deps chromium
      - name: Observe Favorite copy scroll and Enter behavior
        run: |
          mkdir -p Outputs/observed-proof
          python tests/prompt_kit_favorite_browser_proof.py --receipt Outputs/observed-proof/favorite-shortcut-receipt.json --screenshot Outputs/observed-proof/favorite-shortcut.png
          python scripts/validate_observed_behavior_receipt.py Outputs/observed-proof/favorite-shortcut-receipt.json --expected-sha "$(git rev-parse HEAD)" --summary
      - name: Upload observed proof receipt
        uses: actions/upload-artifact@v4
        with:
          name: prompt-kit-favorite-observed-proof
          path: Outputs/observed-proof/
          if-no-files-found: error
"""
(ROOT / ".github/workflows/prompt-kit-observed-browser-proof.yml").write_text(permanent_workflow, encoding="utf-8", newline="\n")

# Harden the faithfulness diagnoser.
registry_path = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
registry = json.loads(registry_path.read_text(encoding="utf-8"))
diagnostic = next(p for p in registry["prompts"] if p["name"] == "Factuality vs Faithfulness Hallucination Diagnoser")
if "OBSERVED-OUTCOME CLAIM GATE" not in diagnostic["copyContent"]:
    diagnostic["copyContent"] = diagnostic["copyContent"].rstrip() + """

OBSERVED-OUTCOME CLAIM GATE
- Separate implementation evidence from outcome evidence. A diff, build, static validator, unit test, mock, synthetic trace, or PR state proves only that layer; it does not prove a browser/runtime outcome occurred.
- Before saying a behavior works, is fixed, or passes, execute the actual interaction at the required proof layer and bind the claim to an exact-head receipt. For UI behavior, observe the input sequence, intended navigation/scroll target, exact side effect such as clipboard content, and relevant focus/keyboard/modal state.
- If the required outcome was not actually observed, classify the claim UNKNOWN/UNPROVEN rather than inferring success from plausible code. Treat a completion claim unsupported by available evidence as a faithfulness failure: the evidence is present, but the conclusion does not follow from it.
- When a counterexample exists, such as a screenshot showing destructive focus, preserve it as higher-priority failure evidence until a current observed run falsifies that counterexample.
"""
clause = "Runtime/UI PASS claims require an exact-head observed-outcome receipt; absent observation remains UNKNOWN/UNPROVEN."
if clause not in diagnostic.get("proofGate", ""):
    diagnostic["proofGate"] = diagnostic.get("proofGate", "").rstrip() + " " + clause
registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

# Harden P08, the existing runtime-proof owner.
base_path = ROOT / "docs/prompts.json"
base = json.loads(base_path.read_text(encoding="utf-8"))
p08 = next(p for p in base if p["id"] == "P08")
if "OBSERVED OUTCOME BEFORE PASS" not in p08["copyContent"]:
    p08["copyContent"] = p08["copyContent"].rstrip() + """

OBSERVED OUTCOME BEFORE PASS
- A runtime claim is UNKNOWN until the exact interaction sequence and required side effect have actually occurred in the selected runtime and are captured in current evidence.
- Static source checks, builds, unit tests, mocks, synthetic traces, process start, and command acknowledgment may support preconditions but may not be promoted to observed runtime PASS.
- Bind each runtime PASS claim to the exact commit/artifact and the observation(s) that make it true. For UI work, include the user input, target visibility/navigation, state mutation or clipboard payload, and focus/keyboard/modal outcome when relevant.
- If any required event is skipped, unavailable, stale, or merely inferred, report UNKNOWN/UNPROVEN and name the missing observation. Do not fill the gap with confidence language.
"""
p08_clause = "Runtime PASS requires current observed events at the claimed proof layer; implementation-only evidence cannot satisfy this gate."
if p08_clause not in p08.get("proofGate", ""):
    p08["proofGate"] = p08.get("proofGate", "").rstrip() + " " + p08_clause
base_path.write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

# Canonical generated website parity.
subprocess.run(
    ["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"],
    cwd=ROOT,
    check=True,
)
print("favorite observed-proof repair applied")
