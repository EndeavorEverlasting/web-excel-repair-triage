from __future__ import annotations

import json
from pathlib import Path

PROMPT_PATH = Path("docs/prompts.json")
TEST_PATH = Path("tests/test_prompt_kit_durability_graduation.py")

P07_MARKER = "## DURABILITY / GRADUATION GATE — NO SNIPPET HELL"
P18_MARKER = "## DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH"
P34_MARKER = "## SNIPPET-TO-OPERATOR-PATH GRADUATION"


def append_once(text: str, marker: str, block: str) -> str:
    if marker in text:
        return text
    return text.rstrip() + "\n\n" + block.strip() + "\n"


def add_keywords(prompt: dict, values: list[str]) -> None:
    prompt["keywords"] = list(dict.fromkeys([*prompt.get("keywords", []), *values]))


def update_prompts() -> None:
    prompts = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))
    by_id = {prompt["id"]: prompt for prompt in prompts}
    required = {"P07", "P18", "P34"}
    missing = sorted(required - set(by_id))
    if missing:
        raise SystemExit(f"missing canonical prompt owners: {missing}")

    p07 = by_id["P07"]
    p07["copyContent"] = append_once(
        p07["copyContent"],
        P07_MARKER,
        r'''## DURABILITY / GRADUATION GATE — NO SNIPPET HELL
When this sprint creates, rediscovers, or depends on operational behavior that exists mainly as chat instructions, copied commands, an ad-hoc snippet, or a temporary manual sequence, treat that form as an incubation state rather than durable completion when the behavior is recurring or reusable.

Classify the current maturity stage and the next evidence-earned stage:
`REQUEST / EXPERIMENT -> SNIPPET -> REUSABLE EXECUTABLE -> REPOSITORY-NATIVE TOOL -> VALIDATED INTERFACE / ARTIFACT`.

The ladder is implementation-form agnostic. A reusable executable may be CMD, PowerShell, Bash, Python, SQL, a task-runner command, macro, workflow, or another repository-native mechanism. An interface/artifact may be a launcher, GUI, web surface, spreadsheet control, menu, dashboard, generated report, API, or automation surface. CMD is one valid implementation form, not the definition of maturity.

Before creating a new wrapper or surface, search the repository for the existing implementation, scripts/helpers, canonical configuration/data owners, validators/tests, operator documentation, launchers, GUI/web controls, spreadsheet surfaces, and generated artifacts. Extend the canonical owner instead of creating a second implementation.

Promotion from snippet to reusable executable is warranted when evidence shows one or more of: repeated operator need; another technician/user must run it; copy/paste creates material error risk; invocation requires non-obvious arguments or ordering; the sequence has entered a documented workflow; or substantially the same commands are being recreated across conversations. The executable must have a stable entry point, bounded behavior, useful failure reporting, documented inputs, and repository-owned validation appropriate to the risk.

Promote a proven repository tool to an interface/artifact when requiring users to know or manually invoke the underlying implementation has become unnecessary friction. The interface MUST call or consume the validated canonical implementation or canonical data contract; do not fork the logic into a GUI, spreadsheet formula/macro, web control, or launcher merely to make it visible.

Do not force a later stage before evidence justifies it. A one-time diagnostic or exploratory snippet may remain a snippet. If behavior is recurring but remains snippet-only at closeout, state the concrete reason promotion is not yet justified or is blocked.

For any graduation performed in this sprint, closeout evidence must name: previous stage; resulting stage; canonical implementation owner; created/modified files; stable invocation or interface; validation actually executed; runtime/field proof ceiling; and whether another graduation is now evidence-warranted. Creating a wrapper, button, workbook element, or other surface is not completion unless it is proven to reach the canonical behavior.''',
    )
    add_keywords(
        p07,
        [
            "snippet hell",
            "snippet to tool",
            "durability graduation",
            "reusable executable",
            "artifact graduation",
        ],
    )

    p18 = by_id["P18"]
    p18["copyContent"] = append_once(
        p18["copyContent"],
        P18_MARKER,
        r'''## DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH
Runnable examples and snippets are teaching and diagnostic aids; they are not a substitute for repository tooling when the same operational sequence is recurring. If documentation keeps reproducing the same copy/paste command sequence, treat that as implementation evidence: route the durable implementation to P07, and route a technician-facing launcher/terminal experience to P34 when that operator surface is the missing piece.

Once behavior has graduated, teach the stable canonical entry point rather than preserving an obsolete chat snippet as the primary workflow. For GUI, web, spreadsheet, launcher, or generated-artifact workflows, document the exact user-facing controls and expected evidence while preserving the boundary that the interface consumes the canonical implementation/data contract instead of duplicating its logic.

Do not claim that prose, a copied snippet, or a screenshot has graduated the behavior. Documentation may expose a proof ceiling or promotion need, but executable/tool/interface maturity is established by the owning implementation and its validation.''',
    )
    add_keywords(p18, ["durable operator path", "reusable snippet", "stable entry point"])

    p34 = by_id["P34"]
    p34["copyContent"] = append_once(
        p34["copyContent"],
        P34_MARKER,
        r'''## SNIPPET-TO-OPERATOR-PATH GRADUATION
Repeated chat retrieval means the operator path is incomplete. Reuse proven canonical behavior; graduate recurring work to a stable executable. Only after proof, expose that same implementation through a launcher, GUI/web control, spreadsheet, or artifact. Never veneer an unproven snippet.''',
    )
    add_keywords(p34, ["chat snippet", "snippet graduation", "operator entry point", "stable executable"])

    PROMPT_PATH.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_focused_test() -> None:
    TEST_PATH.write_text(
        '''from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class PromptDurabilityGraduationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {
            prompt["id"]: prompt
            for prompt in json.loads((REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        }
        cls.effective = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_p07_owns_cross_repo_durability_graduation_without_cmd_lock_in(self) -> None:
        prompt = self.raw["P07"]
        self.assertEqual(prompt["name"], "Repo Sprint Executor")
        self.assertEqual(prompt["type"], "BUILD")
        content = prompt["copyContent"]
        for phrase in (
            "DURABILITY / GRADUATION GATE — NO SNIPPET HELL",
            "REQUEST / EXPERIMENT -> SNIPPET -> REUSABLE EXECUTABLE -> REPOSITORY-NATIVE TOOL -> VALIDATED INTERFACE / ARTIFACT",
            "CMD is one valid implementation form, not the definition of maturity",
            "substantially the same commands are being recreated across conversations",
            "The interface MUST call or consume the validated canonical implementation",
            "Do not force a later stage before evidence justifies it",
            "previous stage; resulting stage; canonical implementation owner",
        ):
            self.assertIn(phrase, content)
        for keyword in ("snippet hell", "snippet to tool", "durability graduation", "artifact graduation"):
            self.assertIn(keyword, prompt["keywords"])

    def test_p18_documents_the_durable_path_without_becoming_the_implementation_owner(self) -> None:
        prompt = self.raw["P18"]
        self.assertEqual(prompt["name"], "Documentation + Tutorial Executor")
        self.assertEqual(prompt["type"], "ENABLEMENT")
        content = prompt["copyContent"]
        for phrase in (
            "DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH",
            "they are not a substitute for repository tooling when the same operational sequence is recurring",
            "route the durable implementation to P07",
            "route a technician-facing launcher/terminal experience to P34",
            "teach the stable canonical entry point",
            "interface consumes the canonical implementation/data contract instead of duplicating its logic",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("REQUEST / EXPERIMENT -> SNIPPET -> REUSABLE EXECUTABLE", content)

    def test_p34_graduates_chat_commands_only_after_canonical_behavior_is_proven(self) -> None:
        prompt = self.raw["P34"]
        self.assertEqual(prompt["name"], "GNHF Technician Experience")
        self.assertEqual(prompt["type"], "ENABLEMENT + BUILD")
        content = prompt["copyContent"]
        for phrase in (
            "SNIPPET-TO-OPERATOR-PATH GRADUATION",
            "Repeated chat retrieval means the operator path is incomplete",
            "Reuse proven canonical behavior",
            "stable executable",
            "launcher, GUI/web control, spreadsheet, or artifact",
            "Never veneer an unproven snippet",
        ):
            self.assertIn(phrase, content)

    def test_combined_registry_retains_the_three_strengthened_owner_roles(self) -> None:
        for prompt_id, expected_name in (
            ("P07", "Repo Sprint Executor"),
            ("P18", "Documentation + Tutorial Executor"),
            ("P34", "GNHF Technician Experience"),
        ):
            self.assertEqual(self.effective[prompt_id]["name"], expected_name)
        self.assertIn("DURABILITY / GRADUATION GATE — NO SNIPPET HELL", self.effective["P07"]["copyContent"])
        self.assertIn("DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH", self.effective["P18"]["copyContent"])
        self.assertIn("SNIPPET-TO-OPERATOR-PATH GRADUATION", self.effective["P34"]["copyContent"])

    def test_generated_site_contains_every_strengthened_owner_marker(self) -> None:
        site = (REPO_ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "DURABILITY / GRADUATION GATE — NO SNIPPET HELL",
            "DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH",
            "SNIPPET-TO-OPERATOR-PATH GRADUATION",
        ):
            self.assertIn(marker, site)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    update_prompts()
    write_focused_test()
