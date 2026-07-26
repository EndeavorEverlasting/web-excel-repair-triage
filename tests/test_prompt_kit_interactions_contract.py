from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_interactions as interactions


class PromptKitInteractionHarnessTests(unittest.TestCase):
    def test_contract_is_complete_and_versioned(self) -> None:
        contract = interactions.validate_contract()
        self.assertEqual(contract["schema_version"], "prompt-kit-interaction-contract/v1")
        self.assertEqual(contract["contract_id"], "prompt-kit-card-interactions")
        self.assertEqual(
            {item["id"] for item in contract["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )
        self.assertIn("--require-implementation", contract["validation"]["implementation_gate"])

    def test_current_source_audit_is_structured_without_inflating_proof(self) -> None:
        report = interactions.audit_implementation()
        self.assertEqual(report["schema_version"], "prompt-kit-interaction-audit-result/v1")
        self.assertEqual(
            {item["id"] for item in report["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )
        self.assertIn("implementation_ready", report)
        self.assertIn("missing_static_markers", report)
        self.assertIn("does not prove", report["proof_ceiling"].lower())

    def test_synthetic_compliant_source_satisfies_static_gate(self) -> None:
        js = """
        card.onclick=function(e){copyPrompt(p.id)};
        card.ondblclick=function(e){e.preventDefault();showPromptDetail(p.id)};
        document.getElementById('promptDetailOverlay').addEventListener('click',function(e){
          if(e.target===this){closePromptDetail();document.getElementById('grid').focus()}
        });
        btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id)};
        document.addEventListener('keydown',function(e){
          switch(e.key){case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}}
        });
        """
        checks = interactions.evaluate_source(js)
        self.assertEqual(set(checks), interactions.REQUIRED_REQUIREMENT_IDS)
        self.assertTrue(all(checks.values()), checks)

    def test_legacy_single_click_expand_is_detected_as_gap(self) -> None:
        js = """
        card.onclick=function(){showPromptDetail(p.id)};
        btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id)};
        document.addEventListener('keydown',function(e){
          switch(e.key){case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}}
        });
        """
        checks = interactions.evaluate_source(js)
        self.assertFalse(checks["single_click_copy"])
        self.assertFalse(checks["double_click_expand"])
        self.assertFalse(checks["outside_click_collapse_restore"])
        self.assertTrue(checks["escape_close_preserved"])
        self.assertTrue(checks["copy_button_compatibility"])

    def test_harness_mode_writes_report_without_requiring_product_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "interaction-audit.json"
            rc = interactions.main(["--output", str(output)])
            self.assertEqual(rc, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_id"], "prompt-kit-card-interactions")


if __name__ == "__main__":
    unittest.main()
