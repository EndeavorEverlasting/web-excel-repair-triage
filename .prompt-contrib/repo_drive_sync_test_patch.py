from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests/test_repository_work_ledger_prompt.py"


def main() -> None:
    text = TEST.read_text(encoding="utf-8")
    method = "test_generic_repo_drive_artifact_synchronizer_is_bounded_and_conflict_safe"
    if f"def {method}" in text:
        print("focused Drive sync tests already present")
        return
    marker = '\n\nif __name__ == "__main__":'
    if marker not in text:
        raise SystemExit("unittest insertion marker missing")
    body = r'''
    def test_generic_repo_drive_artifact_synchronizer_is_bounded_and_conflict_safe(self) -> None:
        matches = [
            prompt
            for prompt in self.prompts_by_id().values()
            if prompt["name"] == "Repository + Google Drive Artifact Synchronizer"
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "SYNC + ARTIFACT")
        self.assertEqual(prompt["class"], "REPOSITORY / ARTIFACT SYNC")
        self.assertEqual(prompt["color"], "Teal")
        self.assertEqual(prompt["category"], "standard")
        self.assertFalse(prompt.get("profile"))
        self.assertEqual(prompt["seq"], prompt["id"][1:])
        self.assertEqual(prompt["copySheet"], f"{prompt['id']}_COPY_SAFE")
        policy = build_prompt_kit_registry.load_actionability_policy()
        self.assertEqual(prompt["actionabilityPolicy"], policy["policy_id"])
        self.assertIn(policy["marker"], content)

        for phrase in (
            "SYNCHRONIZE THE ACTIVE REPOSITORY'S RELEVANT ARTIFACTS WITH GOOGLE DRIVE",
            "DO NOT MIRROR THE WHOLE REPOSITORY",
            "discover and reuse the most strongly evidenced existing workspace",
            "REPO-AUTHORITATIVE",
            "DRIVE-AUTHORITATIVE",
            "BIDIRECTIONAL-BY-CONTRACT",
            "DERIVED / PUBLISH-ONLY",
            "PRIVATE / DO-NOT-SYNC",
            "MAP IDENTITIES, NOT JUST FILENAMES",
            "Preserve Google-native authority",
            "UPLOAD, UPDATE DRIVE, DOWNLOAD/IMPORT, UPDATE REPO, NO CHANGE, CONFLICT, or SKIP",
            "do not create `copy`, `(1)`, dated duplicate",
            "Do not use Drive as source control",
            "FAIL CLOSED ON TWO-SIDED DIVERGENCE",
            "Timestamp-newer alone is not a safe conflict resolver",
            "READ BACK AND VERIFY",
            "SECOND PASS TO A BOUNDED FIXED POINT",
            "does not absorb project-specific management, billing, roster, taxonomy",
        ):
            self.assertIn(phrase, content)

        for forbidden in (
            "EndeavorEverlasting",
            "Triage + FUN + Drive Context Synchronizer",
            "Neuron Track Hours",
            "NTH billing",
        ):
            self.assertNotIn(forbidden, content)

        raw_registry = json.loads(
            (ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json").read_text(
                encoding="utf-8"
            )
        )
        raw_matches = [
            item
            for item in raw_registry["prompts"]
            if item["name"] == "Repository + Google Drive Artifact Synchronizer"
        ]
        self.assertEqual(len(raw_matches), 1)
        self.assertLess(len(raw_matches[0]["copyContent"]), 8000)
        self.assertNotIn(policy["marker"], raw_matches[0]["copyContent"])

    def test_generic_repo_drive_sync_does_not_replace_p77_domain_owner(self) -> None:
        prompts = self.prompts_by_id()
        generic = next(
            prompt
            for prompt in prompts.values()
            if prompt["name"] == "Repository + Google Drive Artifact Synchronizer"
        )
        p77 = prompts["P77"]
        self.assertEqual(p77["name"], "Triage + FUN + Drive Context Synchronizer")
        self.assertEqual(p77["type"], "MAINTENANCE + CROSS-REPO")
        self.assertEqual(p77["profile"], "triage-management")
        self.assertIn("Triage", p77["copyContent"])
        self.assertIn("FUN", p77["copyContent"])
        self.assertNotEqual(generic["class"], p77["class"])
        self.assertNotEqual(generic["type"], p77["type"])
        for keyword in (
            "google drive sync",
            "repository drive sync",
            "artifact sync",
            "sync repo artifacts",
            "drive workspace",
        ):
            self.assertIn(keyword, generic["keywords"])

    def test_generated_preview_contains_generic_repo_drive_sync(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("Repository + Google Drive Artifact Synchronizer", html)
        self.assertIn("REPO-AUTHORITATIVE", html)
        deployed = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(deployed, html)
'''
    TEST.write_text(text.replace(marker, "\n" + body.rstrip() + marker, 1), encoding="utf-8")
    print("added focused generalized repository/Drive sync semantic regressions")


if __name__ == "__main__":
    main()
