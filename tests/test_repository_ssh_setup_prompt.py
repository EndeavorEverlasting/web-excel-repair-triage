import unittest
from scripts.build_prompt_kit_registry import load_prompt_registry

class RepositorySshSetupPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts=load_prompt_registry()
        cls.prompt=next(p for p in cls.prompts if p.get("name")=="Repository SSH Setup + Usage Completer")
        cls.p55=next(p for p in cls.prompts if p.get("id")=="P55")
        cls.p61=next(p for p in cls.prompts if p.get("id")=="P61")
    def test_fresh_identity_and_owner_boundaries(self):
        self.assertEqual(self.prompt["id"], 'P139')
        self.assertNotIn(self.prompt["id"], {"P55","P61","P131","P138"})
        self.assertEqual(self.p55["name"], "GitHub CLI Repository Bootstrapper")
        self.assertEqual(self.p61["name"], "Existing Repository Clone + Working-Directory Bootstrapper")
    def test_setup_proof_and_usage_contract(self):
        t=self.prompt["copyContent"].lower()
        for s in ["public key", "private key", "batchmode=yes", "connecttimeout=8", "git ls-remote --heads origin", "git push --dry-run", "git remote set-url origin", "how to use this ssh setup", "git clone <verified-ssh-url>", "blocked_user_only", "blocked_permission", "blocked_network_policy", "do not blindly answer yes", "git bash/msys2"]:
            self.assertIn(s,t)
        self.assertLess(t.index("6. prove the transport fail-fast"), t.index("9. how to use this ssh setup"))
    def test_secret_and_mutation_boundaries(self):
        t=self.prompt["copyContent"].lower()
        for s in ["never ask the operator to send a private key or passphrase in chat", "do not make a global git/ssh-policy change", "preserve every unrelated remote", "never overwrite an existing key file", "do not delete old keys", "do not create a remote branch, tag, commit, or force update merely to test credentials", "distinguish authentication from authorization"]:
            self.assertIn(s,t)

if __name__ == "__main__":
    unittest.main()
