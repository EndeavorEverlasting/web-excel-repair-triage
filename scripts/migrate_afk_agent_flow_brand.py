#!/usr/bin/env python3
"""Apply the compatibility-safe Operant -> AFK Agent Flow public-brand migration.

This is deliberately a one-way, idempotent migration helper for the rename sprint.
It changes public identity and public routing while preserving historical/internal
Operant and Prompt Kit release seams. Generated HTML is rebuilt by its canonical
builder; this script never hand-edits generated output.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
NEW_PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/afk-agent-flow/"
LEGACY_OPERANT_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/operant/"


class MigrationError(RuntimeError):
    pass


def replace_literal(path: str, old: str, new: str, *, expected: int | None = None) -> bool:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        if new in text:
            return False
        raise MigrationError(f"{path}: neither expected old nor migrated text found: {old!r}")
    if expected is not None and count != expected:
        raise MigrationError(f"{path}: expected {expected} occurrence(s), found {count}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")
    return True


def ensure_contains(path: str, marker: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if marker not in text:
        raise MigrationError(f"{path}: required marker missing after migration: {marker!r}")


def migrate() -> list[str]:
    changed: set[str] = set()

    def apply(path: str, old: str, new: str, *, expected: int | None = None) -> None:
        if replace_literal(path, old, new, expected=expected):
            changed.add(path)

    # Canonical renderer: change only visible brand markers; keep Operant version
    # function/file names as compatibility seams in this wave.
    apply(
        "build_prompt_kit.py",
        "html.append(f'<title>Operant {operant_version}</title>')",
        "html.append(f'<title>AFK Agent Flow {operant_version}</title>')",
        expected=1,
    )
    apply(
        "build_prompt_kit.py",
        "html.append(f'      <div><h1>Operant <span>{operant_version}</span></h1>'",
        "html.append(f'      <div><h1>AFK Agent Flow <span>{operant_version}</span></h1>'",
        expected=1,
    )
    apply(
        "build_prompt_kit.py",
        "html.append('      <div class=\"logo-icon\">AK</div>')",
        "html.append('      <div class=\"logo-icon\">AF</div>')",
        expected=1,
    )

    # Historical Operant version authority remains intact; only generated-site
    # brand markers change so old tags/releases keep their meaning.
    apply(
        "scripts/operant_version.py",
        'f"<title>Operant {version}</title>",',
        'f"<title>AFK Agent Flow {version}</title>",',
        expected=1,
    )
    apply(
        "scripts/operant_version.py",
        'f"Operant <span>{version}</span>",',
        'f"AFK Agent Flow <span>{version}</span>",',
        expected=1,
    )

    # Governance changes the current brand/authority target without rewriting
    # historical release vocabulary.
    apply(
        "AGENTS.md",
        "**Operant** is the operator-approved product identity, formerly Prompt Kit; it began here as a spreadsheet. Target: `UnderDeskDev/Operant`; not yet created/proven.",
        "**AFK Agent Flow** is the operator-approved product identity, formerly Operant / Prompt Kit; it began here as a spreadsheet. Target: `UnderDeskDev/AFK-Agent-Flow`; not yet created/proven.",
        expected=1,
    )
    apply(
        "AGENTS.md",
        "Until cutover, legacy `prompt-kit` paths and sources here remain authoritative compatibility surfaces and must not be silently moved. This repo may pin, mirror, package, link to, or consume Operant releases; it must not become a competing Operant authority; keep cross-repo dependencies explicit and versioned.",
        "Until cutover, legacy `operant` / `prompt-kit` paths and sources here remain authoritative compatibility surfaces and must not be silently moved. This repo may pin, mirror, package, link to, or consume AFK Agent Flow releases through the historical Operant release seams; it must not become a competing AFK Agent Flow authority; keep cross-repo dependencies explicit and versioned.",
        expected=1,
    )

    # Focused tests should assert the new visible identity while retaining tests
    # for historical Operant release mechanics.
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertEqual(payload["product_name"], "Operant")',
        'self.assertEqual(payload["product_name"], "AFK Agent Flow")',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertEqual(payload["authority"]["target_repository"], "UnderDeskDev/Operant")',
        'self.assertEqual(payload["authority"]["target_repository"], "UnderDeskDev/AFK-Agent-Flow")',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn(f"<title>Operant {version}</title>", html)',
        'self.assertIn(f"<title>AFK Agent Flow {version}</title>", html)',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn(f"Operant <span>{version}</span>", html)',
        'self.assertIn(f"AFK Agent Flow <span>{version}</span>", html)',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'def test_governance_and_access_surface_name_operant(self) -> None:',
        'def test_governance_and_access_surface_name_afk_agent_flow(self) -> None:',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn("**Operant** is the operator-approved product identity", governance)',
        'self.assertIn("**AFK Agent Flow** is the operator-approved product identity", governance)',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn("`UnderDeskDev/Operant`", governance)',
        'self.assertIn("`UnderDeskDev/AFK-Agent-Flow`", governance)',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertTrue(access.startswith("# Get Operant"))',
        'self.assertTrue(access.startswith("# Get AFK Agent Flow"))',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn("legacy `prompt-kit` paths", governance)',
        'self.assertIn("legacy `operant` / `prompt-kit` paths", governance)',
        expected=1,
    )
    apply(
        "tests/test_operant_product_identity.py",
        'self.assertIn("compatibility paths", access)',
        'self.assertIn("compatibility and historical release identifiers", access)',
        expected=1,
    )

    apply(
        "tests/test_prompt_kit_order_navigation_product.py",
        "def test_visible_product_identity_is_operant(self) -> None:",
        "def test_visible_product_identity_is_afk_agent_flow(self) -> None:",
        expected=1,
    )
    apply(
        "tests/test_prompt_kit_order_navigation_product.py",
        "self.assertIn(f'<title>Operant {version}</title>', html)",
        "self.assertIn(f'<title>AFK Agent Flow {version}</title>', html)",
        expected=1,
    )
    apply(
        "tests/test_prompt_kit_order_navigation_product.py",
        "self.assertIn(f'Operant <span>{version}</span>', html)",
        "self.assertIn(f'AFK Agent Flow <span>{version}</span>', html)",
        expected=1,
    )

    # User-facing acquisition/access docs and freshness owners move to the
    # canonical public route together so replay cannot leave split guidance.
    apply("PROMPT_KIT_ACCESS.md", "# Get Operant", "# Get AFK Agent Flow", expected=1)
    apply(
        "PROMPT_KIT_ACCESS.md",
        "> **Transition:** Operant is the current product identity. Existing `Prompt Kit`, `prompt-kit`, and `PromptKit` names below are compatibility paths and launcher/storage identifiers until the dedicated `UnderDeskDev/Operant` cutover is proven.",
        "> **Transition:** AFK Agent Flow is the current product identity. `Operant`, `Prompt Kit`, `prompt-kit`, and `PromptKit` remain compatibility and historical release identifiers until the dedicated `UnderDeskDev/AFK-Agent-Flow` cutover is proven. Legacy public compatibility URLs remain https://endeavoreverlasting.github.io/web-excel-repair-triage/operant/ and https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/.",
        expected=1,
    )

    public_route_files = (
        "PROMPT_KIT_ACCESS.md",
        "OPEN_PROMPT_KIT_ON_PHONE.md",
        "README.md",
        "CAPABILITIES.md",
        "CODEBASE_MAP.md",
        "WORKFLOW.md",
        "harness/contracts/prompt-kit-freshness-guidance.v1.json",
        "harness/reports/PROMPT_KIT_RELEASE_IDENTITY.md",
        "harness/reports/PROMPT_KIT_FRESHNESS.md",
        "scripts/validate_prompt_kit_freshness_guidance.py",
        "docs/REPOSITORY_PRESENTATION.md",
        ".ai/skills/technician-prompt-kit-acquisition/SKILL.md",
    )
    for path in public_route_files:
        target = ROOT / path
        if not target.exists():
            raise MigrationError(f"expected public-route owner missing: {path}")
        text = target.read_text(encoding="utf-8")
        if OLD_PUBLIC_URL in text:
            target.write_text(text.replace(OLD_PUBLIC_URL, NEW_PUBLIC_URL), encoding="utf-8")
            changed.add(path)
        elif NEW_PUBLIC_URL not in text:
            raise MigrationError(f"{path}: neither old nor new public URL found")

    apply(
        "harness/contracts/prompt-kit-freshness-guidance.v1.json",
        "canonical public Prompt Kit URL",
        "canonical public AFK Agent Flow URL",
        expected=1,
    )
    apply(
        "scripts/validate_prompt_kit_freshness_guidance.py",
        "canonical public Prompt Kit URL",
        "canonical public AFK Agent Flow URL",
        expected=1,
    )

    # The public-route sweep above also touches the prompt-kit URL embedded
    # in the transition note. Restore that documented compatibility alias
    # while keeping /afk-agent-flow/ canonical everywhere else.
    apply(
        "PROMPT_KIT_ACCESS.md",
        f"Legacy public compatibility URLs remain {LEGACY_OPERANT_URL} and {NEW_PUBLIC_URL}.",
        f"Legacy public compatibility URLs remain {LEGACY_OPERANT_URL} and {OLD_PUBLIC_URL}.",
        expected=1,
    )

    # Keep technical internal Prompt Kit path names, but make the main mobile
    # instructions and visible title current where exact text is known.
    apply(
        "OPEN_PROMPT_KIT_ON_PHONE.md",
        "same Prompt Kit used on desktop",
        "same AFK Agent Flow experience used on desktop",
    )
    apply(
        "PROMPT_KIT_ACCESS.md",
        "The home-screen shortcut opens the same responsive Prompt Kit used on desktop.",
        "The home-screen shortcut opens the same responsive AFK Agent Flow experience used on desktop.",
        expected=1,
    )
    apply(
        "PROMPT_KIT_ACCESS.md",
        "- Tap/click the **Operant** title to reset the temporary browsing state while preserving Favorites.",
        "- Tap/click the **AFK Agent Flow** title to reset the temporary browsing state while preserving Favorites.",
        expected=1,
    )
    apply(
        "docs/REPOSITORY_PRESENTATION.md",
        "the current Operant operator surface",
        "the current AFK Agent Flow operator surface",
    )

    # The product identity test expects both legacy public URLs to remain
    # documented. The prompt-kit URL is present in the transition note above;
    # this marker makes the Operant compatibility route explicit as well.
    ensure_contains("PROMPT_KIT_ACCESS.md", LEGACY_OPERANT_URL)
    ensure_contains("PROMPT_KIT_ACCESS.md", OLD_PUBLIC_URL)
    ensure_contains("PROMPT_KIT_ACCESS.md", NEW_PUBLIC_URL)

    return sorted(changed)


def run_checked(*command: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True)
    if result.returncode:
        raise MigrationError(f"command failed ({result.returncode}): {' '.join(command)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Apply canonical-source edits without regenerating the owned website artifact.",
    )
    args = parser.parse_args(argv)
    try:
        changed = migrate()
        if not args.no_build:
            run_checked(
                sys.executable,
                "scripts/build_prompt_kit_registry.py",
                "--output",
                "web/prompt-kit/index.html",
            )
            run_checked(
                sys.executable,
                "scripts/build_prompt_kit_registry.py",
                "--output",
                "web/prompt-kit/index.html",
                "--check",
            )
    except (OSError, MigrationError) as exc:
        print(f"AFK Agent Flow migration failed: {exc}", file=sys.stderr)
        return 1

    print("AFK Agent Flow migration applied.")
    for path in changed:
        print(f"- {path}")
    if not changed:
        print("- no canonical-source edits required; migration was already applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
