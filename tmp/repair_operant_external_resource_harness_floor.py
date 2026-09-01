#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "validate_harness.py"
text = path.read_text(encoding="utf-8")

insertions = {
    '    "app-harness-validation-report",\n}': '    "app-harness-validation-report",\n    "operant-external-resource-index",\n    "operant-external-resource-gap-ledger",\n}',
    '    "operant-product-identity-tests",\n}': '    "operant-product-identity-tests",\n    "operant-external-resource-audit",\n    "operant-external-resource-tests",\n}',
    '    "repository-hook-integration",\n}': '    "repository-hook-integration",\n    "operant-external-resource-intake",\n}',
    '    "repository-hook-installation-needed",\n}': '    "repository-hook-installation-needed",\n    "operant-external-resource-refresh-needed",\n}',
}
for old, new in insertions.items():
    if new in text:
        continue
    if old not in text:
        raise SystemExit(f"missing validate_harness allowlist anchor: {old!r}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("OPERANT_EXTERNAL_RESOURCE_HARNESS_ALLOWLIST_REPAIRED=1")
