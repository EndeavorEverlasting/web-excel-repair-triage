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


class ExternalSkillSemanticPrototypeTests(unittest.TestCase):
    def test_success_stack_extracts_provenance_rich_directive_candidates(self) -> None:
        receipt = prototype.build_receipt(
            source_id="fixture-skills",
            resource_id="fixture-skills:task-isolation",
            repository="fixture/skills",
            source_sha="a" * 40,
            path="task-isolation/SKILL.md",
            body=FIXTURE,
        )
        self.assertEqual(receipt["schema_version"], prototype.SCHEMA_VERSION)
        self.assertEqual(receipt["document"]["name"], "task-isolation")
        self.assertEqual(receipt["source"]["body_sha256"], hashlib.sha256(FIXTURE.encode()).hexdigest())
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

    def test_failure_stack_rejects_stale_body_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "body sha256 mismatch"):
            prototype.build_receipt(
                source_id="fixture-skills",
                resource_id="fixture-skills:task-isolation",
                repository="fixture/skills",
                source_sha="b" * 40,
                path="task-isolation/SKILL.md",
                body=FIXTURE,
                expected_body_sha256="0" * 64,
            )

    def test_pinned_url_must_match_repository_sha_and_path_exactly(self) -> None:
        sha = "c" * 40
        good = f"https://raw.githubusercontent.com/fixture/skills/{sha}/task/SKILL.md"
        prototype.validate_pinned_raw_url(good, repository="fixture/skills", source_sha=sha, path="task/SKILL.md")
        with self.assertRaisesRegex(ValueError, "exact raw.githubusercontent.com"):
            prototype.validate_pinned_raw_url(
                "https://raw.githubusercontent.com/fixture/skills/main/task/SKILL.md",
                repository="fixture/skills",
                source_sha=sha,
                path="task/SKILL.md",
            )

    def test_empty_semantic_result_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "no directive candidates"):
            prototype.build_receipt(
                source_id="fixture-skills",
                resource_id="fixture-skills:empty",
                repository="fixture/skills",
                source_sha="d" * 40,
                path="empty/SKILL.md",
                body="# Empty\n\nDescriptive text without policy language.\n",
            )

    def test_unterminated_front_matter_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unterminated front matter"):
            prototype.extract_directive_candidates("---\nname: broken\n# Heading\n")


if __name__ == "__main__":
    unittest.main()
