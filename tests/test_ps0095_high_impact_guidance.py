"""PS-0095: fail-closed static semantic regression for high-impact guidance.

Canonical policy must contain the shared evidence gate on both effective
Prompt Kit surfaces. This is static contract proof, not model behavior proof.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
MARKER = "HIGH-IMPACT GUIDANCE EVIDENCE GATE / PS-0095"
SURFACES = ("next_step_suffix", "copy_content_appendix")
STEPS = (
    "1. CLASSIFY THE HIGH-IMPACT CONSEQUENCE",
    "2. RECOVER RELEVANT HISTORY",
    "3. RECOVER CANONICAL PROMPT REGISTRY",
    "4. RECOVER EVALUATOR AND HARNESS EVIDENCE",
    "5. FORM A BOUNDED HYPOTHESIS",
    "6. PROTOTYPE AND MEASURE",
    "7. CRITIQUE AND REPAIR",
    "8. DECIDE FROM EVIDENCE",
    "9. RETURN AFTER THE EVIDENCE GATE",
)
SAFEGUARDS = (
    "ORIENT/SUMMARIZE/CLOSEOUT",
    "Do not invent evidence",
    "Do not delegate canonical prompt mutation",
)


def validate_gate(value: str) -> None:
    if MARKER not in value:
        raise ValueError("missing high-impact guidance gate")
    gate = value[value.index(MARKER):]
    positions = [gate.find(step) for step in STEPS]
    if any(pos < 0 for pos in positions) or any(a >= b for a, b in zip(positions, positions[1:])):
        raise ValueError("missing or unordered guidance step")
    for safeguard in SAFEGUARDS:
        if safeguard.casefold() not in gate.casefold():
            raise ValueError("missing safeguard: " + safeguard)


def positive() -> str:
    return "\n".join((MARKER, *STEPS, *SAFEGUARDS))


class HighImpactGuidanceTests(unittest.TestCase):
    def test_canonical_policy(self):
        self.assertTrue(POLICY.is_file(), f"missing canonical policy: {POLICY}")
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["policy_id"], "actionable-next-command/v1")
        self.assertEqual(
            policy["applies_to"],
            "Every prompt in the combined canonical Prompt Kit registry.",
        )
        self.assertIn("non-execution", policy["disposition_tail_guard"])
        for surface in SURFACES:
            with self.subTest(surface=surface):
                validate_gate(policy[surface])
        self.assertEqual(
            policy[SURFACES[0]].split(MARKER, 1)[1],
            policy[SURFACES[1]].split(MARKER, 1)[1],
            "effective guidance gates diverged across surfaces",
        )

    def test_positive(self):
        validate_gate(positive())

    def test_absent_gate_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing high-impact"):
            validate_gate("unverified high-impact recommendation")

    def test_each_step_required(self):
        for step in STEPS:
            with self.subTest(step=step):
                with self.assertRaisesRegex(ValueError, "missing or unordered"):
                    validate_gate(positive().replace(step, "[REMOVED]"))

    def test_reordering_rejected(self):
        swapped = positive().replace(STEPS[1], "[SWAP]").replace(
            STEPS[2], STEPS[1]
        ).replace("[SWAP]", STEPS[2])
        with self.assertRaisesRegex(ValueError, "missing or unordered"):
            validate_gate(swapped)

    def test_safeguards_required(self):
        for safeguard in SAFEGUARDS:
            with self.subTest(safeguard=safeguard):
                with self.assertRaisesRegex(ValueError, "missing safeguard"):
                    validate_gate(positive().replace(safeguard, "[REMOVED]"))

    def test_mutation_must_target_gate(self):
        prefix = "ORIENT/SUMMARIZE/CLOSEOUT already appears in legacy text."
        with self.assertRaisesRegex(ValueError, "missing safeguard"):
            validate_gate(prefix + "\n" + positive().replace(SAFEGUARDS[0], "[REMOVED]"))


if __name__ == "__main__":
    unittest.main()
