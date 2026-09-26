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
        single = next(item for item in contract["requirements"] if item["id"] == "single_click_copy")
        self.assertIn("touch tap", single["event"])
        self.assertIn("whole non-control prompt-card surface", single["expected"])
        self.assertIn("must not have to scroll through a detail modal", single["expected"])
        detail_copy = next(item for item in contract["requirements"] if item["id"] == "detail_surface_click_copy")
        self.assertIn("non-conflicting", detail_copy["event"])
        self.assertIn("active text selection", detail_copy["expected"])
        detail_edges = next(item for item in contract["requirements"] if item["id"] == "detail_local_edge_navigation")
        self.assertIn("Home/End are panel-local", detail_edges["expected"])

    def test_current_source_audit_is_structured_without_inflating_proof(self) -> None:
        report = interactions.audit_implementation()
        self.assertEqual(report["schema_version"], "prompt-kit-interaction-audit-result/v1")
        self.assertEqual(
            {item["id"] for item in report["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )
        self.assertIn("implementation_ready", report)
        self.assertTrue(report["implementation_ready"], report["missing_static_markers"])
        self.assertEqual(report["missing_static_markers"], [])
        self.assertIn("does not prove", report["proof_ceiling"].lower())

    def test_synthetic_compliant_source_satisfies_static_gate(self) -> None:
        js = """
        card.onclick=function(e){copyPrompt(p.id)};
        card.ondblclick=function(e){e.preventDefault();showPromptDetail(p.id)};
        document.getElementById('promptDetailOverlay').addEventListener('click',function(e){
          if(e.target===this){closePromptDetail();document.getElementById('grid').focus()}
        });
        btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id)};
        function promptDetailHasTextSelection(){return false}
        function isPromptDetailCopyConflict(target){return target.closest('[data-prompt-detail-no-copy]')}
        function handlePromptDetailSurfaceCopy(e){if(isPromptDetailCopyConflict(e.target))return;copyPrompt(openPromptId)}
        function scrollPromptDetailTo(edge){return true}
        function handlePromptDetailKeydown(e){if(e.key==='Home'||e.key==='End'){scrollPromptDetailTo(e.key==='Home'?'top':'bottom')}}
        var promptDetailTop=true,promptDetailBottom=true;
        document.addEventListener('keydown',function(e){
          switch(e.key){case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}}
        });
        """
        checks = interactions.evaluate_source(js)
        self.assertEqual(set(checks), interactions.REQUIRED_REQUIREMENT_IDS)
        self.assertTrue(all(checks.values()), checks)

    def test_deferred_single_click_and_object_literal_double_click_are_recognized(self) -> None:
        js = """
        function schedulePromptCardSingleClick(card,id){
          selectPrompt(id,{source:'pointer',scroll:false});
          card._copyTimer=setTimeout(function(){copyPrompt(id)},350)
        }
        card.onclick=function(e){schedulePromptCardSingleClick(card,p.id)};
        card.ondblclick=function(e){selectPrompt(p.id,{source:'pointer',scroll:true});showPromptDetail(p.id,card)};
        """
        checks = interactions.evaluate_source(js)
        self.assertTrue(checks["single_click_copy"])
        self.assertTrue(checks["double_click_expand"])

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
