            workflow,
        )
        self.assertNotIn(
            'git ls-remote --exit-code --heads origin "refs/heads/${pending_branch}"',
            workflow,
        )
        self.assertNotIn('git checkout -B "$pending_branch"', workflow)
        self.assertNotIn('candidate_branch="$pending_branch"', workflow)
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
        self.assertIn('candidate_branch="$staging_branch"', workflow)
        self.assertNotIn('git push origin HEAD:"$target_head"', workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertNotIn("git push -f", workflow)

    def test_existing_release_pr_refresh_is_staged_for_external_publication(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('gh pr edit "$existing_url"', workflow)
        self.assertNotIn('git checkout -B "$existing_branch"', workflow)
        self.assertIn('staging_branch="automation/operant-release-staging-v${next_version}"', workflow)
        self.assertIn('target_head="${existing_branch:-$pending_branch}"', workflow)
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