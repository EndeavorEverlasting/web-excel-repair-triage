from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/operant-versioning.yml"
PR_REQUEST_SCRIPT = ROOT / "scripts/operant_release_pr_request.py"


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


class OperantVersioningWorkflowTests(unittest.TestCase):
    def test_release_detection_uses_full_push_range(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('before="${{ github.event.before }}"', workflow)
        self.assertIn('git diff --quiet "$before" HEAD -- OPERANT_VERSION', workflow)
        self.assertNotIn("git diff --quiet HEAD^ HEAD -- OPERANT_VERSION", workflow)

    def test_multi_commit_rebase_style_push_detects_earlier_version_bump(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_git(root, "init").returncode, 0)
            self.assertEqual(run_git(root, "config", "user.name", "Operant Test").returncode, 0)
            self.assertEqual(
                run_git(root, "config", "user.email", "operant-test@example.invalid").returncode,
                0,
            )

            version_file = root / "OPERANT_VERSION"
            changelog = root / "OPERANT_CHANGELOG.md"
            version_file.write_text("0.5.0\n", encoding="utf-8")
            changelog.write_text("# Operant Changelog\n", encoding="utf-8")
            self.assertEqual(run_git(root, "add", ".").returncode, 0)
            self.assertEqual(run_git(root, "commit", "-m", "chore: baseline").returncode, 0)
            before = run_git(root, "rev-parse", "HEAD").stdout.strip()
            self.assertTrue(before)

            version_file.write_text("0.6.0\n", encoding="utf-8")
            self.assertEqual(run_git(root, "add", "OPERANT_VERSION").returncode, 0)
            self.assertEqual(
                run_git(root, "commit", "-m", "chore(operant): release v0.6.0").returncode,
                0,
            )

            changelog.write_text(
                "# Operant Changelog\n\n## 0.6.0\n\n- reconciled release notes\n",
                encoding="utf-8",
            )
            self.assertEqual(run_git(root, "add", "OPERANT_CHANGELOG.md").returncode, 0)
            self.assertEqual(
                run_git(root, "commit", "-m", "chore(operant): reconcile release notes").returncode,
                0,
            )

            last_commit_only = run_git(
                root,
                "diff",
                "--quiet",
                "HEAD^",
                "HEAD",
                "--",
                "OPERANT_VERSION",
            )
            full_integrated_range = run_git(
                root,
                "diff",
                "--quiet",
                before,
                "HEAD",
                "--",
                "OPERANT_VERSION",
            )

            self.assertEqual(
                last_commit_only.returncode,
                0,
                "the final commit intentionally does not touch OPERANT_VERSION",
            )
            self.assertEqual(
                full_integrated_range.returncode,
                1,
                "the full push range must detect the earlier OPERANT_VERSION bump",
            )

    def test_first_release_pr_creation_is_externalized_as_machine_readable_request(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("gh pr create", workflow)
        self.assertIn("python scripts/operant_release_pr_request.py", workflow)
        self.assertIn("Outputs/operant-release-pr-request.json", workflow)
        self.assertIn("actions/upload-artifact@v7", workflow)
        self.assertIn("GITHUB_STEP_SUMMARY", workflow)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            body_path = root / "body.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PR_REQUEST_SCRIPT),
                    "--version",
                    "0.6.1",
                    "--source-sha",
                    "abc123",
                    "--head",
                    "automation/operant-release-v0.6.1",
                    "--base",
                    "main",
                    "--candidate-branch",
                    "automation/operant-release-v0.6.1",
                    "--candidate-sha",
                    "candidate-create-sha",
                    "--candidate-tree-sha",
                    "candidate-create-tree",
                    "--output",
                    str(request_path),
                    "--body-output",
                    str(body_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "operant-release-pr-request/v2")
            self.assertEqual(payload["publication_owner"], "external-provider")
            self.assertEqual(payload["publication_mode"], "external-create")
            self.assertTrue(payload["requires_external_pr_creation"])
            self.assertFalse(payload["requires_external_pr_refresh"])
            self.assertEqual(payload["base"], "main")
            self.assertEqual(payload["head"], "automation/operant-release-v0.6.1")
            self.assertEqual(payload["candidate_branch"], "automation/operant-release-v0.6.1")
            self.assertEqual(payload["candidate_sha"], "candidate-create-sha")
            self.assertEqual(payload["candidate_tree_sha"], "candidate-create-tree")
            self.assertEqual(payload["title"], "chore(operant): release v0.6.1")
            self.assertIn("external provider/agent", body_path.read_text(encoding="utf-8"))

    def test_unpublished_candidate_converges_on_one_stable_branch(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('pending_branch="automation/operant-release-v${next_version}"', workflow)
        self.assertIn(
            'git ls-remote --exit-code --heads origin "refs/heads/${pending_branch}"',
            workflow,
        )
        self.assertIn(
            'echo "Refreshing unpublished Operant release candidate branch in place: $pending_branch"',
            workflow,
        )
        self.assertIn('git fetch origin "$pending_branch"', workflow)
        self.assertIn('git merge --no-edit origin/main', workflow)
        self.assertNotIn('branch="automation/operant-release-v${next_version}-${main_sha:0:8}"', workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertNotIn("git push -f", workflow)

    def test_mainline_release_owners_are_serialized_across_push_and_dispatch(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("'mainline-owner'", workflow)
        self.assertIn("format('pr-{0}', github.event.pull_request.number)", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn(
            "operant-versioning-${{ github.event_name }}-${{ github.ref }}",
            workflow,
        )
        self.assertIn('git push origin HEAD:"$candidate_branch"', workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertNotIn("git push -f", workflow)

    def test_existing_release_pr_refresh_is_staged_for_external_publication(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('gh pr edit "$existing_url"', workflow)
        self.assertNotIn('git checkout -B "$existing_branch"', workflow)
        self.assertIn('staging_branch="automation/operant-release-staging-v${next_version}"', workflow)
        self.assertIn('target_head="$existing_branch"', workflow)
        self.assertIn('candidate_branch="$staging_branch"', workflow)
        self.assertIn('git push origin HEAD:"$candidate_branch"', workflow)

        existing_pr_url = "https://github.example.invalid/org/repo/pull/999"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            body_path = root / "body.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PR_REQUEST_SCRIPT),
                    "--version",
                    "0.6.1",
                    "--source-sha",
                    "abc123",
                    "--head",
                    "automation/operant-release-v0.6.1",
                    "--base",
                    "main",
                    "--candidate-branch",
                    "automation/operant-release-staging-v0.6.1",
                    "--candidate-sha",
                    "candidate-refresh-sha",
                    "--candidate-tree-sha",
                    "candidate-refresh-tree",
                    "--existing-pr-url",
                    existing_pr_url,
                    "--output",
                    str(request_path),
                    "--body-output",
                    str(body_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "operant-release-pr-request/v2")
            self.assertEqual(payload["publication_owner"], "external-provider")
            self.assertEqual(payload["publication_mode"], "external-refresh-existing-pr")
            self.assertFalse(payload["requires_external_pr_creation"])
            self.assertTrue(payload["requires_external_pr_refresh"])
            self.assertEqual(payload["existing_pr_url"], existing_pr_url)
            self.assertEqual(payload["head"], "automation/operant-release-v0.6.1")
            self.assertEqual(
                payload["candidate_branch"],
                "automation/operant-release-staging-v0.6.1",
            )
            self.assertEqual(payload["candidate_sha"], "candidate-refresh-sha")
            self.assertEqual(payload["candidate_tree_sha"], "candidate-refresh-tree")
            self.assertEqual(
                payload["refresh_strategy"],
                "create-two-parent-candidate-tree-commit-and-fast-forward-target-head",
            )
            body = body_path.read_text(encoding="utf-8")
            self.assertIn("external provider/agent owns both first-PR publication", body)
            self.assertIn("existing-PR head refresh", body)


if __name__ == "__main__":
    unittest.main()