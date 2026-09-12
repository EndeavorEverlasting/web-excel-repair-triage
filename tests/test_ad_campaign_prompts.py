from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from scripts import build_ad_campaign_pack, build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]


class AdCampaignPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "harness/ad-campaign/campaign.v1.json").read_text(encoding="utf-8"))
        cls.all = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.prompts = [p for p in cls.all if p.get("profile") == "ad-campaign"]
        cls.by_name = {p["name"]: p for p in cls.prompts}

    def test_six_distinct_helper_identities_and_stage_owners(self):
        self.assertEqual(set(self.by_name), set(self.contract["prompt_names"]))
        self.assertEqual(len(self.prompts), 6)
        for field in ("id", "seq", "name", "useWhen", "expectedOutput"):
            self.assertEqual(len({p[field] for p in self.prompts}), 6, field)
        ids = [int(self.by_name[name]["id"][1:]) for name in self.contract["prompt_names"]]
        self.assertEqual(ids, sorted(ids))
        for prompt in self.prompts:
            self.assertEqual(prompt["copySheet"], prompt["id"] + "_COPY_SAFE")
            self.assertEqual(prompt["actionabilityPolicy"], build_prompt_kit_registry.load_actionability_policy()["policy_id"])

    def test_semantic_boundaries_survive_canonical_composition(self):
        for prompt in self.prompts:
            for phrase in ("A Git repository is not required", "Preparation does not authorize",
                           "Do not invent budgets", "Campaign approval applies to the exact version"):
                self.assertIn(phrase, prompt["copyContent"])
        expected = {
            "Ad Campaign Doctrine Builder": ("claims ledger", "brand", "Unsupported claims"),
            "Ad Campaign Harness Builder": ("harness/ad-campaign/campaign.v1.json", "python scripts/ad_campaign.py --help", "synthetic", "version"),
            "Ad Campaign Planner": ("percentage allocation totaling 100%", "comparison", "decision rule", "conversion lag"),
            "Ad Campaign Creative Executor": ("not synonym swaps", "claim keys", "not a rendered asset", "Do not silently alter a live page"),
            "Ad Campaign Launch Reviewer": ("Pending platform review remains pending", "REVIEWED", "AUTHORIZED", "observed platform evidence supports LIVE"),
            "Ad Campaign Results Analyst": ("Zero or missing denominators", "INCONCLUSIVE", "attribution", "not profit", "No data means"),
        }
        for name, phrases in expected.items():
            for phrase in phrases:
                self.assertIn(phrase, self.by_name[name]["copyContent"], (name, phrase))

    def test_named_pack_selects_exactly_campaign_domain(self):
        script = """
const fs=require('fs');const api=require('./docs/prompt-kit-profiles.js');
const rows=JSON.parse(fs.readFileSync(0,'utf8'));
const pack=api.PREDEFINED_PACKS.AD_CAMPAIGNS;
console.log(JSON.stringify({label:pack.label,ids:rows.filter(api.compileRule(pack.rule)).map(p=>p.id)}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, input=json.dumps(self.all),
                                text=True, capture_output=True, check=True)
        proof = json.loads(result.stdout)
        self.assertEqual(proof["label"], "Ad Campaigns")
        self.assertEqual(set(proof["ids"]), {p["id"] for p in self.prompts})

    def test_search_and_guided_entrypoint_use_campaign_metadata(self):
        for prompt in self.prompts:
            self.assertIn("ad campaign", prompt["keywords"])
        guidance = (ROOT / "docs/prompt-kit-guided-recommendations.js").read_text(encoding="utf-8")
        self.assertIn("id:'ad-campaign'", guidance)
        self.assertIn("queries:['ad campaign doctrine','ad campaign planner','ad-campaign']", guidance)
        runtime = (ROOT / "docs/prompt-kit-management.js").read_text(encoding="utf-8")
        self.assertIn("badge:'Ad Campaigns'", runtime)
        self.assertIn("'ad-campaign'", runtime)

    def test_pack_is_derived_from_source_and_has_no_placeholder_ids(self):
        output, expected = build_ad_campaign_pack.render()
        self.assertEqual(output.read_text(encoding="utf-8"), expected)
        for prompt in self.prompts:
            self.assertIn(prompt["id"] + " — " + prompt["name"], expected)
        self.assertNotIn("P131-P136", expected)

    def test_domain_and_repository_routes_resolve(self):
        for field in ("doctrine", "router", "template", "validator", "prompt_pack", "prompt_pack_builder", "registry_path"):
            self.assertTrue((ROOT / self.contract[field]).is_file(), field)
        self.assertIn(self.contract["router"], (ROOT / "harness/CONTEXT.md").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "harness/manifest.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain_contracts"]["ad_campaign"]["contract"], "harness/ad-campaign/campaign.v1.json")


if __name__ == "__main__":
    unittest.main()
