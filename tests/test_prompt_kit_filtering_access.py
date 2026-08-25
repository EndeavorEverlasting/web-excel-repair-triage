from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
ACCESS = ROOT / "PROMPT_KIT_ACCESS.md"
WEB_README = ROOT / "web" / "README.md"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-filtering.v1.json"
ACQUIRE_CMD = ROOT / "Acquire-Latest-PromptKit.cmd"
ACQUIRE_PS1 = ROOT / "scripts" / "Acquire-LatestPromptKit.ps1"


class PromptKitFilteringAccessTests(unittest.TestCase):
    def test_filtering_contract_has_required_requirements(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-filtering-contract/v1")
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            {
                "unique_categories",
                "single_category_scope",
                "unique_type_filters",
                "progressive_type_disclosure",
                "all_view_full_reset",
                "sequential_with_gaps",
                "anchors_on_visible_categories",
                "acquisition_discoverability",
            },
        )
        expected = {item["id"]: item["expected"] for item in payload["requirements"]}
        self.assertIn("complete prompt stream", expected["all_view_full_reset"])
        self.assertIn("Favorites then All", expected["all_view_full_reset"])
        self.assertIn("complete visible prompt-card stream", expected["sequential_with_gaps"])
        self.assertIn("at most once", expected["unique_categories"])
        self.assertIn("compact instructional hint", expected["progressive_type_disclosure"])
        self.assertIn("only subcategories available in that scope", expected["progressive_type_disclosure"])

    def test_category_and_type_controls_are_initialized(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("All Categories", js)
        self.assertIn("All Subcategories", js)
        self.assertIn("renderSections();", js)
        self.assertIn("renderTypes();", js)
        self.assertIn("aria-label','Prompt categories", js)
        self.assertIn("aria-label','Prompt subcategories", js)

    def test_type_subcategories_are_progressively_scoped_by_category(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("Select a category above to browse subcategories.", js)
        self.assertIn("Subcategories · ", js)
        self.assertIn("All Subcategories", js)
        self.assertIn("activeSection=sn==='__all__'?null:sn;activeType=null", js)
        self.assertIn("renderTypes();render();return", js)

        start = js.index("function typeFilterScopePrompts")
        end = js.index("function renderSections", start)
        helper = js[start:end]
        script = """
var SECTIONS=[
 {name:'Foundation',types:['SETUP','HARVEST']},
 {name:'Build & Repair',types:['BUILD','REPAIR','BUILD + ARTIFACT']}
];
function isFavoritePrompt(id){return id==='P04'}
""" + helper + r"""
var prompts=[
 {id:'P01',category:'standard',type:'SETUP'},
 {id:'P02',category:'standard',type:'BUILD'},
 {id:'P03',category:'gnhf',type:'REPAIR'},
 {id:'P04',category:'standard',type:'BUILD + ARTIFACT'},
 {id:'P05',category:'standard',type:'HARVEST'}
];
var result={
  all:typeFilterScopePrompts(prompts,'all',null).map(function(p){return p.id}),
  build:typeFilterScopePrompts(prompts,'all','Build & Repair').map(function(p){return p.id}),
  standardBuild:typeFilterScopePrompts(prompts,'standard','Build & Repair').map(function(p){return p.id}),
  favorites:typeFilterScopePrompts(prompts,'all','__favorites__').map(function(p){return p.id})
};
process.stdout.write(JSON.stringify(result));
"""
        completed = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["all"], [])
        self.assertEqual(result["build"], ["P02", "P03", "P04"])
        self.assertEqual(result["standardBuild"], ["P02", "P04"])
        self.assertEqual(result["favorites"], ["P04"])

    def test_all_view_is_an_atomic_reset_after_favorites(self) -> None:
        js = JS.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")

        start = js.index("function resetPromptKitView()")
        end = js.index("\n\nfunction showAddPrompt", start)
        reset = js[start:end]
        for marker in (
            "activeCat='all'",
            "activeSection=null",
            "activeType=null",
            "activeColor=null",
            "collapsedSections={}",
            "search.value=''",
            "syncLibraryTabs()",
            "renderSections()",
            "renderTypes()",
            "render()",
        ):
            self.assertIn(marker, reset)

        favorites = polish[polish.index("function activateFavoritesView()") : polish.index("function ensureCompactBrowsingControls()")]
        self.assertIn("activeSection='__favorites__'", favorites)

        all_view = polish[polish.index("function activateAllPromptsView()") : polish.index("function activateFavoritesView()")]
        self.assertIn("resetPromptKitView();", all_view)

        switches = polish[polish.index("function installCompactBrowsingViewSwitches()") : polish.index("function installCompactBrowsingHotkeys()")]
        self.assertIn(".cat-tab[data-cat=\"all\"]", switches)
        self.assertIn("e.stopImmediatePropagation();", switches)
        self.assertIn("activateAllPromptsView();", switches)

        hotkeys = polish[polish.index("function installCompactBrowsingHotkeys()") : polish.index("window.appendPromptCard")]
        self.assertIn("var key=String(e.key||'').toLowerCase();", hotkeys)
        key_all = hotkeys[hotkeys.index("if(key==='a')") : hotkeys.index("if(key==='s')")]
        self.assertIn("e.preventDefault();", key_all)
        self.assertIn("e.stopImmediatePropagation();", key_all)
        self.assertIn("activateAllPromptsView();", key_all)
        key_favorites = hotkeys[hotkeys.index("if(key==='v')") : hotkeys.index("if(key==='d')")]
        self.assertIn("activateFavoritesView();", key_favorites)

        self.assertIn("installCompactBrowsingViewSwitches();", polish)
        self.assertIn("installCompactBrowsingHotkeys();", polish)

    def test_render_uses_unique_category_metadata_without_reordering_cards(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function groupPromptsBySection(prompts)", js)
        self.assertIn("var groups=groupPromptsBySection(orderedPrompts),groupByName={},renderedSections={};", js)
        self.assertIn("groups.forEach(function(group){groupByName[group.name]=group});", js)
        self.assertIn("orderedPrompts.forEach(function(p)", js)
        self.assertIn("if(!renderedSections[sectionName]){appendSectionDivider(grid,group);renderedSections[sectionName]=true}", js)
        self.assertIn("appendPromptCard(grid,p);visiblePromptIndex++;", js)
        self.assertNotIn("sectionName!==lastSection&&!activeSection&&!activeType", js)
        self.assertIn("divider.setAttribute('data-category',group.name)", js)

    def test_grouping_is_unique_and_numeric_for_noncontiguous_prompt_ids(self) -> None:
        js = JS.read_text(encoding="utf-8")
        start = js.index("function promptSequenceValue")
        end = js.index("function renderSections")
        helpers = js[start:end]
        script = """
var SECTIONS=[
 {name:'Foundation',types:['SETUP'],glow:'#1'},
 {name:'Build & Repair',types:['BUILD','REPAIR'],glow:'#2'},
 {name:'Validate & Protect',types:['VALIDATE'],glow:'#3'}
];
""" + helpers + r"""
var prompts=[
 {id:'P10',seq:'10',type:'BUILD'},
 {id:'P02',seq:'02',type:'SETUP'},
 {id:'P05',seq:'05',type:'BUILD'},
 {id:'P12',seq:'12',type:'SETUP'},
 {id:'P07',seq:'07',type:'VALIDATE'},
 {id:'P03',seq:'03',type:'BUILD'}
];
var groups=groupPromptsBySection(prompts);
process.stdout.write(JSON.stringify(groups.map(function(g){
  return {name:g.name,ids:g.prompts.map(function(p){return p.id})};
})));
"""
        completed = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        groups = json.loads(completed.stdout)
        self.assertEqual(
            groups,
            [
                {"name": "Foundation", "ids": ["P02", "P12"]},
                {"name": "Build & Repair", "ids": ["P03", "P05", "P10"]},
                {"name": "Validate & Protect", "ids": ["P07"]},
            ],
        )
        names = [item["name"] for item in groups]
        self.assertEqual(len(names), len(set(names)))
        for group in groups:
            seqs = [int(item[1:]) for item in group["ids"]]
            self.assertEqual(seqs, sorted(seqs))

    def test_visible_category_divider_keeps_top_and_bottom_anchors(self) -> None:
        js = JS.read_text(encoding="utf-8")
        start = js.index("function appendSectionDivider")
        end = js.index("function appendPromptCard")
        divider = js[start:end]
        self.assertIn('href="#page-top"', divider)
        self.assertIn('href="#page-bottom"', divider)
        self.assertLess(divider.index("page-jump-top"), divider.index("sd-label"))
        self.assertGreater(divider.index("page-jump-bottom"), divider.index("sd-label"))

    def test_access_guide_exposes_all_supported_acquisition_routes(self) -> None:
        guide = ACCESS.read_text(encoding="utf-8")
        for marker in (
            "web/prompt-kit/index.html",
            "Acquire-Latest-PromptKit.cmd",
            "git pull --ff-only origin main",
            "git clone --branch main --single-branch",
            "Download ZIP",
            "prompt-kit-current-preview",
            "Build-PromptKitWebsite.cmd",
            "scripts\\build_prompt_kit_registry.py",
        ):
            self.assertIn(marker, guide)
        self.assertNotIn("feat/prompt-kit", guide)

    def test_existing_acquisition_launcher_targets_canonical_main_and_opens_site(self) -> None:
        cmd = ACQUIRE_CMD.read_text(encoding="utf-8")
        ps1 = ACQUIRE_PS1.read_text(encoding="utf-8")
        self.assertIn("/main/scripts/Acquire-LatestPromptKit.ps1", cmd)
        self.assertIn("$DefaultBranch = 'main'", ps1)
        self.assertIn("'clone', '--branch', $DefaultBranch, '--single-branch'", ps1)
        self.assertIn("'merge', '--ff-only'", ps1)
        self.assertIn("'web\\prompt-kit\\index.html'", ps1)
        self.assertIn("Open Prompt Kit website", ps1)

    def test_web_readme_points_to_canonical_access_guide_and_filter_contract(self) -> None:
        text = WEB_README.read_text(encoding="utf-8")
        self.assertIn("../PROMPT_KIT_ACCESS.md", text)
        self.assertIn("All Categories", text)
        self.assertIn("All Types", text)
        self.assertIn("numeric prompt sequence", text)
        self.assertIn("Top", text)
        self.assertIn("Bottom", text)


if __name__ == "__main__":
    unittest.main()
