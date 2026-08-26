#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor missing in {path}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        "tests/test_afk_deterministic_testing_prompt.py",
        '''        self.assertIn("A scheduled wake-up is not work by itself", self.target["copyContent"])
        self.assertIn("This prompt still owns test-floor bootstrap", self.target["copyContent"])
''',
        '''        content = self.target["copyContent"]
        self.assertIn("A scheduled wake-up is not work by itself", content)
        self.assertIn("This prompt still owns test-floor bootstrap", content)
        self.assertIn("route generalized feedback-driven repair to P115", content)
        self.assertIn("Missing or weak regression coverage belongs to P113", content)
        self.assertIn("a red established CI lane belongs to P32", content)
        self.assertIn("an authored exact-green candidate belongs to P105 for promotion", content)
''',
    )

    replace_once(
        "tests/test_test_floor_evolution_prompt.py",
        '''        self.assertIn("PRODUCT DEFECTS MUST ESCAPE THE TEST LANE", self.target["copyContent"])
        self.assertIn("Preserve the regression", self.target["copyContent"])
''',
        '''        content = self.target["copyContent"]
        self.assertIn("PRODUCT DEFECTS MUST ESCAPE THE TEST LANE", content)
        self.assertIn("Preserve the regression, bind the exact failure evidence", content)
        self.assertIn("route the bounded product repair through P115", content)
        self.assertIn("After the repair, rerun the regression and provider gate", content)
        self.assertIn("ingest the new feedback, and continue the next justified pass", content)
        self.assertIn("This prompt owns test evolution; it does not gain arbitrary product ownership", content)
''',
    )

    replace_once(
        "tests/test_afk_feedback_development_prompt.py",
        '''        for phrase in (
            "provider run/job/check ID and candidate SHA",
            "PR review thread/comment/path/line",
            "developers, scripts, agents, models, PRs",
            "exact target, owned surface, evidence, acceptance condition",
            "Do not force the operator to shuttle CI logs",
            "Deduplicate already-consumed signal identities",
        ):
            self.assertIn(phrase, content)
''',
        '''        for phrase in (
            "SIGNAL -> CURRENT OWNER -> CAPABLE WORKER -> MUTATION SURFACE -> VALIDATION -> INTEGRATION GATE -> NEXT SIGNAL",
            "provider run/job/check ID and candidate SHA",
            "failing command/test and first useful error",
            "PR review thread/comment/path/line",
            "runtime receipt; or moved-base/stale-proof evidence",
            "developers, scripts, agents, models, PRs",
            "exact target, owned surface, evidence, acceptance condition, forbidden scope, and command or mutation entrypoint",
            "Do not force the operator to shuttle CI logs",
            "Deduplicate already-consumed signal identities",
        ):
            self.assertIn(phrase, content)
''',
    )

    replace_once(
        "tests/test_afk_feedback_development_prompt.py",
        '''        self.assertIn("Use existing specialized owners rather than teaching this loop to impersonate every subsystem", content)
''',
        '''        self.assertIn("Use existing specialized owners rather than teaching this loop to impersonate every subsystem", content)
        for boundary in (
            "P07 owns general bounded repository execution and its fixed-point/mainline discipline",
            "P32 owns repair of an established failing CI lane",
            "P112 owns bootstrap of a missing deterministic automated-test floor",
            "P113 owns proactive risk-driven evolution of an already trustworthy floor",
            "P104 owns bounded deterministic repository-native code generation from canonical inputs",
            "P105 owns validation and authorized promotion of an already-authored exact candidate",
            "Route other domain work to its current repository owner, developer, agent, model, script, generator, or workflow",
        ):
            self.assertIn(boundary, content)
        self.assertIn("one writer per mutation surface", content)
''',
    )

    replace_once(
        "tests/test_afk_feedback_development_prompt.py",
        '''        self.assertIn("This pipeline remains promotion-only", self.full["P105"]["copyContent"])
        self.assertIn("This prompt still owns test-floor bootstrap", self.full["P112"]["copyContent"])
        self.assertIn("This prompt owns test evolution", self.full["P113"]["copyContent"])
''',
        '''        p105 = self.full["P105"]["copyContent"]
        p112 = self.full["P112"]["copyContent"]
        p113 = self.full["P113"]["copyContent"]
        self.assertIn("This pipeline remains promotion-only", p105)
        self.assertIn("failed promotion gate must produce an actionable repair signal", p105)
        self.assertIn("hand that exact signal to P115", p105)
        self.assertIn("keep promotion blocked", p105)
        self.assertIn("new exact candidate; re-enter this P105 pipeline from the beginning", p105)
        self.assertIn("never reuse proof from the failed candidate", p105)
        self.assertIn("This prompt still owns test-floor bootstrap", p112)
        self.assertIn("route generalized feedback-driven repair to P115", p112)
        self.assertIn("This prompt owns test evolution", p113)
        self.assertIn("Preserve the regression, bind the exact failure evidence", p113)
        self.assertIn("route the bounded product repair through P115", p113)
        self.assertIn("rerun the regression and provider gate", p113)
''',
    )

    replace_once(
        "tests/test_spec_architecture_prompt_registry.py",
        '''        self.assertIn("This pipeline remains promotion-only", promotion["copyContent"])
        self.assertIn("new exact candidate", promotion["copyContent"])
''',
        '''        content = promotion["copyContent"]
        self.assertIn("This pipeline remains promotion-only", content)
        self.assertIn("Emit candidate SHA/base, failing job/check/command", content)
        self.assertIn("artifact/log or review-thread identity", content)
        self.assertIn("owning surface, required acceptance condition, and proof ceiling", content)
        self.assertIn("hand that exact signal to P115", content)
        self.assertIn("keep promotion blocked", content)
        self.assertIn("The repair owner must create a new exact candidate", content)
        self.assertIn("re-enter this P105 pipeline from the beginning", content)
        self.assertIn("never reuse proof from the failed candidate", content)
''',
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
