from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class OperantProductIdentityTests(unittest.TestCase):
    def test_identity_contract_preserves_transition_boundary(self) -> None:
        payload = json.loads((ROOT / "harness/contracts/operant-product-identity.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "operant-product-identity/v1")
        self.assertEqual(payload["product_name"], "Operant")
        self.assertEqual(payload["product_version"], "0.1.0")
        self.assertEqual(payload["authority"]["target_repository"], "UnderDeskDev/Operant")
        self.assertEqual(payload["authority"]["target_repository_state"], "not-created-or-unproven")
        self.assertTrue(payload["compatibility"]["internal_path_renames_deferred"])
        self.assertIn("web/prompt-kit/index.html", payload["compatibility"]["preserve_paths"])
        self.assertIn("Prompt Kit", payload["legacy_identity"]["names"])

    def test_visible_brand_is_operant_without_renaming_compatibility_paths(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("<title>Operant 0.1</title>", html)
        self.assertIn("Operant <span>0.1</span>", html)
        self.assertIn("Capabilities · Skills · Implementations · Evidence", html)
        self.assertNotIn("<title>AI Harness Prompt Kit v40</title>", html)
        self.assertTrue((ROOT / "web/prompt-kit").is_dir())

    def test_governance_and_access_surface_name_operant(self) -> None:
        governance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        access = (ROOT / "PROMPT_KIT_ACCESS.md").read_text(encoding="utf-8")
        self.assertIn("**Operant** is the operator-approved product identity", governance)
        self.assertIn("`UnderDeskDev/Operant`", governance)
        self.assertIn("legacy `prompt-kit` paths", governance)
        self.assertTrue(access.startswith("# Get Operant"))
        self.assertIn("compatibility paths", access)


if __name__ == "__main__":
    unittest.main()
