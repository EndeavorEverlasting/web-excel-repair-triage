from __future__ import annotations

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

    def test_helper_readds_historical_semantic_records_with_fresh_append_only_identity_and_site_parity(self) -> None:
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

            # This copied fixture intentionally starts from a historical source state.
            # Rebind only the sandbox quality-history baseline to that state so the
            # lifecycle helper must extend a valid history chain rather than bless drift.
            quality_contract_path = sandbox / "harness" / "contracts" / "prompt-quality-history.v1.json"
            quality_contract = json.loads(quality_contract_path.read_text(encoding="utf-8"))
            source_rel = sandbox_raw.relative_to(sandbox).as_posix()
            source_row = next(
                row
                for row in quality_contract["canonical_body_sources"]
                if row["path"] == source_rel
            )
            source_bytes = sandbox_raw.read_bytes()
            source_row["git_blob_sha1"] = prompt_registry_ops._git_blob_sha1(source_bytes)
            source_row["baseline_size_bytes"] = len(source_bytes)
            quality_contract_path.write_text(
                json.dumps(quality_contract, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # Sprint 2: Remove linked semantic/capability migrations from sandbox.
            # The test rebases to a historical state by removing prompts, which invalidates
            # the existing migration chain. Since this is a sandbox test without git history,
            # clear only source-history migrations for this registry and capability migrations
            # linked to those removed source-history rows before fresh lifecycle operations.
            migrations_path = sandbox / "harness" / "prompt-compilation" / "prompt-semantic-migrations.v1.json"
            removed_source_history_ids: set[str] = set()
            if migrations_path.exists():
                migrations_data = json.loads(migrations_path.read_text(encoding="utf-8"))
                source_migrations = migrations_data.get("migrations", [])
                removed_source_history_ids = {
                    str(m["migration_id"])
                    for m in source_migrations
                    if m.get("path") == source_rel and m.get("migration_id")
                }
                migrations_data["migrations"] = [
                    m for m in source_migrations
                    if str(m.get("migration_id", "")) not in removed_source_history_ids
                ]
                migrations_path.write_text(
                    json.dumps(migrations_data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

            capability_migrations_path = (
                sandbox / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
            )
            if capability_migrations_path.exists() and removed_source_history_ids:
                capability_data = json.loads(
                    capability_migrations_path.read_text(encoding="utf-8")
                )
                capability_data["migrations"] = [
                    m for m in capability_data.get("migrations", [])
                    if str(m.get("source_history_migration_id", ""))
                    not in removed_source_history_ids
                ]
                capability_migrations_path.write_text(
                    json.dumps(capability_data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                self.assertFalse(
                    {
                        str(m.get("source_history_migration_id", ""))
                        for m in capability_data.get("migrations", [])
                    }
                    & removed_source_history_ids
                )

            inspect_proc = subprocess.run(
                [sys.executable, "scripts/prompt_registry_ops.py", "inspect"],
                cwd=sandbox,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(inspect_proc.returncode, 0, inspect_proc.stdout)
            inspect_receipt = json.loads(inspect_proc.stdout)
            floor = int(str(inspect_receipt["next_id"])[1:]) - 1

            receipts = []
            for index, name in enumerate(ORDER, start=1):
                draft = {key: value for key, value in records[name].items() if key in allowed}
                draft["semantic_profile"] = {
                    "direct_assignments": [
                        {
                            "capability_id": "execution.implementation",
                            "presence": "AWARE",
                            "ownership": "NONE",
                            "capability_relation": "ROUTES_TO",
                            "delivery_source": "ROUTED_OWNER",
                            "evidence_refs": ["tests/test_sysadminsuite_prompt_registry.py"],
                            "rationale": "Historical re-add fixture routes implementation to P07.",
                        }
                    ],
                    "evidence_refs": ["tests/test_sysadminsuite_prompt_registry.py"],
                    "distinct_residual": {
                        "summary": f"Restore the distinct historical SysAdminSuite use case {index} without claiming execution ownership.",
                        "evidence_refs": ["tests/test_sysadminsuite_prompt_registry.py"],
                        "reviewed_against": ["P07"],
                    },
                }
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

            expected_ids = [f"P{floor + offset}" for offset in range(1, len(ORDER) + 1)]
            self.assertEqual([receipt["id"] for receipt in receipts], expected_ids)
            self.assertTrue(all(receipt["site_parity"] for receipt in receipts))

            replayed = json.loads(sandbox_raw.read_text(encoding="utf-8"))["prompts"]
            replayed_by_name = {item["name"]: item for item in replayed if item.get("name") in ORDER}
            self.assertEqual(set(replayed_by_name), set(ORDER))
            for name in ORDER:
                original_semantics = {key: value for key, value in records[name].items() if key in allowed}
                replayed_semantics = {key: value for key, value in replayed_by_name[name].items() if key in allowed}
                self.assertEqual(replayed_semantics, original_semantics)

            replayed_site = (sandbox / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
            for name in ORDER:
                self.assertIn(name, replayed_site)

            # Exercise the actual atomic lifecycle, not only admission helpers:
            # ADD above -> EDIT with explicit no-capability-change proof -> RETIRE.
            target_receipt = receipts[-1]
            target_id = target_receipt["id"]
            target_name = ORDER[-1]
            target_record = replayed_by_name[target_name]
            edit_patch = {
                "useWhen": target_record["useWhen"]
                + " Synthetic lifecycle edit keeps the accepted capability profile unchanged."
            }
            edit_path = sandbox / "sas-edit.json"
            edit_path.write_text(
                json.dumps(edit_patch, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            edit_proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/prompt_registry_ops.py",
                    "edit",
                    "--prompt-id",
                    target_id,
                    "--input",
                    str(edit_path),
                    "--disposition",
                    "NO_CAPABILITY_CHANGE",
                    "--evidence-ref",
                    "tests/test_sysadminsuite_prompt_registry.py",
                    "--rationale",
                    "Synthetic lifecycle edit proves PSC009 disposition and atomic persistence.",
                    "--compression-disposition",
                    "PRESERVE",
                ],
                cwd=sandbox,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(edit_proc.returncode, 0, edit_proc.stdout)
            edit_receipt = json.loads(edit_proc.stdout)
            self.assertEqual(edit_receipt["status"], "edited")
            self.assertTrue(edit_receipt["site_parity"])
            self.assertEqual(edit_receipt["profile_version"], 2)

            edited_rows = json.loads(sandbox_raw.read_text(encoding="utf-8"))["prompts"]
            edited = next(row for row in edited_rows if row["id"] == target_id)
            self.assertIn("Synthetic lifecycle edit", edited["useWhen"])

            retire_proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/prompt_registry_ops.py",
                    "retire",
                    "--prompt-id",
                    target_id,
                    "--rationale",
                    "Synthetic lifecycle retirement proves canonical removal and tombstone retention.",
                ],
                cwd=sandbox,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(retire_proc.returncode, 0, retire_proc.stdout)
            retire_receipt = json.loads(retire_proc.stdout)
            self.assertEqual(retire_receipt["status"], "retired")
            self.assertTrue(retire_receipt["site_parity"])
            self.assertTrue((sandbox / retire_receipt["backup_path"]).is_dir())

            retired_rows = json.loads(sandbox_raw.read_text(encoding="utf-8"))["prompts"]
            self.assertNotIn(target_id, {row["id"] for row in retired_rows})
            retired_site = (sandbox / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn(target_name, retired_site)

            profiles = json.loads(
                (sandbox / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                    encoding="utf-8"
                )
            )["profiles"]
            tombstone = next(row for row in profiles if row["prompt_id"] == target_id)
            self.assertEqual(tombstone["profile_status"], "RETIRED")

            migrations = json.loads(
                (sandbox / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json").read_text(
                    encoding="utf-8"
                )
            )["migrations"]
            kinds = [row["migration_kind"] for row in migrations if row["prompt_id"] == target_id]
            self.assertEqual(kinds, ["ADD", "NO_CAPABILITY_CHANGE", "RETIRE"])
            self.assertTrue(all(row.get("source_history_migration_id") for row in migrations if row["prompt_id"] == target_id))

            next_proc = subprocess.run(
                [sys.executable, "scripts/prompt_registry_ops.py", "inspect"],
                cwd=sandbox,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(next_proc.returncode, 0, next_proc.stdout)
            next_receipt = json.loads(next_proc.stdout)
            self.assertGreater(int(next_receipt["next_id"][1:]), int(target_id[1:]))


if __name__ == "__main__":
    unittest.main()
