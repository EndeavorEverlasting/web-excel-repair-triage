#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TESTS = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"

CONTRACT_HEADING = "MCP / SEMANTIC REPOSITORY RETRIEVAL CONTRACT"
CONTRACT = """MCP / SEMANTIC REPOSITORY RETRIEVAL CONTRACT
- FIRST EVIDENCE ACTION: when Augment Context Engine MCP is configured in the active Cursor environment, call its repository-retrieval tool before forming a repository-sensitive implementation plan or making repository-sensitive conclusions. Resolve the active MCP server/tool identity from Cursor; do not invent a tool name.
- Use separate bounded MCP retrievals for promotion authority, validation owners, proof/provenance, and write authority. Return the exact paths/owners found. Do not satisfy this contract with one vague or ceremonial MCP call, generic model knowledge, or ordinary local search alone.
- Then verify every material MCP finding against the actual checkout, refreshed Git state, GitHub/provider state, and repository-owned validators. MCP maps architecture; it does not prove current SHA/base, branch protection, PR/check status, credentials, deployment state, or promotion authority.
- If Augment MCP is unavailable, disconnected, unauthorized, or insufficient, report MCP_RETRIEVAL_BLOCKED and the resulting proof ceiling. Do not claim MCP-backed discovery or silently substitute assumptions."""


def fail(message: str) -> None:
    raise SystemExit(message)


def update_registry() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompts = payload.get("prompts")
    if not isinstance(prompts, list):
        fail("spec architecture registry has no prompt list")
    matches = [item for item in prompts if isinstance(item, dict) and item.get("id") == "P105"]
    if len(matches) != 1:
        fail(f"expected exactly one P105 owner, found {len(matches)}")
    prompt = matches[0]
    if prompt.get("name") != "Validated CI/CD Promotion Pipeline Builder":
        fail("P105 canonical name moved; refuse stale carrier mutation")

    content = str(prompt.get("copyContent", ""))
    if CONTRACT_HEADING in content:
        fail("P105 already contains the Augment MCP retrieval contract; carrier is stale")
    anchor = "\n\nMISSION\n"
    if content.count(anchor) != 1:
        fail("P105 mission anchor is not unique; refuse ambiguous insertion")
    prompt["copyContent"] = content.replace(anchor, f"\n\n{CONTRACT}{anchor}", 1)

    keywords = prompt.get("keywords")
    if not isinstance(keywords, list):
        fail("P105 keywords are not a list")
    for keyword in (
        "augment mcp",
        "context engine mcp",
        "cursor mcp",
        "semantic repository retrieval",
    ):
        if keyword not in keywords:
            keywords.append(keyword)

    REGISTRY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def update_regression() -> None:
    text = TESTS.read_text(encoding="utf-8")
    if "MCP_RETRIEVAL_BLOCKED" in text:
        fail("focused P105 MCP regression already exists; carrier is stale")
    anchor = '        self.assertIn("code already authored", promotion["copyContent"])\n'
    if text.count(anchor) != 1:
        fail("P105 focused-regression anchor is not unique")
    addition = '''        self.assertLess(
            promotion["copyContent"].index("MCP / SEMANTIC REPOSITORY RETRIEVAL CONTRACT"),
            promotion["copyContent"].index("\\nMISSION\\n"),
        )
        for phrase in (
            "FIRST EVIDENCE ACTION",
            "Augment Context Engine MCP",
            "Resolve the active MCP server/tool identity from Cursor",
            "promotion authority, validation owners, proof/provenance, and write authority",
            "Do not satisfy this contract with one vague or ceremonial MCP call",
            "MCP maps architecture; it does not prove current SHA/base",
            "MCP_RETRIEVAL_BLOCKED",
            "Do not claim MCP-backed discovery or silently substitute assumptions",
        ):
            self.assertIn(phrase, promotion["copyContent"])
        self.assertIn("augment mcp", promotion["keywords"])
'''
    TESTS.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")


def verify_local_mutation() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p105 = [item for item in payload["prompts"] if item.get("id") == "P105"]
    if len(p105) != 1:
        fail("post-mutation P105 identity count changed")
    content = p105[0]["copyContent"]
    if content.count(CONTRACT_HEADING) != 1:
        fail("MCP contract must occur exactly once in P105")
    if content.index(CONTRACT_HEADING) > content.index("\nMISSION\n"):
        fail("MCP contract must precede P105 mission")


if __name__ == "__main__":
    update_registry()
    update_regression()
    verify_local_mutation()
