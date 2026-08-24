from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TEST = ROOT / "tests/test_ux_design_prompt_suite.py"

SCOPES = {
    "P106": (
        "Information architecture, user journeys, interaction/state architecture, responsive/accessibility behavior, component/action hierarchy, and the smallest representative vertical UX slice needed to prove that structure.",
        "Do not absorb P95 runtime/call-stack architecture, P82 generic experiment ownership, P99 post-working flow/telemetry refinement, P107 reference-fidelity emulation, P108 craft-only polish, P109 cross-app design-system factoring, or P110 acceptance-only certification unless a discovered dependency is explicitly handed to that owner.",
    ),
    "P107": (
        "Observable reference decomposition, observed-vs-inferred fidelity rules, lawful adaptation to the target product, intentional deviations, and real responsive/interactive implementation needed to prove reference fidelity.",
        "Do not become general greenfield UX architecture when no reference drives the work (P106), pure finish/polish (P108), cross-app design-system factoring (P109), or acceptance-only certification (P110); do not copy unauthorized assets, protected content, or unobservable behavior as fact.",
    ),
    "P108": (
        "Craft and finish of an already-working UX: visual hierarchy, spacing, typography, density, motion/feedback, interaction feel, consistency, and bounded repeated polish passes backed by live evidence.",
        "Do not redesign information architecture or product journeys by default (P106), emulate a reference as the primary goal (P107), create a cross-app design system (P109), or replace whole-interface integrity certification (P110); route structural defects to their owning prompt instead of hiding them with cosmetics.",
    ),
    "P109": (
        "Cross-app semantic UX tokens, reusable components/patterns, ownership boundaries, adoption/migration seams, and evidence that consistency improves without forcing unrelated products into identical behavior.",
        "Do not take over app-specific journey architecture (P106), reference emulation (P107), one-interface polish (P108), or final cross-viewport/input acceptance (P110); shared patterns must not erase product-specific semantics or create a second competing source of truth.",
    ),
    "P110": (
        "Falsification and repair of an implemented interface across supported viewports, input modes, focus/keyboard/touch behavior, responsive states, loading/empty/error/success states, and composed interaction sequences.",
        "Do not use acceptance work as a pretext for broad product redesign (P106), reference emulation (P107), craft-only polish (P108), or new cross-app design-system architecture (P109); when a failure reveals an upstream design defect, prove it and hand it to the correct owner.",
    ),
}


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def patch_registry() -> None:
    payload = load_registry()
    by_id = {p["id"]: p for p in payload["prompts"]}
    for prompt_id, (owned, forbidden) in SCOPES.items():
        prompt = by_id[prompt_id]
        content = prompt["copyContent"]
        if "OWNED SCOPE\n" in content and "FORBIDDEN SCOPE\n" in content:
            continue
        needle = "\n\n1. "
        index = content.find(needle)
        if index < 0:
            raise SystemExit(f"numbered-section insertion point missing for {prompt_id}")
        block = (
            "\n\nOWNED SCOPE\n- " + owned
            + "\n\nFORBIDDEN SCOPE\n- " + forbidden
        )
        prompt["copyContent"] = content[:index] + block + content[index:]
    REGISTRY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def patch_tests() -> None:
    text = TEST.read_text(encoding="utf-8")
    method = "test_ux_specialists_declare_owned_and_forbidden_scope"
    if f"def {method}" in text:
        return
    marker = '\n\nif __name__ == "__main__":'
    if marker not in text:
        raise SystemExit("unittest insertion point missing")
    body = '''\n    def test_ux_specialists_declare_owned_and_forbidden_scope(self) -> None:\n        for prompt_id in ("P106", "P107", "P108", "P109", "P110"):\n            content = self.prompts[prompt_id]["copyContent"]\n            with self.subTest(prompt=prompt_id):\n                self.assertIn("OWNED SCOPE", content)\n                self.assertIn("FORBIDDEN SCOPE", content)\n        self.assertIn("P95 runtime/call-stack architecture", self.prompts["P106"]["copyContent"])\n        self.assertIn("when no reference drives the work (P106)", self.prompts["P107"]["copyContent"])\n        self.assertIn("route structural defects to their owning prompt", self.prompts["P108"]["copyContent"])\n        self.assertIn("must not erase product-specific semantics", self.prompts["P109"]["copyContent"])\n        self.assertIn("hand it to the correct owner", self.prompts["P110"]["copyContent"])\n'''
    TEST.write_text(text.replace(marker, body + marker, 1), encoding="utf-8")


def main() -> None:
    patch_registry()
    patch_tests()
    print(json.dumps({"repaired": list(SCOPES), "finding": "explicit UX owned/forbidden scopes"}, indent=2))


if __name__ == "__main__":
    main()
