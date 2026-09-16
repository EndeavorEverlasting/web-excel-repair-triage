#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF CONTRACT"
P140_MARKER = "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(path: str, payload):
    (ROOT / path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def one(items, prompt_id: str):
    matches = [item for item in items if isinstance(item, dict) and item.get("id") == prompt_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {prompt_id}, found {len(matches)}")
    return matches[0]


def append_once(text: str, marker: str, block: str) -> str:
    if marker in text:
        return text
    return text.rstrip() + "\n\n" + block.strip() + "\n"


def append_sentence(value: str, marker: str, sentence: str) -> str:
    if marker in value:
        return value
    return value.rstrip().rstrip(".") + ". " + sentence.strip()


def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"anchor missing in {path}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_doc_section(path: str, marker: str, section: str):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if marker not in text:
        p.write_text(text.rstrip() + "\n\n" + section.strip() + "\n", encoding="utf-8")


def strengthen_p11():
    path = "docs/prompts.json"
    prompts = load(path)
    before_count = len(prompts)
    p11 = one(prompts, "P11")
    if p11.get("name") != "End-to-End Harness Validator":
        raise SystemExit("P11 identity drifted")
    block = r'''GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF CONTRACT
- When repository evidence says an artifact has a mapped Google Drive allocation or stable Drive identity, treat that allocation as a harness requirement, not optional presentation metadata.
- Resolve the canonical Drive identity from the repository/provider map, manifest, registry, or workspace authority before offering a local artifact path or ad-hoc external mirror.
- If publication to the allocated Drive artifact succeeds and readback verifies the intended identity/content, the verified Google Drive URL is the PRIMARY user-facing artifact link. A repo path, CI artifact, temporary path, `sandbox:/...` link, local filesystem path, or downloadable copy is supplemental only.
- A user explicitly asking for a downloadable copy permits a supplemental download; it does not demote a healthy mapped Drive artifact from primary handoff.
- If Drive publication, identity resolution, permission, or readback is blocked, name the exact Drive gate before offering a bounded local/download fallback. Do not imply synchronization succeeded.
- Preserve per-artifact authority. Drive-primary handoff does not make Drive source control, does not authorize lossy Google-native round trips, and does not let timestamp recency override an explicit authority/conflict contract.
- Regression hardening must fail when a Drive-allocated artifact is handed off only through a local, sandbox, CI, repo-output, or unrelated external resource while a verified mapped Drive artifact is available.
- Reuse stable Drive identity; do not create a second CURRENT file or workspace because local output is easier to link.'''
    p11["copyContent"] = append_once(str(p11["copyContent"]), MARKER, block)
    p11["inspectFirst"] = append_sentence(str(p11["inspectFirst"]), "mapped Google Drive allocations", "Inspect mapped Google Drive allocations/identities and any artifact-handoff contract when the repository publishes collaboration artifacts to Drive.")
    p11["expectedOutput"] = append_sentence(str(p11["expectedOutput"]), "Drive-primary handoff proof", "For Drive-allocated artifacts, include Drive-primary handoff proof or an exact Drive blocker; local/downloadable artifacts remain supplemental.")
    p11["proofGate"] = append_sentence(str(p11["proofGate"]), "Drive-allocated artifact", "Any Drive-allocated artifact fails the harness gate if a healthy verified Drive identity exists but the operator is referred only to local, sandbox, CI, repo-output, or unrelated external resources.")
    kws = list(p11.get("keywords", []))
    for kw in ["google drive handoff", "drive allocated artifact", "drive primary link"]:
        if kw not in kws:
            kws.append(kw)
    p11["keywords"] = kws
    if len(prompts) != before_count:
        raise SystemExit("P11 strengthening changed prompt count")
    save(path, prompts)


def strengthen_p140():
    path = "registry/prompts/repository-work-ledger-prompts.v1.json"
    payload = load(path)
    prompts = payload["prompts"]
    before_count = len(prompts)
    p140 = one(prompts, "P140")
    if p140.get("name") != "Connected Health Record Workspace Synchronizer":
        raise SystemExit("P140 identity drifted")
    block = r'''GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF
- A health record may be backed by a repository, database, app, document store, spreadsheet, or connector. Do not assume Google Drive is authoritative merely because it is connected.
- When the established health workspace explicitly maps an operator-facing artifact to Google Drive, resolve and reuse that exact Drive identity. Do not create a competing same-purpose Drive copy by filename guess.
- After successful publication/update and readback of that mapped Drive artifact, return the verified Google Drive URL as the primary operator-facing artifact. Local repo paths, exports, temporary files, `sandbox:/...` links, CI artifacts, and unrelated external mirrors are supplemental only.
- If the mapped Drive identity cannot be resolved, updated, or read back, preserve the strongest existing truth, name the exact access/permission/identity gate, and only then use a bounded fallback. Never call a local export "synced" when Drive proof is missing.
- An explicit request for a downloadable copy may add one, but it does not replace a healthy allocated Drive artifact as the primary handoff.
- Preserve privacy and source authority: this rule changes handoff/routing behavior, not which clinical or health-data source is canonical.'''
    p140["copyContent"] = append_once(str(p140["copyContent"]), P140_MARKER, block)
    p140["inspectFirst"] = append_sentence(str(p140["inspectFirst"]), "Google Drive allocation", "Inspect any established Google Drive allocation/stable file identity and its authority contract before creating or returning a new artifact.")
    p140["expectedOutput"] = append_sentence(str(p140["expectedOutput"]), "Drive-primary operator handoff", "When a mapped Drive artifact exists and readback succeeds, provide a Drive-primary operator handoff with any local/downloadable representation treated as supplemental.")
    p140["proofGate"] = append_sentence(str(p140["proofGate"]), "mapped Drive artifact", "A mapped Drive artifact is not complete when only a local/export/sandbox/external link is returned despite successful Drive publication/readback; blocked Drive handoff must name the exact gate.")
    kws = list(p140.get("keywords", []))
    for kw in ["google drive health record", "drive handoff", "mapped drive artifact"]:
        if kw not in kws:
            kws.append(kw)
    p140["keywords"] = kws
    if len(prompts) != before_count:
        raise SystemExit("P140 strengthening changed prompt count")
    save(path, payload)


def strengthen_artifact_handoff_contract():
    path = "harness/artifact-handoff/contracts/share-alias-download.v1.json"
    payload = load(path)
    rules = payload["rules"]
    additions = {
        "drive_allocation_primary_handoff": "When an artifact has an explicit Google Drive allocation/stable identity and publication plus readback succeed, the verified Google Drive URL is the primary user-facing handoff; local, sandbox, CI, repo-output, downloadable, or unrelated external resources are supplemental only.",
        "drive_blocked_fallback": "When the allocated Drive identity cannot be resolved, published, permitted, or read back, the handoff must name the exact Drive gate before a local/download fallback is used and must not claim synchronization succeeded.",
        "drive_authority_preservation": "Drive-primary handoff does not change per-artifact authority, make Drive source control, authorize lossy Google-native round trips, or permit creation of a competing CURRENT identity.",
        "explicit_download_is_supplemental": "An explicit operator request for a downloadable copy allows a supplemental download but does not demote a healthy verified mapped Google Drive artifact from primary handoff."
    }
    for key, value in additions.items():
        rules[key] = value
    save(path, payload)


def patch_artifact_handoff_validator():
    path = "scripts/validate_artifact_handoff_harness.py"
    replace_once(
        path,
        '    "operator_zero_rename",\n}',
        '    "operator_zero_rename",\n    "drive_allocation_primary_handoff",\n    "drive_blocked_fallback",\n    "drive_authority_preservation",\n    "explicit_download_is_supplemental",\n}',
    )
    anchor = 'def sha256(path: Path) -> str:\n'
    function = r'''def is_google_drive_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc.casefold() in {
        "drive.google.com",
        "docs.google.com",
    }


def validate_drive_allocated_handoff(
    *,
    drive_allocated: bool,
    drive_published_readback: bool,
    primary_href: str,
    drive_url: str | None = None,
    supplemental_hrefs: list[str] | None = None,
    drive_blocker: str | None = None,
    download_explicitly_requested: bool = False,
) -> list[str]:
    """Validate user-facing handoff precedence for a mapped Drive artifact."""
    del download_explicitly_requested  # explicit download changes supplementation, never primary precedence
    supplemental_hrefs = supplemental_hrefs or []
    if not drive_allocated:
        return []
    errors: list[str] = []
    if drive_published_readback:
        if not is_google_drive_url(drive_url):
            errors.append("verified Drive handoff requires a canonical Google Drive URL")
        if not drive_url or primary_href != drive_url:
            errors.append("verified mapped Google Drive URL must be the primary handoff")
        if not is_google_drive_url(primary_href):
            errors.append("local, sandbox, CI, repo-output, download, or external mirror cannot be primary while Drive is healthy")
    else:
        if not is_google_drive_url(primary_href) and not (drive_blocker or "").strip():
            errors.append("non-Drive fallback requires the exact Drive blocker")
    if drive_url and drive_url in supplemental_hrefs and primary_href != drive_url and drive_published_readback:
        errors.append("healthy Drive identity may not be demoted to supplemental handoff")
    return errors


'''
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if "def validate_drive_allocated_handoff(" not in text:
        if anchor not in text:
            raise SystemExit("artifact handoff validator insertion anchor missing")
        text = text.replace(anchor, function + anchor, 1)
        p.write_text(text, encoding="utf-8")
    # Require prompt strengthening as part of static harness proof.
    anchor2 = '    fixture_results = validate_contract_payload(load_json(CONTRACT))\n\n'
    insert2 = r'''    fixture_results = validate_contract_payload(load_json(CONTRACT))

    prompt_sources = {
        "P11": ROOT / "docs" / "prompts.json",
        "P140": ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json",
    }
    p11_items = load_json(prompt_sources["P11"])
    p140_items = load_json(prompt_sources["P140"]).get("prompts", [])
    p11 = next((item for item in p11_items if item.get("id") == "P11"), None)
    p140 = next((item for item in p140_items if item.get("id") == "P140"), None)
    if not p11 or "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF CONTRACT" not in str(p11.get("copyContent", "")):
        raise ValidationError("P11 is missing the Google Drive primary-handoff harness contract")
    if not p140 or "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF" not in str(p140.get("copyContent", "")):
        raise ValidationError("P140 is missing the Google Drive primary-handoff specialization")

'''
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if "P11 is missing the Google Drive primary-handoff harness contract" not in text:
        if anchor2 not in text:
            raise SystemExit("static harness prompt anchor missing")
        text = text.replace(anchor2, insert2, 1)
        p.write_text(text, encoding="utf-8")


def patch_artifact_handoff_tests():
    path = "tests/test_artifact_handoff_harness.py"
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    marker = "def test_drive_allocated_artifact_requires_drive_primary_when_readback_is_green"
    if marker in text:
        return
    insert = r'''
    def test_drive_allocated_artifact_requires_drive_primary_when_readback_is_green(self) -> None:
        drive_url = "https://docs.google.com/spreadsheets/d/abc/edit"
        errors = validator.validate_drive_allocated_handoff(
            drive_allocated=True,
            drive_published_readback=True,
            primary_href="sandbox:/mnt/data/report.xlsx",
            drive_url=drive_url,
            supplemental_hrefs=["sandbox:/mnt/data/report.xlsx"],
        )
        self.assertTrue(any("primary" in error for error in errors))

    def test_drive_allocated_artifact_accepts_drive_primary_and_local_supplement(self) -> None:
        drive_url = "https://drive.google.com/file/d/abc/view"
        errors = validator.validate_drive_allocated_handoff(
            drive_allocated=True,
            drive_published_readback=True,
            primary_href=drive_url,
            drive_url=drive_url,
            supplemental_hrefs=["sandbox:/mnt/data/report.xlsx"],
            download_explicitly_requested=True,
        )
        self.assertEqual([], errors)

    def test_drive_blocked_fallback_requires_exact_gate(self) -> None:
        errors = validator.validate_drive_allocated_handoff(
            drive_allocated=True,
            drive_published_readback=False,
            primary_href="sandbox:/mnt/data/report.xlsx",
        )
        self.assertTrue(any("blocker" in error for error in errors))
        allowed = validator.validate_drive_allocated_handoff(
            drive_allocated=True,
            drive_published_readback=False,
            primary_href="sandbox:/mnt/data/report.xlsx",
            drive_blocker="Drive connector lacks write permission for mapped file ID",
        )
        self.assertEqual([], allowed)

    def test_drive_healthy_rejects_unrelated_external_primary(self) -> None:
        drive_url = "https://docs.google.com/document/d/abc/edit"
        errors = validator.validate_drive_allocated_handoff(
            drive_allocated=True,
            drive_published_readback=True,
            primary_href="https://example.invalid/report.xlsx",
            drive_url=drive_url,
        )
        self.assertTrue(any("primary" in error for error in errors))
'''
    anchor = '\n\nif __name__ == "__main__":\n'
    if anchor not in text:
        raise SystemExit("artifact handoff test anchor missing")
    p.write_text(text.replace(anchor, insert + anchor, 1), encoding="utf-8")


def strengthen_artifact_handoff_docs():
    append_doc_section(
        "harness/artifact-handoff/WORKFLOW.md",
        "## Google Drive allocation precedence",
        '''## Google Drive allocation precedence

When a repository artifact has an explicit mapped Google Drive allocation/stable identity, the handoff workflow resolves that identity before any local fallback. After publication/update plus readback succeed, the Google Drive URL is the primary operator-facing link. Local paths, repo outputs, CI artifacts, `sandbox:/...` downloads, and unrelated external mirrors may be supplemental only. If Drive is blocked, name the exact identity/access/write/readback gate before falling back; never claim Drive synchronization from a local artifact alone. This changes handoff precedence, not per-artifact source authority.''',
    )
    append_doc_section(
        "harness/artifact-handoff/CODEBASE_MAP.md",
        "## Drive-primary handoff seam",
        '''## Drive-primary handoff seam

`contracts/share-alias-download.v1.json` also owns provider-allocation precedence for Google Drive: stable mapped Drive identity -> publication/readback proof -> Drive-primary user-facing link. `scripts/validate_artifact_handoff_harness.py` supplies the executable regression so a healthy Drive allocation cannot silently collapse back to a local/sandbox/CI/external-only handoff.''',
    )


def register_harness_owner():
    manifest_path = "harness/manifest.v1.json"
    payload = load(manifest_path)
    domain = payload.setdefault("domain_contracts", {})
    domain.setdefault("artifact_handoff", {
        "contract": "harness/artifact-handoff/contracts/share-alias-download.v1.json",
        "validator": "scripts/validate_artifact_handoff_harness.py",
        "contract_tests": "tests/test_artifact_handoff_harness.py",
        "workflow": "harness/artifact-handoff/WORKFLOW.md",
        "harness_gate": "python scripts/validate_artifact_handoff_harness.py --summary",
        "domain_manifest": "harness/artifact-handoff/manifest.v1.json",
        "skill": ".ai/skills/share-artifact-alias-handoff/SKILL.md",
        "operator_report": "harness/artifact-handoff/reports/CURRENT_STATE.md"
    })
    save(manifest_path, payload)

    validators_path = "harness/validators.v1.json"
    validators = load(validators_path)
    ids = {item.get("id") for item in validators.get("validators", []) if isinstance(item, dict)}
    if "artifact-handoff-harness-audit" not in ids:
        validators["validators"].append({
            "id": "artifact-handoff-harness-audit",
            "class": "contract",
            "command": "python scripts/validate_artifact_handoff_harness.py --summary",
            "blocking": True,
            "output": "process log",
            "proof_ceiling": "Static artifact handoff identity, alias integrity, and Google Drive allocation precedence proof."
        })
    save(validators_path, validators)


def strengthen_p11_runtime_validator():
    path = "scripts/validate_app_harness.py"
    replace_once(
        path,
        '    "scripts/validate_harness.py",\n    ".githooks/pre-commit",',
        '    "scripts/validate_harness.py",\n    "harness/artifact-handoff/manifest.v1.json",\n    "scripts/validate_artifact_handoff_harness.py",\n    ".githooks/pre-commit",',
    )
    replace_once(
        path,
        '        command == (sys.executable, "-m", "triage.gitignore_hygiene"),\n',
        '        command == (sys.executable, "-m", "triage.gitignore_hygiene"),\n        command == (sys.executable, str(root / "scripts" / "validate_artifact_handoff_harness.py"), "--summary"),\n',
    )
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if "def check_artifact_handoff_contract(" not in text:
        anchor = 'def check_optional_mcp(root: Path, env: Mapping[str, str]) -> Check:\n'
        fn = r'''def check_artifact_handoff_contract(root: Path, runner: Runner) -> Check:
    command = [sys.executable, str(root / "scripts" / "validate_artifact_handoff_harness.py"), "--summary"]
    completed = runner(command, root)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        return result("artifact_handoff_contract", "artifact handoff contract", False, "artifact_handoff_harness_failed", [detail][:1])
    return result("artifact_handoff_contract", "artifact handoff contract", True, "drive_primary_handoff_contract_passed")


'''
        if anchor not in text:
            raise SystemExit("P11 runtime validator function anchor missing")
        text = text.replace(anchor, fn + anchor, 1)
        p.write_text(text, encoding="utf-8")
    replace_once(
        path,
        '        check_report_renderer(root),\n        check_optional_mcp(root, environment),',
        '        check_report_renderer(root),\n        check_artifact_handoff_contract(root, runner),\n        check_optional_mcp(root, environment),',
    )


def patch_p11_runtime_tests():
    path = "tests/test_app_harness_validator.py"
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    text = text.replace('{"passed": 5, "skipped": 1, "failed": 0}', '{"passed": 6, "skipped": 1, "failed": 0}')
    text = text.replace('Result: 5 passed / 1 skipped / 0 failed', 'Result: 6 passed / 1 skipped / 0 failed')
    text = text.replace('self.assertEqual(6, len(decoded["validator_set"]))', 'self.assertEqual(7, len(decoded["validator_set"]))')
    if "test_drive_primary_handoff_is_required_in_p11_gate" not in text:
        insert = r'''
    def test_drive_primary_handoff_is_required_in_p11_gate(self):
        check = validator.check_artifact_handoff_contract(ROOT, self.fake_runner)
        self.assertEqual("REQUIRED", check.requirement)
        self.assertEqual("PASS", check.status)
        self.assertEqual("drive_primary_handoff_contract_passed", check.reason)
'''
        anchor = '\n    def test_optional_missing_dependency_is_honest_skip(self):\n'
        if anchor not in text:
            raise SystemExit("app harness test insertion anchor missing")
        text = text.replace(anchor, insert + anchor, 1)
    p.write_text(text, encoding="utf-8")


def add_prompt_strengthening_regression():
    path = ROOT / "tests" / "test_google_drive_handoff_prompt_strengthening.py"
    if path.exists():
        return
    path.write_text(r'''from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry


class GoogleDriveHandoffPromptStrengtheningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_kit_registry()}

    def test_p11_owns_drive_allocated_handoff_harness_semantics(self) -> None:
        body = self.prompts["P11"]["copyContent"]
        for phrase in (
            "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF CONTRACT",
            "verified Google Drive URL is the PRIMARY user-facing artifact link",
            "`sandbox:/...` link",
            "supplemental only",
            "name the exact Drive gate",
            "Drive-primary handoff does not make Drive source control",
            "Regression hardening must fail",
        ):
            self.assertIn(phrase, body)

    def test_p140_specializes_drive_primary_handoff_without_making_drive_universal_authority(self) -> None:
        body = self.prompts["P140"]["copyContent"]
        for phrase in (
            "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF",
            "Do not assume Google Drive is authoritative merely because it is connected",
            "return the verified Google Drive URL as the primary operator-facing artifact",
            "`sandbox:/...` links",
            "name the exact access/permission/identity gate",
            "this rule changes handoff/routing behavior, not which clinical or health-data source is canonical",
        ):
            self.assertIn(phrase, body)

    def test_strengthening_reuses_existing_prompt_ids(self) -> None:
        self.assertEqual("End-to-End Harness Validator", self.prompts["P11"]["name"])
        self.assertEqual("Connected Health Record Workspace Synchronizer", self.prompts["P140"]["name"])


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")


def main():
    strengthen_p11()
    strengthen_p140()
    strengthen_artifact_handoff_contract()
    patch_artifact_handoff_validator()
    patch_artifact_handoff_tests()
    strengthen_artifact_handoff_docs()
    register_harness_owner()
    strengthen_p11_runtime_validator()
    patch_p11_runtime_tests()
    add_prompt_strengthening_regression()
    print("Applied P79 strengthen-first disposition: P11 + P140 + existing artifact-handoff harness; no prompt added.")


if __name__ == "__main__":
    main()
