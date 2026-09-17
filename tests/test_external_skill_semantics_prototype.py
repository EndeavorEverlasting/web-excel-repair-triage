from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import prototype_external_skill_semantics as prototype  # noqa: E402


FIXTURE = """---
name: task-isolation
description: >
  Keep independent work isolated and current.
---

# Task Isolation

Every task must use its own worktree from the latest origin/main. Never reuse another agent's branch.

## Steps

1. Fetch the current default branch before creating the lane.
2. Check open PR changed files and stop on a collision.
3. Install dependencies fresh inside the worktree.

```bash
# Code examples are not semantic directives.
echo "never parse me as a directive"
```

## Remember

- Resolve lockfile conflicts by regenerating,
  never by hand-merging them when regeneration is canonical.
- Cleanup after merge and remove the disposable worktree.
"""


def identity(sha: str = "a" * 40, path: str = "task-isolation/SKILL.md") -> prototype.ResourceIdentity:
    return prototype.ResourceIdentity(
        source_id="fixture-skills",
        resource_id="fixture-skills:task-isolation",
        repository="fixture/skills",
        source_sha=sha,
        path=path,
    )


def pinned_fixture() -> prototype.PinnedBody:
    digest = hashlib.sha256(FIXTURE.encode()).hexdigest()
    return prototype.verify_body(
        identity=identity(),
        body=FIXTURE,
        expected_body_sha256=digest,
        acquisition="verified_fixture",
    )


class ExternalSkillSemanticPrototypeTests(unittest.TestCase):
    def test_success_stack_extracts_provenance_rich_directive_candidates(self) -> None:
        receipt = prototype.build_receipt(pinned_fixture())
        self.assertEqual(receipt["schema_version"], prototype.SCHEMA_VERSION)
        self.assertEqual(receipt["document"]["name"], "task-isolation")
        self.assertEqual(receipt["source"]["body_sha256"], hashlib.sha256(FIXTURE.encode()).hexdigest())
        self.assertEqual(receipt["source"]["acquisition"], "verified_fixture")
        directives = receipt["directive_candidates"]
        self.assertGreaterEqual(len(directives), 6)
        self.assertEqual([row["candidate_id"] for row in directives], [f"D{i:03d}" for i in range(1, len(directives) + 1)])
        self.assertTrue(any("isolation" in row["signals"] for row in directives))
        self.assertTrue(any("freshness" in row["signals"] for row in directives))
        self.assertTrue(any("collision" in row["signals"] for row in directives))
        self.assertTrue(any("dependency" in row["signals"] for row in directives))
        self.assertTrue(any("cleanup" in row["signals"] for row in directives))
        self.assertFalse(any("parse me" in row["text"] for row in directives))
        self.assertTrue(all(row["line_start"] <= row["line_end"] for row in directives))
        self.assertIn("lexical hints", receipt["proof_ceiling"])

    def test_multiline_list_item_remains_one_candidate(self) -> None:
        _, directives = prototype.extract_directive_candidates(FIXTURE)
        lockfile = [row for row in directives if "lockfile conflicts" in row["text"]]
        self.assertEqual(len(lockfile), 1)
        self.assertIn("never by hand-merging", lockfile[0]["text"])
        self.assertEqual(lockfile[0]["structure"], "list_item")
        self.assertGreater(lockfile[0]["line_end"], lockfile[0]["line_start"])

    def test_markdown_reference_table_is_not_flattened_into_directive(self) -> None:
        body = """# Platform\n\n| OS | Requirement |\n|---|---|\n| Linux | Must use DISPLAY |\n| Windows | Verify capture source |\n\nAlways verify the selected runtime.\n"""
        _, directives = prototype.extract_directive_candidates(body)
        self.assertEqual(len(directives), 1)
        self.assertEqual(directives[0]["text"], "Always verify the selected runtime.")
        self.assertNotIn("Linux", directives[0]["text"])

    def test_tilde_fenced_code_is_not_extracted(self) -> None:
        body = """# Tilde fence\n\n~~~bash\n# Never treat this as policy.\necho verify\n~~~\n\nAlways verify the real result.\n"""
        _, directives = prototype.extract_directive_candidates(body)
        self.assertEqual([row["text"] for row in directives], ["Always verify the real result."])

    def test_descriptive_list_items_are_not_directives(self) -> None:
        body = """# Inputs\n\n- PR number (optional).\n- Target platform and repository name.\n- Always verify the exact head before review.\n"""
        _, directives = prototype.extract_directive_candidates(body)
        self.assertEqual(len(directives), 1)
        self.assertEqual(directives[0]["text"], "Always verify the exact head before review.")

    def test_failure_stack_rejects_stale_body_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "body sha256 mismatch"):
            prototype.verify_body(
                identity=identity("b" * 40),
                body=FIXTURE,
                expected_body_sha256="0" * 64,
                acquisition="verified_fixture",
            )

    def test_pinned_body_rejects_self_inconsistent_digest(self) -> None:
        with self.assertRaisesRegex(ValueError, "digest does not match body"):
            prototype.PinnedBody(
                identity=identity(),
                body=FIXTURE,
                body_sha256="0" * 64,
                acquisition="fixture",
            )

    def test_pinned_url_must_match_repository_sha_and_path_exactly(self) -> None:
        ident = identity("c" * 40, "task/SKILL.md")
        good = f"https://raw.githubusercontent.com/fixture/skills/{ident.source_sha}/task/SKILL.md"
        prototype.validate_pinned_raw_url(good, ident)
        with self.assertRaisesRegex(ValueError, "exact raw.githubusercontent.com"):
            prototype.validate_pinned_raw_url(
                "https://raw.githubusercontent.com/fixture/skills/main/task/SKILL.md",
                ident,
            )

    def test_resource_identity_rejects_movable_or_escaping_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "40-character Git SHA"):
            identity("main")
        with self.assertRaisesRegex(ValueError, "relative repository path"):
            identity("d" * 40, "../SKILL.md")

    def test_empty_semantic_result_fails_closed(self) -> None:
        body = "# Empty\n\nDescriptive text without policy language.\n"
        pinned = prototype.verify_body(
            identity=identity("e" * 40, "empty/SKILL.md"),
            body=body,
            expected_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
            acquisition="verified_fixture",
        )
        with self.assertRaisesRegex(ValueError, "no directive candidates"):
            prototype.build_receipt(pinned)

    def test_unterminated_front_matter_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unterminated front matter"):
            prototype.extract_directive_candidates("---\nname: broken\n# Heading\n")


if __name__ == "__main__":
    unittest.main()
