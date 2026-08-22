from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DRAFT = REPO_ROOT / ".prompt-contrib" / "open-source-prior-art-gap.json"
TEST_PATH = REPO_ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
RECEIPT_PATH = REPO_ROOT / ".prior-art-receipt.tmp.json"
NAME = "Open-Source Prior-Art & Gap Analyst"
TEST_NAME = "test_open_source_prior_art_prompt_separates_real_world_baseline_from_local_gap"


def main() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "prompt_registry_ops.py"),
            "add",
            "--input",
            str(DRAFT),
            "--registry",
            "spec-architecture-prompts",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    receipt = json.loads(result.stdout)
    if receipt.get("status") != "added":
        raise SystemExit(f"unexpected helper status: {receipt!r}")
    prompt_id = receipt["id"]
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    source = TEST_PATH.read_text(encoding="utf-8")
    marker = '\n\nif __name__ == "__main__":\n'
    if marker not in source:
        raise SystemExit("focused-test insertion marker not found")
    if TEST_NAME in source:
        raise SystemExit("focused prior-art semantic test already exists")

    method = f'''
    def {TEST_NAME}(self) -> None:
        matches = [
            prompt
            for prompt in self.full.values()
            if prompt["name"] == {NAME!r}
        ]
        self.assertEqual(len(matches), 1)
        prompt = matches[0]
        content = prompt["copyContent"]
        raw_content = self.raw[prompt["id"]]["copyContent"]
        self.assertEqual(prompt["id"], {prompt_id!r})
        self.assertEqual(prompt["seq"], {prompt_id[1:]!r})
        self.assertEqual(prompt["copySheet"], {prompt_id + "_COPY_SAFE"!r})
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "RESEARCH / REFERENCE ARCHITECTURE")
        self.assertIn(
            "ANALYZE OPEN-SOURCE REPOSITORIES THAT HAVE ALREADY DONE THINGS LIKE THIS SO THAT WE CAN EMULATE THAT",
            content,
        )
        self.assertIn("WHAT IS ALREADY AVAILABLE IN THE REAL WORLD", content)
        self.assertIn("WHAT PROJECT-SPECIFIC GAP IS STILL WORTH DEVELOPING", content)
        self.assertIn("VERIFY IMPLEMENTATION, NOT MARKETING", content)
        self.assertIn("A README can orient the search but cannot by itself prove an implementation claim", content)
        for evidence_state in (
            "OBSERVED_IMPLEMENTED",
            "DOCUMENTED_UNVERIFIED",
            "INFERRED",
            "ABSENT",
        ):
            self.assertIn(evidence_state, content)
        for disposition in ("ADOPT", "ADAPT", "REJECT", "UNKNOWN"):
            self.assertIn(disposition, content)
        for gap_state in (
            "ALREADY_SOLVED_INTERNALLY",
            "AVAILABLE_TO_EMULATE_EXTERNALLY",
            "PROJECT_SPECIFIC_GAP",
            "EVIDENCE_GAP",
        ):
            self.assertIn(gap_state, content)
        self.assertIn("EMULATE MECHANISMS, NOT CODE BLINDLY", content)
        self.assertIn("verify license compatibility", content)
        self.assertIn("Search the current repo before the wider ecosystem", content)
        self.assertIn("fresh current repository", content.lower())
        self.assertIn("refresh the evidence", content.lower())
        self.assertIn("ADVANCE, DON'T END WITH A RESEARCH ESSAY", content)
        self.assertIn("not portfolio ranking", content.lower())
        self.assertIn("do not primarily rank which of our internal repositories", content.lower())
        self.assertIn("do not replace the repository's internal intent routing", content.lower())
        self.assertGreater(len(raw_content), 4500)
        self.assertLess(len(raw_content), 9000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn({NAME!r}, html)
'''
    TEST_PATH.write_text(source.replace(marker, "\n" + method + marker, 1), encoding="utf-8")
    print(f"focused semantic proof inserted for {prompt_id} {NAME}")


if __name__ == "__main__":
    main()
