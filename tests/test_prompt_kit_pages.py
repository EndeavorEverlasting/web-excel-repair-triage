from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
ACCESS_GUIDE = ROOT / "PROMPT_KIT_ACCESS.md"
PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"


class PromptKitPagesContractTests(unittest.TestCase):
    def test_pages_workflow_uses_canonical_builder_and_release_gate(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "name: Prompt Kit GitHub Pages",
            "branches: [main]",
            "workflow_dispatch:",
            "fetch-depth: 0",
            "git diff --check",
            "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
            'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/index.html"',
            'cp "$SITE_ROOT/index.html" "$SITE_ROOT/prompt-kit/index.html"',
            'cmp "$SITE_ROOT/index.html" web/prompt-kit/index.html',
            'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_pages_workflow_uses_github_pages_permissions_and_actions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "contents: read",
            "pages: write",
            "id-token: write",
            "name: github-pages",
            "actions/configure-pages@v5",
            "actions/upload-pages-artifact@v4",
            "actions/deploy-pages@v4",
            "if: github.event_name != 'pull_request'",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_access_guide_leads_with_public_mobile_surface(self):
        text = ACCESS_GUIDE.read_text(encoding="utf-8")
        self.assertIn(PUBLIC_URL, text)
        self.assertIn("## Phone, tablet, or any browser", text)
        self.assertIn("Add to Home Screen", text)
        self.assertIn("Settings", text)
        self.assertIn("Pages", text)
        self.assertIn("GitHub Actions", text)


if __name__ == "__main__":
    unittest.main()
