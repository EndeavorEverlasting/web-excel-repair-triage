#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = ROOT / "tmp" / "sas-prompt-drafts"
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
TEST = ROOT / "tests" / "test_sysadminsuite_prompt_registry.py"
FLOOR = ROOT / "harness" / "test-floor.v1.json"

DRAFTS = [
    "protected-network-probe.json",
    "clinical-core-deploy.json",
    "autologon-recovery.json",
    "fleet-batch-change.json",
    "printer-mapping.json",
    "ad-ou-move.json",
]
NAMES = [
    "SysAdminSuite Protected-Network Endpoint Probe & Identity Gate",
    "SysAdminSuite Clinical-Core Deployment with AutoLogon Isolation",
    "SysAdminSuite AutoLogon-Only Crash-Safe Recovery",
    "SysAdminSuite Fleet Batch Endpoint Change Orchestrator",
    "SysAdminSuite Reversible Printer Mapping & Audit",
    "SysAdminSuite Active Directory Computer OU Move & Verification",
]


def run(*argv: str) -> str:
    proc = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode:
        raise SystemExit(proc.returncode)
    return proc.stdout


def write_focused_test() -> None:
    content = r'''from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry, prompt_registry_ops

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
PROFILE_JS = ROOT / "docs" / "prompt-kit-profiles.js"
ORDER = [
    "SysAdminSuite Protected-Network Endpoint Probe & Identity Gate",
    "SysAdminSuite Clinical-Core Deployment with AutoLogon Isolation",
    "SysAdminSuite AutoLogon-Only Crash-Safe Recovery",
    "SysAdminSuite Fleet Batch Endpoint Change Orchestrator",
    "SysAdminSuite Reversible Printer Mapping & Audit",
    "SysAdminSuite Active Directory Computer OU Move & Verification",
]
REQUIRED = {
    ORDER[0]: ("read-only", "DNS_UNRESOLVED", "identity evidence"),
    ORDER[1]: ("clinical-core", "SHA-256", "AutoLogon"),
    ORDER[2]: ("S4U", "UNKNOWN", "blindly rerun"),
    ORDER[3]: ("bounded concurrency", "per-host", "resume"),
    ORDER[4]: ("MAP", "UNMAP", "system-wide"),
    ORDER[5]: ("destination OU", "distinguished name", "already-correct"),
}


class SysAdminSuitePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_records = json.loads(RAW.read_text(encoding="utf-8"))["prompts"]
        cls.raw_by_name = {item["name"]: item for item in cls.raw_records}
        cls.full = {item["name"]: item for item in build_prompt_kit_registry.load_prompt_kit_registry()}
        cls.policy = build_prompt_kit_registry.load_actionability_policy()

    def test_six_recurring_sas_use_cases_have_distinct_canonical_owners(self) -> None:
        ids = []
        for name in ORDER:
            self.assertIn(name, self.raw_by_name)
            raw = self.raw_by_name[name]
            full = self.full[name]
            ids.append(raw["id"])
            self.assertEqual(raw.get("profile"), "sysadminsuite")
            self.assertEqual(raw.get("color"), "Cyan")
            self.assertEqual(raw.get("category"), "standard")
            self.assertIn("sysadminsuite", [str(x).casefold() for x in raw["keywords"]])
            self.assertEqual(full.get("actionabilityPolicy"), self.policy["policy_id"])
            self.assertIn(self.policy["marker"], full["copyContent"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_sas_owners_keep_their_distinct_failure_and_closure_boundaries(self) -> None:
        for name, phrases in REQUIRED.items():
            content = self.raw_by_name[name]["copyContent"]
            folded = content.casefold()
            for phrase in phrases:
                self.assertIn(phrase.casefold(), folded, (name, phrase))
        self.assertIn("do not mutate", self.raw_by_name[ORDER[0]]["copyContent"].casefold())
        self.assertIn("do not redeploy the clinical core", self.raw_by_name[ORDER[2]]["copyContent"].casefold())
        self.assertIn("does not reimplement the underlying mutation logic", self.raw_by_name[ORDER[3]]["copyContent"].casefold())
        self.assertIn("do not mutate trust, dns, firewall, gpo", self.raw_by_name[ORDER[4]]["copyContent"].casefold())
        self.assertIn("do not create a missing computer object", self.raw_by_name[ORDER[5]]["copyContent"].casefold())

    def test_existing_sas_profile_pack_discovers_every_new_owner(self) -> None:
        js = PROFILE_JS.read_text(encoding="utf-8")
        self.assertIn("SAS:{id:'SAS'", js)
        self.assertIn("'sysadminsuite'", js)
        for name in ORDER:
            prompt = self.raw_by_name[name]
            searchable = " ".join(
                [str(prompt.get("name", "")), str(prompt.get("profile", ""))]
                + [str(x) for x in prompt.get("keywords", [])]
            ).casefold()
            self.assertIn("sysadminsuite", searchable)

    def test_helper_reproduces_exact_registry_and_generated_site_from_semantic_records(self) -> None:
        allowed = prompt_registry_ops.REQUIRED_DRAFT_FIELDS | prompt_registry_ops.OPTIONAL_DRAFT_FIELDS
        with tempfile.TemporaryDirectory(prefix="sas-prompt-helper-") as tmp:
            sandbox = Path(tmp) / "repo"
            shutil.copytree(
                ROOT,
                sandbox,
                ignore=shutil.ignore_patterns(".git", "Outputs", "__pycache__", ".pytest_cache", "tmp"),
            )
            sandbox_raw = sandbox / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
            payload = json.loads(sandbox_raw.read_text(encoding="utf-8"))
            records = {item["name"]: item for item in payload["prompts"] if item.get("name") in ORDER}
            self.assertEqual(set(records), set(ORDER))
            payload["prompts"] = [item for item in payload["prompts"] if item.get("name") not in ORDER]
            sandbox_raw.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            receipts = []
            for index, name in enumerate(ORDER, start=1):
                draft = {key: value for key, value in records[name].items() if key in allowed}
                draft_path = sandbox / f"sas-draft-{index}.json"
                draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                proc = subprocess.run(
                    [sys.executable, "scripts/prompt_registry_ops.py", "add", "--input", str(draft_path), "--registry", "spec-architecture-prompts"],
                    cwd=sandbox,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stdout)
                receipts.append(json.loads(proc.stdout))

            self.assertEqual([r["id"] for r in receipts], [records[name]["id"] for name in ORDER])
            self.assertTrue(all(r["site_parity"] for r in receipts))
            self.assertEqual(sandbox_raw.read_bytes(), RAW.read_bytes())
            self.assertEqual((sandbox / "web" / "prompt-kit" / "index.html").read_bytes(), SITE.read_bytes())


if __name__ == "__main__":
    unittest.main()
'''
    TEST.write_text(content, encoding="utf-8")


