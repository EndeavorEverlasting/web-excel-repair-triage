from __future__ import annotations

import unittest

import build_prompt_kit
from scripts import build_prompt_kit_registry, prompt_registry_ops


class P55RepositoryBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }
        cls.p55 = cls.prompts["P55"]

    def test_p55_identity_is_context_grounded_and_provider_neutral(self) -> None:
        self.assertEqual(self.p55["name"], "Context-Grounded Repository Bootstrapper")
        self.assertEqual(
            self.p55["class"],
            "STANDARD AI / CONTEXT-GROUNDED REPOSITORY CREATION",
        )
        self.assertIn("Git-compatible provider", self.p55["sprintRole"])
        self.assertIn("incomplete", self.p55["useWhen"])
        self.assertIn("repository namespace", self.p55["keywords"])
        self.assertIn("Entire repository", self.p55["keywords"])

    def test_p55_completes_missing_parameters_under_explicit_policy(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "PARAMETER COMPLETION POLICY",
            "ASK",
            "INFER",
            "HYBRID",
            "HYBRID is the default",
            "Do not ask the operator to repeat information that can be recovered",
            "one compact question",
            "Freeze the manifest before repository mutation",
        ):
            self.assertIn(phrase, content)

    def test_p55_owns_namespace_screening_without_claiming_legal_clearance(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "NAMESPACE GATE",
            "exact-name collision",
            "root-name collision",
            "adjacent software/AI/developer-tool collision",
            "product-vs-subsystem naming level",
            "screening, not trademark or legal clearance",
            "existing canonical repository",
        ):
            self.assertIn(phrase, content)

    def test_p55_models_repository_provider_as_adapter(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "Repository provider: AUTO | GITHUB | ENTIRE | OTHER",
            "Provider adapter: AUTO | CLI | API | CONNECTOR | NATIVE_GIT",
            "GitHub CLI is one adapter",
            "do not invent provider syntax from memory",
            "current provider help, documentation, connector schema, or repository-owned adapter",
            "ENTIRE",
            "REMOTE_ONLY",
            "LOCAL_ONLY",
        ):
            self.assertIn(phrase, content)

    def test_p55_preserves_visibility_and_collision_safety(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "Never default to PUBLIC",
            "EXISTS_AND_MATCHES",
            "EXISTS_BUT_CONFLICTS",
            "CONFIRMED_NOT_FOUND",
            "UNKNOWN_AUTH",
            "UNKNOWN_PERMISSION",
            "UNKNOWN_NETWORK",
            "UNKNOWN_PROVIDER",
            "Do not interpret authentication, permission, or network failure as proof that a namespace is free",
        ):
            self.assertIn(phrase, content)

    def test_registry_edit_helper_can_keep_prompt_metadata_atomic(self) -> None:
        required = {
            "name",
            "class",
            "sprintRole",
            "useWhen",
            "inspectFirst",
            "expectedOutput",
            "proofGate",
            "nextStep",
            "copyContent",
            "keywords",
        }
        self.assertTrue(required.issubset(prompt_registry_ops.EDITABLE_PROMPT_FIELDS))
        self.assertEqual(
            prompt_registry_ops.SEMANTIC_EDITABLE_PROMPT_FIELDS,
            {"name", "copyContent", "sprintRole", "useWhen"},
        )
        self.assertTrue(
            {"class", "inspectFirst", "expectedOutput", "nextStep", "proofGate", "keywords"}.issubset(
                prompt_registry_ops.METADATA_EDITABLE_PROMPT_FIELDS
            )
        )

    def test_metadata_only_edit_cannot_fake_semantic_lifecycle_progress(self) -> None:
        with self.assertRaisesRegex(SystemExit, "cannot independently advance"):
            prompt_registry_ops.edit_prompt(
                "P55",
                {"keywords": ["repository creation"]},
                "NO_CAPABILITY_CHANGE",
                ["tests/test_p55_repository_bootstrap.py"],
                "metadata-only negative control",
                dry_run=True,
            )

    def test_edit_rejects_non_string_keyword_metadata(self) -> None:
        with self.assertRaisesRegex(SystemExit, "only non-empty strings"):
            prompt_registry_ops.edit_prompt(
                "P55",
                {
                    "name": self.p55["name"] + " test-only candidate",
                    "keywords": [None],
                },
                "NO_CAPABILITY_CHANGE",
                ["tests/test_p55_repository_bootstrap.py"],
                "invalid keyword type negative control",
                dry_run=True,
            )

    def test_discovery_synonyms_route_repository_creation_to_p55(self) -> None:
        for term in (
            "create repository",
            "create repo",
            "new repository",
            "repository bootstrap",
            "name repository",
            "repository namespace",
            "git provider",
            "publish repository",
        ):
            self.assertEqual(build_prompt_kit.SYNONYMS[term], "P55")


    def test_manifest_status_vocabulary_is_consistent(self) -> None:
        content = self.p55["copyContent"]
        self.assertIn("Status is exactly RESOLVED, INFERRED, or USER_ONLY.", content)
        self.assertIn("Unsupported or unresolved manifest fields use USER_ONLY.", content)
        self.assertNotIn("Unsupported fields remain UNKNOWN or USER_ONLY.", content)

    def test_pre_mutation_execution_contract_is_required(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "PRE-MUTATION REPOSITORY EXECUTION CONTRACT",
            "lane and mission",
            "owned scope and forbidden scope",
            "expected artifacts",
            "validation order",
            "mutation authority",
            "writer-isolation and collision posture",
            "One writer owns each branch/worktree",
            "Repository mutation is blocked",
        ):
            self.assertIn(phrase, content)

    def test_continuation_is_execution_surface_aware(self) -> None:
        step = self.p55["nextStep"]
        self.assertIn("verified local root", step)
        self.assertIn("REMOTE_ONLY", step)
        self.assertIn("clone or adopt the verified remote", step)
        self.assertIn("LOCAL_ONLY", step)
        self.assertIn("remote-provider/auth gate", step)



if __name__ == "__main__":
    unittest.main()
