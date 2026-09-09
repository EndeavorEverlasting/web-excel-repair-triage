from __future__ import annotations

import argparse
import json
from pathlib import Path

REGISTRY = Path("registry/prompts/correspondence-prompts.v1.json")
TEST = Path("tests/test_correspondence_prompt_registry.py")

P72_SECTION = """MINIMUM SUFFICIENT CONTEXT
Apply a recipient-need gate before keeping supporting detail. Sender-side reasoning, evidence sources, private trackers or ledgers, checkpoint mechanics, internal timestamps or cutoffs, monitoring/reporting cadence, and fine-grained precision are not automatically message content. Keep them only when they help the recipient answer, decide, authorize, or act, or when they are externally material for correctness, safety, compliance, contractual or SLA commitments, authorization, or risk.

QUESTION-SURFACE CONTROL
Avoid self-inflicted disclosure: do not volunteer a hidden tool, tracker or ledger name, `daily`, `hourly`, `same-day`, an internal cutoff, or other cadence or precision merely to justify the ask when doing so could create a new management question, reporting expectation, commitment, or scope unrelated to the recipient's task. Ask the smallest sufficient external question. Do not hide a detail the recipient genuinely needs.

"""

P73_SECTION = """RECIPIENT-NEED GATE / MINIMUM SUFFICIENT CONTEXT
For every contextual detail, ask whether it helps the recipient answer, decide, authorize, or act. If it merely explains why the sender is asking or proves internal diligence, keep it internal. Evidence that convinced the sender is not automatically evidence the recipient needs.

QUESTION-SURFACE CONTROL / SELF-INFLICTED DISCLOSURE
Do not volunteer private tracker or ledger names, internal checkpoint or cutoff times, monitoring/reporting cadence, or fine-grained precision such as `daily`, `hourly`, or `same-day` language when those details are not externally material. They can create new management questions, reporting expectations, commitments, or scope unrelated to the requested decision. Ask the smallest sufficient external question instead.

EXTERNAL-MATERIAL EXCEPTION
Preserve details necessary for correctness, safety, compliance, contractual or SLA obligations, authorization, material risk, or the recipient's ability to respond correctly. This is audience selection, not concealment.

EXAMPLE
When asking a coordinator how work reaches them, ask for the intake path and whether they use a dedicated queue/view/report or a broader work pool. Do not cite a private tracker, an internal cutoff time, or `same-day` monitoring merely to justify the question.

"""

TEST_METHOD = """
    def test_correspondence_prompts_gate_self_inflicted_disclosure(self) -> None:
        p72 = self.prompts["P72"]["copyContent"]
        p73 = self.prompts["P73"]["copyContent"]

        for phrase in (
            "MINIMUM SUFFICIENT CONTEXT",
            "QUESTION-SURFACE CONTROL",
            "self-inflicted disclosure",
            "reporting expectation",
            "smallest sufficient external question",
        ):
            with self.subTest(prompt="P72", phrase=phrase):
                self.assertIn(phrase, p72)

        for phrase in (
            "RECIPIENT-NEED GATE / MINIMUM SUFFICIENT CONTEXT",
            "QUESTION-SURFACE CONTROL / SELF-INFLICTED DISCLOSURE",
            "private tracker",
            "daily",
            "hourly",
            "same-day",
            "reporting expectations",
            "smallest sufficient external question",
            "EXTERNAL-MATERIAL EXCEPTION",
            "audience selection, not concealment",
            "queue/view/report",
        ):
            with self.subTest(prompt="P73", phrase=phrase):
                self.assertIn(phrase, p73)

        self.assertIn(
            "Do not hide a detail the recipient genuinely needs",
            p72,
        )
        self.assertIn(
            "Evidence that convinced the sender is not automatically evidence the recipient needs",
            p73,
        )
"""

def add_section(content: str, anchor: str, section: str, marker: str) -> str:
    if marker in content:
        return content
    if anchor not in content:
        raise SystemExit(f"required prompt anchor missing: {anchor!r}")
    return content.replace(anchor, section + anchor, 1)

def mutate_registry() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompts = {prompt["id"]: prompt for prompt in data["prompts"]}
    if set(prompts) != {"P72", "P73"}:
        raise SystemExit(f"unexpected correspondence owner set: {sorted(prompts)}")

    p72 = prompts["P72"]
    p73 = prompts["P73"]

    p72["copyContent"] = add_section(
        p72["copyContent"],
        "TONE\n",
        P72_SECTION,
        "MINIMUM SUFFICIENT CONTEXT",
    )
    p73["copyContent"] = add_section(
        p73["copyContent"],
        "REMOVE OR TRANSLATE INTERNAL MACHINERY UNLESS THE RECIPIENT ACTUALLY NEEDS IT\n",
        P73_SECTION,
        "RECIPIENT-NEED GATE / MINIMUM SUFFICIENT CONTEXT",
    )

    p72["proofGate"] = (
        "The result is shorter without dropping material content, confident without overclaiming, "
        "actionable without inventing owners or deadlines, cordial without becoming gushy or submissive, "
        "faithful to the source, and limited to minimum sufficient recipient context; sender-side evidence, "
        "cadence, and precision do not create avoidable question or reporting surfaces."
    )
    p73["proofGate"] = (
        "The recipient can understand what happened, what matters to them, what remains constrained, and what "
        "action is needed without seeing irrelevant internal machinery or self-inflicted disclosure; every "
        "contextual detail earns its place by helping the recipient answer, decide, authorize, or act, while no "
        "material failure, uncertainty, dependency, accountability fact, safety/compliance obligation, or "
        "externally material risk is hidden or converted into false certainty."
    )

    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def mutate_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    if "def test_correspondence_prompts_gate_self_inflicted_disclosure" not in text:
        marker = "    def test_render_includes_correspondence_runtime_and_profile_tokens"
        if marker not in text:
            raise SystemExit("focused test insertion anchor missing")
        text = text.replace(marker, TEST_METHOD + "\n" + marker, 1)
        TEST.write_text(text, encoding="utf-8")

def verify() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompts = {prompt["id"]: prompt for prompt in data["prompts"]}
    p72 = prompts["P72"]["copyContent"]
    p73 = prompts["P73"]["copyContent"]

    required_p72 = [
        "MINIMUM SUFFICIENT CONTEXT",
        "QUESTION-SURFACE CONTROL",
        "self-inflicted disclosure",
        "smallest sufficient external question",
    ]
    required_p73 = [
        "RECIPIENT-NEED GATE / MINIMUM SUFFICIENT CONTEXT",
        "QUESTION-SURFACE CONTROL / SELF-INFLICTED DISCLOSURE",
        "private tracker",
        "`daily`",
        "`hourly`",
        "`same-day`",
        "reporting expectations",
        "EXTERNAL-MATERIAL EXCEPTION",
        "queue/view/report",
    ]
    for phrase in required_p72:
        if phrase not in p72:
            raise SystemExit(f"P72 missing semantic marker: {phrase}")
    for phrase in required_p73:
        if phrase not in p73:
            raise SystemExit(f"P73 missing semantic marker: {phrase}")

    test_text = TEST.read_text(encoding="utf-8")
    if "def test_correspondence_prompts_gate_self_inflicted_disclosure" not in test_text:
        raise SystemExit("focused regression missing")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        mutate_registry()
        mutate_test()
    verify()
    print("PASS: P72/P73 recipient-need and question-surface semantics")

if __name__ == "__main__":
    main()