def update_test_floor() -> None:
    payload = json.loads(FLOOR.read_text(encoding="utf-8"))
    rel = "tests/test_sysadminsuite_prompt_registry.py"
    tests = payload["self_tests"]
    if rel not in tests:
        anchor = "tests/test_spec_architecture_prompt_registry.py"
        index = tests.index(anchor) + 1 if anchor in tests else len(tests)
        tests.insert(index, rel)
    FLOOR.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    inspect = json.loads(run(sys.executable, "scripts/prompt_registry_ops.py", "inspect"))
    print("SAS_HELPER_INSPECT=" + json.dumps(inspect, sort_keys=True))

    receipts = []
    for filename in DRAFTS:
        output = run(
            sys.executable,
            "scripts/prompt_registry_ops.py",
            "add",
            "--input",
            str(DRAFT_ROOT / filename),
            "--registry",
            "spec-architecture-prompts",
        )
        receipts.append(json.loads(output))
    print("SAS_HELPER_RECEIPTS=" + json.dumps(receipts, sort_keys=True))

    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_name = {item.get("name"): item for item in payload["prompts"]}
    missing = [name for name in NAMES if name not in by_name]
    if missing:
        raise SystemExit(f"helper output missing SAS prompts: {missing}")
    ids = [by_name[name]["id"] for name in NAMES]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"duplicate SAS identities: {ids}")
    print("SAS_ALLOCATED_IDS=" + json.dumps(ids))

    write_focused_test()
    update_test_floor()

    run(sys.executable, "-m", "unittest", "tests.test_sysadminsuite_prompt_registry", "-v")
    run(sys.executable, "scripts/prompt_registry_ops.py", "validate")
    run(sys.executable, "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(sys.executable, "scripts/evaluate_prompt_language.py", "--summary")
    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
