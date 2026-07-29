from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-discovery.v1.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


class PromptKitDiscoveryTests(unittest.TestCase):
    def test_contract_covers_field_regressions(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-discovery-contract/v1")
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            {
                "section_heading_contrast",
                "ranked_search",
                "synonym_routing",
                "body_noise_suppression",
                "local_favorites",
                "favorites_first",
                "favorite_accessibility",
                "generated_site_parity",
            },
        )

    def test_section_button_has_explicit_dark_surface_contrast(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn(".section-divider .section-toggle{color:var(--text-primary)", js)
        self.assertIn(".section-divider .section-toggle .sd-count{color:var(--text-secondary)}", js)

    def test_ranked_search_uses_synonyms_without_copy_body_flood(self) -> None:
        js = JS.read_text(encoding="utf-8")
        start = js.index("function normalizeSearchText")
        end = js.index("function promptSequenceValue")
        helpers = js[start:end]
        script = "var SYNONYMS={artifact:'P56',closeout:'P12',handoff:'P12'};\n" + helpers + r'''
var prompts=[
 {id:'P56',seq:'56',name:'Context to Artifact Builder',type:'BUILD + ARTIFACT',class:'standard',useWhen:'Generate the actual artifact from supplied context',sprintRole:'implementor',proofGate:'artifact proof',copyContent:'build the file',keywords:['artifact','generate']},
 {id:'P07',seq:'7',name:'Sprint Executor',type:'BUILD',class:'standard',useWhen:'Execute repository work',sprintRole:'implementor',proofGate:'commit proof',copyContent:'report expected artifacts and artifact registry',keywords:['sprint']},
 {id:'P12',seq:'12',name:'Final Handoff Compressor',type:'CLOSEOUT',class:'standard',useWhen:'Close out completed work cleanly',sprintRole:'closer',proofGate:'handoff proof',copyContent:'compress the final state',keywords:['handoff']},
 {id:'P20',seq:'20',name:'Opportunity Builder',type:'OPPORTUNITY',class:'standard',useWhen:'Turn opportunity into work',sprintRole:'planner',proofGate:'plan proof',copyContent:'the final response names artifact paths',keywords:['opportunity']}
];
var artifact=filterPromptsForQuery(prompts,'artifact').map(function(p){return p.id});
var close=filterPromptsForQuery(prompts,'close').map(function(p){return p.id});
process.stdout.write(JSON.stringify({artifact:artifact,close:close}));
'''
        completed = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        result = json.loads(completed.stdout)
        self.assertEqual(result["artifact"][0], "P56")
        self.assertNotIn("P07", result["artifact"], "copyContent-only artifact noise must be suppressed")
        self.assertNotIn("P20", result["artifact"], "copyContent-only artifact noise must be suppressed")
        self.assertIn("P12", result["close"], "partial close must resolve closeout synonym and metadata")

    def test_favorites_persist_and_are_promoted_without_duplication(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "promptKit.favoritePromptIds.v1",
            "window.localStorage.getItem(FAVORITES_STORAGE_KEY)",
            "window.localStorage.setItem(FAVORITES_STORAGE_KEY",
            "favBtn.className='prompt-favorite-btn'",
            "favBtn.setAttribute('aria-pressed'",
        ):
            self.assertIn(marker, js)
        start = js.index("function promptSequenceValue")
        end = js.index("function renderSections")
        helpers = js[start:end]
        script = r'''
var SECTIONS=[
 {name:'Foundation',types:['SETUP'],glow:'#64748b'},
 {name:'Build & Repair',types:['BUILD'],glow:'#22c55e'}
];
var favoritePromptIds={P10:true};
function isFavoritePrompt(id){return favoritePromptIds[String(id||'').toUpperCase()]===true}
''' + helpers + r'''
var groups=groupPromptsBySection([
 {id:'P02',seq:'2',type:'SETUP'},
 {id:'P10',seq:'10',type:'BUILD'},
 {id:'P03',seq:'3',type:'BUILD'}
]);
process.stdout.write(JSON.stringify(groups.map(function(g){return {name:g.name,ids:g.prompts.map(function(p){return p.id})}})));
'''
        completed = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        groups = json.loads(completed.stdout)
        self.assertEqual(groups[0], {"name": "Favorites", "ids": ["P10"]})
        flattened = [prompt_id for group in groups for prompt_id in group["ids"]]
        self.assertEqual(flattened.count("P10"), 1)

    def test_generated_site_contains_exact_behavior_source(self) -> None:
        js = JS.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn(js, deployed)


if __name__ == "__main__":
    unittest.main()
