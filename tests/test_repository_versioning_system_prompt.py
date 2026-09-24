import unittest

from scripts.build_prompt_kit_registry import load_prompt_registry


class RepositoryVersioningSystemPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = load_prompt_registry()
        cls.prompt = next(p for p in cls.prompts if p.get("name") == "Repository Versioning System Establisher")
        cls.p15 = next(p for p in cls.prompts if p.get("id") == "P15")

    def test_helper_allocated_identity_and_downstream_owner_remain_distinct(self):
        self.assertEqual(self.prompt["id"], 'P130')
        self.assertNotEqual(self.prompt["id"], self.p15["id"])
        p15_text = " ".join(str(self.p15.get(k, "")) for k in ("name", "sprintRole", "useWhen", "copyContent")).lower()
        self.assertIn("release", p15_text)
        self.assertIn("merge", p15_text)

    def test_versioning_owner_establishes_policy_before_release_execution(self):
        text = self.prompt["copyContent"].lower()
        required = [
            "one canonical version authority",
            "exact commit/artifact identity",
            "semver",
            "calver",
            "do not choose semver merely because it is familiar",
            "change-to-version matrix",
            "synchronized version surface",
            "changelog",
            "do not rename old tags",
            "rollback",
            "deprecation",
            "idempotent version calculation",
            "released version would be reused",
            "ordinary merge/release execution is downstream work",
        ]
        for phrase in required:
            self.assertIn(phrase, text)

    def test_scheme_selection_preserves_schema_and_release_identity_boundaries(self):
        text = self.prompt["copyContent"].lower()
        self.assertIn("product release version", text)
        self.assertIn("schema/protocol version", text)
        self.assertIn("ui badge alone is never freshness proof", text)
        self.assertIn("do not claim a published/runtime release", text)


if __name__ == "__main__":
    unittest.main()
