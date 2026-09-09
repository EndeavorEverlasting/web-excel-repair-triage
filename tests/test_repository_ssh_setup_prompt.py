import unittest

from scripts.build_prompt_kit_registry import load_prompt_registry


class RepositorySshSetupPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = load_prompt_registry()
        cls.prompt = next(p for p in cls.prompts if p.get("name") == 'Repository SSH Setup + Usage Completer')
        cls.p55 = next(p for p in cls.prompts if p.get("id") == "P55")
        cls.p61 = next(p for p in cls.prompts if p.get("id") == "P61")

    def test_helper_allocated_distinct_identity_without_stealing_adjacent_owners(self):
        self.assertEqual(self.prompt["id"], 'P131')
        self.assertEqual(self.p55["name"], "GitHub CLI Repository Bootstrapper")
        self.assertEqual(self.p61["name"], "Existing Repository Clone + Working-Directory Bootstrapper")
        self.assertNotEqual(self.prompt["id"], self.p55["id"])
        self.assertNotEqual(self.prompt["id"], self.p61["id"])

    def test_ssh_owner_completes_transport_before_teaching_usage(self):
        lower = self.prompt["copyContent"].lower()
        required = [
            "complete this repository's ssh setup",
            "public key",
            "private key",
            "batchmode=yes",
            "connecttimeout=8",
            "git ls-remote --heads origin",
            "git push --dry-run",
            "git remote set-url origin",
            "how to use this ssh setup",
            "git clone <verified-ssh-url>",
            "blocked_user_only",
            "blocked_permission",
            "blocked_network_policy",
            "do not blindly answer `yes`",
            "git bash/msys2",
        ]
        for phrase in required:
            self.assertIn(phrase, lower)
        self.assertLess(lower.index("prove the transport fail-fast"), lower.index("how to use this ssh setup"))

    def test_secret_scope_and_safe_write_boundaries(self):
        lower = self.prompt["copyContent"].lower()
        self.assertIn("never ask the operator to send a private key or passphrase in chat", lower)
        self.assertIn("do not make a global git/ssh-policy change", lower)
        self.assertIn("preserve every unrelated remote", lower)
        self.assertIn("never overwrite an existing key file", lower)
        self.assertIn("do not delete old keys", lower)
        self.assertIn("non-mutating proof", lower)
        self.assertIn("do not create a remote branch, tag, commit, or force update merely to test credentials", lower)
        self.assertIn("distinguish authentication success from authorization", lower)
        self.assertIn("read-only intent", lower)
        self.assertIn("read-write intent", lower)


if __name__ == "__main__":
    unittest.main()
