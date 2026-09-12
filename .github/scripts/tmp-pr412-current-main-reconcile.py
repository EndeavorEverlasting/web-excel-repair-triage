import json
import re
from pathlib import Path


tutorial = Path("docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md")
text = tutorial.read_text(encoding="utf-8")
p105_row = "| CI/CD promotion should work locally or over generic Git whenever possible and use a forge only for forge-owned gates | P105 | Builds a provider-agnostic, local-first promotion core with thin host adapters and a bounded provider-request budget. |"
if p105_row not in text:
    anchor = "| Work must proceed in dependency order | P60 | Produces a serialized execution sequence. |\n"
    if text.count(anchor) != 1:
        raise SystemExit("tutorial: P105 common-path insertion anchor drifted")
    text = text.replace(anchor, anchor + p105_row + "\n")

section = """## Local-first CI/CD with P105

P105 separates the **repository-owned promotion core** from any particular forge. The first question is not “which GitHub Action should we write?” It is “which parts of this promotion can the repository and plain Git prove without a provider?”

Use three execution modes:

1. **LOCAL_ONLY** — run repository-owned validation, build/package, provenance, candidate-receipt, and policy-evaluation commands without a hosted CI provider.
2. **GIT_REMOTE_MINIMAL** — use ordinary Git transport for fetch/push/tag/ref operations when repository policy allows them and no provider-only gate is required.
3. **PROVIDER_GOVERNED** — use the host adapter only for facts or mutations Git cannot establish, such as required-check state, unresolved review threads, merge queues, protected environments, or authoritative provider mutation receipts.

GitHub Actions remains supported when GitHub is the observed host, but it is an adapter over the same repository-owned commands. A GitLab CI, Azure Pipelines, Gitea/Forgejo, self-hosted runner, or local shell should be able to invoke the same core when its capability map permits.

### Rate-limit behavior

Provider calls are a budgeted dependency, not free background polling. P105 requires agents to:

- classify a call as **GIT_PROVABLE** or **PROVIDER_ONLY** before adding another provider dependency;
- reuse candidate-bound provider truth while its SHA/base/policy identity remains current;
- prefer event-driven wakeups over status polling and batch compatible reads where supported;
- honor `Retry-After` and provider reset metadata, use bounded backoff with jitter, and cap refresh attempts;
- preserve the highest proven local gate and candidate receipt when `PROVIDER_RATE_LIMITED` occurs;
- resume from the same candidate after provider recovery instead of rerunning unchanged local work;
- still perform the authoritative fresh provider read immediately before a provider-governed mutation.

A provider outage or rate limit never grants permission to bypass branch protection. Local/Git proof reduces dependence on the forge; it does not counterfeit provider-owned proof.

"""
if "## Local-first CI/CD with P105" not in text:
    anchor = "## Conversational fallback\n"
    if text.count(anchor) != 1:
        raise SystemExit("tutorial: P105 section insertion anchor drifted")
    text = text.replace(anchor, section + anchor)
tutorial.write_text(text, encoding="utf-8")

strengthening_path = Path("registry/prompts/prompt-strengthenings.v1.json")
strengthening = json.loads(strengthening_path.read_text(encoding="utf-8"))
records = [record for record in strengthening.get("strengthenings", []) if record.get("id") == "P105"]
if len(records) != 1:
    raise SystemExit(f"expected exactly one P105 strengthening, found {len(records)}")
records[0].pop("tutorial", None)
strengthening["strengthenings"] = records
strengthening_path.write_text(
    json.dumps(strengthening, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

builder = Path("scripts/build_prompt_kit_registry.py")
builder_text = builder.read_text(encoding="utf-8")
builder_text, count = re.subn(
    r'\nTUTORIAL_STRENGTHENING_DISPOSITIONS = \{.*?\n\}\n',
    '\n',
    builder_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("builder: tutorial strengthening disposition constant anchor drifted")
builder_text, count = re.subn(
    r'\n        tutorial = strengthening\.get\("tutorial"\).*?\n        result\[positions\[prompt_id\]\] = strengthened',
    '\n        result[positions[prompt_id]] = strengthened',
    builder_text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("builder: tutorial strengthening metadata block anchor drifted")
builder.write_text(builder_text, encoding="utf-8")

Path("registry/prompts/tutorial-freshness.v1.json").unlink(missing_ok=True)

test_path = Path("tests/test_p105_local_first_tutorial_freshness.py")
test_path.write_text(
    '''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry
from scripts import prompt_kit_tutorial_coverage

ROOT = Path(__file__).resolve().parents[1]
STRENGTHENINGS = ROOT / "registry" / "prompts" / "prompt-strengthenings.v1.json"
TUTORIAL = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"


class P105LocalFirstAndTutorialCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.strengthenings = json.loads(STRENGTHENINGS.read_text(encoding="utf-8"))
        cls.tutorial = TUTORIAL.read_text(encoding="utf-8")

    def test_p105_prefers_local_first_provider_minimal_execution(self) -> None:
        prompt = self.prompts["P105"]
        content = prompt["copyContent"]
        for phrase in (
            "LOCAL-FIRST / PROVIDER-MINIMAL CONTROL PLANE",
            "LOCAL_ONLY",
            "GIT_REMOTE_MINIMAL",
            "PROVIDER_GOVERNED",
            "Prefer plain Git transport",
            "Use the provider API only for facts Git cannot prove",
            "GitHub Actions remains a thin adapter",
            "PROVIDER REQUEST BUDGET / RATE-LIMIT ECONOMY",
            "event-driven wakeups over status polling",
            "Retry-After",
            "bounded exponential backoff with jitter",
            "preserve the locally complete candidate receipt",
            "without rerunning unchanged local work",
            "PORTABLE CORE / THIN ADAPTER PROOF",
            "same canonical repo-owned commands",
        ):
            self.assertIn(phrase, content)
        for keyword in (
            "local-first CI/CD",
            "provider-minimal promotion",
            "provider request budget",
            "thin CI adapter",
        ):
            self.assertIn(keyword, prompt["keywords"])

    def test_strengthening_registry_is_bounded_to_p105(self) -> None:
        self.assertEqual(
            self.strengthenings["schema_version"], "prompt-registry-strengthenings/v1"
        )
        records = self.strengthenings["strengthenings"]
        self.assertEqual([record["id"] for record in records], ["P105"])
        self.assertNotIn("tutorial", records[0])

    def test_p105_uses_current_classifier_backed_tutorial_coverage(self) -> None:
        route = prompt_kit_tutorial_coverage.coverage_for_prompt(self.prompts["P105"])
        self.assertFalse(route["needs_wiring"])
        self.assertIn(route["wiring_status"], {"CLASSIFIER_WIRED", "CURATED_WIRED"})
        self.assertEqual(route["prompt_id"], "P105")
        self.assertTrue(route["tutorial_route"])

    def test_tutorial_documents_local_first_without_legacy_freshness_ledger(self) -> None:
        for phrase in (
            "## Classifier-assisted coverage and prompt paths",
            "## Local-first CI/CD with P105",
            "GIT_REMOTE_MINIMAL",
            "PROVIDER_ONLY",
            "Provider calls are a budgeted dependency",
            "P105",
        ):
            self.assertIn(phrase, self.tutorial)
        self.assertNotIn("tutorial-freshness.v1.json", self.tutorial)


if __name__ == "__main__":
    unittest.main()
''',
    encoding="utf-8",
)
