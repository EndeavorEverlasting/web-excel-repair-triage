from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
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
                "sequential_with_gaps",
                "anchors_on_visible_categories",
                "acquisition_discoverability",
            },
        )

    def test_category_and_type_controls_are_initialized(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("All Categories", js)
        self.assertIn("All Types", js)
        self.assertIn("renderSections();", js)
        self.assertIn("renderTypes();", js)
        self.assertIn("aria-label','Prompt categories", js)
        self.assertIn("aria-label','Prompt types", js)

    def test_render_groups_once_and_preserves_category_heading_when_filtered(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function groupPromptsBySection(prompts)", js)
        self.assertIn("var groups=groupPromptsBySection(f);", js)
        self.assertIn("groups.forEach(function(group)", js)
        self.assertIn("appendSectionDivider(grid,group);", js)
        self.assertIn("group.prompts.forEach(function(p){appendPromptCard(grid,p)})", js)
        self.assertNotIn("sectionName!==lastSection&&!activeSection&&!activeType", js)
        self.assertIn("if(activeSection){var secTypes=[];", js)
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
function isFavoritePrompt(id){return false;}
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
