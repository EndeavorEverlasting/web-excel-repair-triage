from __future__ import annotations
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("observed_proof_validator", ROOT / "scripts/validate_observed_behavior_receipt.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)
PREPARE_SPEC = importlib.util.spec_from_file_location(
    "prepare_observed_behavior_subject",
    ROOT / "scripts/prepare_observed_behavior_subject.py",
)
PREPARE = importlib.util.module_from_spec(PREPARE_SPEC)
assert PREPARE_SPEC.loader is not None
PREPARE_SPEC.loader.exec_module(PREPARE)

CLEAN_CHECK = "git status --porcelain=v1 --untracked-files=no"
PARITY_COMMAND = "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check"


class ObservedBehaviorProofHarnessTests(unittest.TestCase):
    def exact_head_subject(self, sha: str = "1" * 40):
        artifact = ROOT / "web/prompt-kit/index.html"
        return {
            "commit_sha": sha,
            "clean_worktree": {
                "tracked_modifications": False,
                "status": "PASS",
                "check": CLEAN_CHECK,
            },
            "generated_parity": {
                "status": "PASS",
                "command": PARITY_COMMAND,
                "artifact_path": "web/prompt-kit/index.html",
            },
            "artifact": {
                "path": "web/prompt-kit/index.html",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            },
        }

    def base_receipt(self):
        return {
            "schema_version": "observed-behavior-proof/v1",
            "verdict": "PASS",
            "evidence_class": "browser_runtime_observed",
            "subject": self.exact_head_subject(),
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

    def test_non_pass_receipt_cannot_validate_as_success(self):
        for verdict in ("FAIL", "UNKNOWN", "UNPROVEN", None):
            receipt = self.base_receipt()
            receipt["verdict"] = verdict
            self.assertTrue(any("not PASS" in e for e in MOD.validate(receipt)))

    def test_missing_clean_worktree_or_generated_parity_fails_closed(self):
        for evidence_class in ("browser_runtime_observed", "target_runtime_observed"):
            receipt = self.base_receipt()
            receipt["evidence_class"] = evidence_class
            if evidence_class == "target_runtime_observed":
                receipt["claims"][0]["required_evidence_class"] = "target_runtime_observed"
            del receipt["subject"]["clean_worktree"]
            del receipt["subject"]["generated_parity"]
            errors = MOD.validate(receipt)
            self.assertTrue(any("clean_worktree" in e for e in errors), evidence_class)
            self.assertTrue(any("generated_parity" in e for e in errors), evidence_class)

    def test_dirty_or_stale_exact_head_claim_fails_closed(self):
        dirty = self.base_receipt()
        dirty["subject"]["clean_worktree"]["tracked_modifications"] = True
        self.assertTrue(any("tracked_modifications" in e for e in MOD.validate(dirty)))
        stale = self.base_receipt()
        stale["subject"]["generated_parity"]["status"] = "FAIL"
        self.assertTrue(any("generated_parity.status" in e for e in MOD.validate(stale)))

    def test_prepare_rejects_tracked_modifications_before_chromium(self):
        with self.assertRaises(PREPARE.ExactHeadError) as raised:
            PREPARE.prepare_exact_head_subject(
                porcelain_fn=lambda: " M docs/prompt-kit-polish.js\n",
                parity_fn=lambda: SimpleNamespace(returncode=0, stdout="", stderr=""),
                head_fn=lambda: "a" * 40,
            )
        self.assertIn("tracked modifications present; Chromium was not launched", str(raised.exception))
        self.assertIn("docs/prompt-kit-polish.js", str(raised.exception))

    def test_prepare_rejects_stale_generated_prompt_kit_before_chromium(self):
        with self.assertRaises(PREPARE.ExactHeadError) as raised:
            PREPARE.prepare_exact_head_subject(
                porcelain_fn=lambda: "",
                parity_fn=lambda: SimpleNamespace(returncode=1, stdout="", stderr="output is stale"),
                head_fn=lambda: "a" * 40,
            )
        self.assertIn("generated Prompt Kit parity failed; Chromium was not launched", str(raised.exception))

    def test_prepare_records_sha_and_exact_head_evidence(self):
        subject = PREPARE.prepare_exact_head_subject(
            porcelain_fn=lambda: "",
            parity_fn=lambda: SimpleNamespace(returncode=0, stdout="Prompt Kit check passed", stderr=""),
            head_fn=lambda: "b" * 40,
        )
        self.assertEqual(subject["commit_sha"], "b" * 40)
        self.assertEqual(subject["clean_worktree"]["tracked_modifications"], False)
        self.assertEqual(subject["clean_worktree"]["status"], "PASS")
        self.assertEqual(subject["generated_parity"]["status"], "PASS")
        self.assertEqual(subject["generated_parity"]["command"], PARITY_COMMAND)
        self.assertEqual(
            subject["artifact"]["sha256"],
            hashlib.sha256((ROOT / "web/prompt-kit/index.html").read_bytes()).hexdigest(),
        )

    def test_reverify_fails_closed_on_later_dirty_tree(self):
        errors = PREPARE.reverify_exact_head_tree(
            self.exact_head_subject("c" * 40),
            porcelain_fn=lambda: " M web/prompt-kit/index.html\n",
            parity_fn=lambda: SimpleNamespace(returncode=0, stdout="", stderr=""),
            head_fn=lambda: "c" * 40,
        )
        self.assertTrue(any("tracked modifications" in e for e in errors))

    def test_browser_proofs_call_exact_head_preflight_before_observe(self):
        for rel in (
            "tests/prompt_kit_favorite_browser_proof.py",
            "tests/prompt_kit_external_resources_browser_proof.py",
            "tests/prompt_kit_hotkey_identity_browser_proof.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("subject = prepare_exact_head_subject()", source)
            self.assertLess(
                source.index("subject = prepare_exact_head_subject()"),
                source.index("observations = observe("),
            )
            self.assertIn("Chromium was not launched", source)

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
