from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNEY = ROOT / "docs" / "prompt-kit-journey.js"
GUIDED = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-discovery.v1.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


class PromptKitGuidanceTests(unittest.TestCase):
    def test_journey_runtime_reuses_registered_next_steps(self) -> None:
        source = JOURNEY.read_text(encoding="utf-8")
        for marker in (
            "promptKit.guidance.completed.v1",
            "function guidanceNextIds(prompt)",
            "String(prompt&&prompt.nextStep||'')",
            "root.buildPromptGuidanceModel=guidanceModel",
            "Guided workflow",
            "NEXT-STEP CONTRACT",
            "READY TO CONTINUE WHEN",
            "Mark this step complete",
            "MutationObserver",
            "stableGuidanceOrigin",
            "closest('#promptDetail')",
            "finder-journey-preview",
            "prefers-reduced-motion:reduce",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("NEXT_PROMPT_MAP", source)
        self.assertNotIn("hard-coded prompt", source.lower())
        self.assertNotIn("MAX_NEXT", source)

    def test_next_prompt_parser_keeps_known_ids_deduplicated_and_ordered(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is not installed in this test environment")
        script = f"""const fs=require('fs');
global.PROMPTS=[
 {{id:'P06',name:'Cleanup',nextStep:'Use P07 for feature work, P12 to close, or P07 again.',useWhen:'cleanup'}},
 {{id:'P07',name:'Sprint',nextStep:'Use P11 or P12.',useWhen:'build'}},
 {{id:'P11',name:'Proof',nextStep:'Use P12.',useWhen:'prove'}},
 {{id:'P12',name:'Close',nextStep:'none; no safe actionable work remains',useWhen:'close'}}
];
const vm=require('vm');
vm.runInThisContext(fs.readFileSync({json.dumps(str(JOURNEY))},'utf8'));
const ids=global.promptGuidanceNextIds('P06');
if(JSON.stringify(ids)!==JSON.stringify(['P07','P12'])) throw new Error(JSON.stringify(ids));
const model=global.buildPromptGuidanceModel('P07');
if(!model || model.current.id!=='P07' || model.next.map(x=>x.id).join(',')!=='P11,P12') throw new Error('bad model');
console.log('GUIDANCE_MODEL_PASS');
"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name
        try:
            completed = subprocess.run(
                [node, tmp_path],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("GUIDANCE_MODEL_PASS", completed.stdout)
        finally:
            os.unlink(tmp_path)

    def test_complex_next_step_preserves_every_registered_route(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is not installed in this test environment")
        script = f"""const fs=require('fs');
global.PROMPTS=[
 {{id:'P03',name:'Intake',nextStep:'Use P06.',useWhen:'intake'}},
 {{id:'P06',name:'Cleanup',nextStep:'Use P07.',useWhen:'cleanup'}},
 {{id:'P07',name:'Sprint',nextStep:'Use P12.',useWhen:'build'}},
 {{id:'P12',name:'Close',nextStep:'none; no safe actionable work remains',useWhen:'close'}},
 {{id:'P14',name:'Repair',nextStep:'Use P15.',useWhen:'repair'}},
 {{id:'P15',name:'Merge',nextStep:'Use P12.',useWhen:'merge'}},
 {{id:'P20',name:'Discover',nextStep:'Use P07.',useWhen:'discover'}},
 {{id:'P57',name:'Router',nextStep:'Route through P03, P06, P07, P14, P15, P20, then P12.',useWhen:'route'}}
];
const vm=require('vm');
vm.runInThisContext(fs.readFileSync({json.dumps(str(JOURNEY))},'utf8'));
const ids=global.promptGuidanceNextIds('P57');
const expected=['P03','P06','P07','P14','P15','P20','P12'];
if(JSON.stringify(ids)!==JSON.stringify(expected)) throw new Error(JSON.stringify(ids));
console.log('GUIDANCE_COMPLEX_ROUTE_PASS');
"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name
        try:
            completed = subprocess.run(
                [node, tmp_path],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("GUIDANCE_COMPLEX_ROUTE_PASS", completed.stdout)
        finally:
            os.unlink(tmp_path)

    def test_builder_and_discovery_contract_register_journey_runtime(self) -> None:
        builder = BUILDER.read_text(encoding="utf-8")
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("PROMPT_JOURNEY_RUNTIME", builder)
        self.assertIn("prompt-kit-journey.js", builder)
        self.assertEqual(
            contract["surface"]["journey_behavior_source"],
            "docs/prompt-kit-journey.js",
        )
        ids = {item["id"] for item in contract["requirements"]}
        self.assertIn("guided_next_step_journey", ids)
        self.assertIn("guided_completion_state", ids)

    def test_generated_site_contains_exact_journey_runtime(self) -> None:
        journey = JOURNEY.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn(journey, deployed)
        self.assertIn("prompt-kit-journey-styles", deployed)

    def test_existing_questionnaire_remains_shared_search_driven(self) -> None:
        guided = GUIDED.read_text(encoding="utf-8")
        self.assertIn("filterPromptsForQuery(PROMPTS,query)", guided)
        self.assertIn("slice(0,3)", guided)
        self.assertIn("✦ Tutorial · Find My Prompt", guided)


if __name__ == "__main__":
    unittest.main()
