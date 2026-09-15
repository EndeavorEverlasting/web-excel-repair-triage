#!/usr/bin/env python3
"""Fail closed when Prompt Kit UI leaves the formatting sequence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-kit-ui-format-alignment.v1.json"
LEDGER = ROOT / "harness/prompt-kit-ui-format-alignment/ledger.v1.json"

CLASSNAME_RE = re.compile(
    r"""(?:className|\.className)\s*=\s*['"]([^'"]+)['"]|class\s*=\s*['"]([^'"]+)['"]""",
    re.MULTILINE,
)
BUTTON_CREATE_RE = re.compile(
    r"""createElement\(\s*['"]button['"]\s*\)|<button\b[^>]*>""",
    re.IGNORECASE,
)
DEFERRED_RE = re.compile(
    r"""data-ui-format-deferred\s*=\s*['"]([^'"]+)['"]|setAttribute\(\s*['"]data-ui-format-deferred['"]\s*,\s*['"]([^'"]+)['"]\s*\)"""
)
FORBIDDEN_ASSIGN_RE = re.compile(
    r"""(?:className|\.className)\s*=\s*['"]([^'"]+)['"]|class\s*=\s*['"]([^'"]+)['"]"""
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tokenize_classes(raw: str) -> list[str]:
    return [part for part in re.split(r"\s+", raw.strip()) if part]


def class_allowed(token: str, allowed: set[str], prefixes: list[str]) -> bool:
    if token in allowed:
        return True
    return any(token.startswith(prefix) for prefix in prefixes)


def validate(require_implementation: bool = True) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    findings: list[dict] = []

    if not CONTRACT.exists():
        return {
            "ok": False,
            "errors": [f"missing contract: {CONTRACT.relative_to(ROOT).as_posix()}"],
            "warnings": [],
            "findings": [],
        }
    if not LEDGER.exists():
        return {
            "ok": False,
            "errors": [f"missing ledger: {LEDGER.relative_to(ROOT).as_posix()}"],
            "warnings": [],
            "findings": [],
        }

    contract = load_json(CONTRACT)
    ledger = load_json(LEDGER)

    if contract.get("schema_version") != "prompt-kit-ui-format-alignment/v1":
        errors.append("contract schema_version must be prompt-kit-ui-format-alignment/v1")
    if ledger.get("schema_version") != "prompt-kit-ui-format-alignment-ledger/v1":
        errors.append("ledger schema_version must be prompt-kit-ui-format-alignment-ledger/v1")
    if ledger.get("contract_id") != contract.get("contract_id"):
        errors.append("ledger contract_id must match the format-alignment contract")

    allowed = set(contract.get("allowed_classes") or [])
    prefixes = list(contract.get("allowed_class_prefixes") or [])
    forbidden = set(contract.get("forbidden_classes") or [])
    deferred_attr = contract.get("deferred_attribute") or "data-ui-format-deferred"
    header_class = contract.get("header_utility_required_class") or "operant-resource-button"
    header_ids = list(contract.get("header_utility_control_ids") or [])
    scan_paths = list(contract.get("scan_paths") or [])

    aligned_rows = ledger.get("aligned") if isinstance(ledger.get("aligned"), list) else []
    deferred_rows = ledger.get("deferred") if isinstance(ledger.get("deferred"), list) else []
    if not isinstance(ledger.get("aligned"), list):
        errors.append("ledger.aligned must be an array")
    if not isinstance(ledger.get("deferred"), list):
        errors.append("ledger.deferred must be an array")

    deferred_ids = set()
    for row in deferred_rows:
        if not isinstance(row, dict):
            errors.append("deferred ledger rows must be objects")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip():
            errors.append("deferred ledger rows require non-empty id")
            continue
        if row_id in deferred_ids:
            errors.append(f"duplicate deferred ledger id: {row_id}")
        deferred_ids.add(row_id)
        for field in ("source", "reason", "owner", "next_action"):
            if not isinstance(row.get(field), str) or not str(row.get(field)).strip():
                errors.append(f"deferred row {row_id} missing {field}")
        if row.get("status") != "deferred":
            errors.append(f"deferred row {row_id} status must be 'deferred'")

    aligned_ids = set()
    for row in aligned_rows:
        if not isinstance(row, dict):
            errors.append("aligned ledger rows must be objects")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip():
            errors.append("aligned ledger rows require non-empty id")
            continue
        if row_id in aligned_ids:
            errors.append(f"duplicate aligned ledger id: {row_id}")
        aligned_ids.add(row_id)
        if row.get("status") != "aligned":
            errors.append(f"aligned row {row_id} status must be 'aligned'")
        classes = row.get("classes")
        if not isinstance(classes, list) or not classes:
            errors.append(f"aligned row {row_id} must declare classes")
        else:
            for token in classes:
                if not isinstance(token, str) or not class_allowed(token, allowed, prefixes):
                    errors.append(f"aligned row {row_id} uses uncatalogued class: {token!r}")

    overlap = aligned_ids & deferred_ids
    if overlap:
        errors.append("ledger ids cannot be both aligned and deferred: " + ", ".join(sorted(overlap)))

    for rel in scan_paths:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing scan path: {rel}")
            continue
        text = path.read_text(encoding="utf-8")

        for control_id in header_ids:
            if control_id not in text:
                continue
            marker = f"id='{control_id}'" if f"id='{control_id}'" in text else f'id="{control_id}"'
            window_start = text.find(marker)
            if window_start < 0:
                # id assigned as property: button.id='...'
                prop = f".id='{control_id}'"
                window_start = text.find(prop)
                if window_start < 0:
                    prop = f'.id="{control_id}"'
                    window_start = text.find(prop)
            if window_start < 0:
                errors.append(f"{rel}: could not locate assignment for {control_id}")
                continue
            window = text[max(0, window_start - 220) : window_start + 420]
            if header_class not in window:
                findings.append(
                    {
                        "path": rel,
                        "control_id": control_id,
                        "kind": "header-utility-misaligned",
                        "detail": f"header utility must use class {header_class}",
                    }
                )
                errors.append(
                    f"{rel}: {control_id} is out of the header formatting sequence; required class {header_class}"
                )
            if any(token in tokenize_classes(m.group(1) or m.group(2) or "") for m in FORBIDDEN_ASSIGN_RE.finditer(window) for token in tokenize_classes(m.group(1) or m.group(2) or "") if token in forbidden):
                errors.append(f"{rel}: {control_id} still uses a forbidden class token")

        for match in FORBIDDEN_ASSIGN_RE.finditer(text):
            raw = match.group(1) or match.group(2) or ""
            tokens = tokenize_classes(raw)
            bad = [token for token in tokens if token in forbidden]
            if not bad:
                continue
            start = max(0, match.start() - 180)
            end = min(len(text), match.end() + 180)
            vicinity = text[start:end]
            deferred_match = DEFERRED_RE.search(vicinity)
            deferred_id = None
            if deferred_match:
                deferred_id = deferred_match.group(1) or deferred_match.group(2)
            finding = {
                "path": rel,
                "classes": bad,
                "kind": "forbidden-class",
                "deferred_id": deferred_id,
            }
            findings.append(finding)
            if deferred_id and deferred_id in deferred_ids:
                warnings.append(
                    f"{rel}: forbidden class {bad} deferred as {deferred_id} (PR fodder)"
                )
                continue
            errors.append(
                f"{rel}: forbidden class(es) {bad} without a matching deferred ledger entry; "
                f"either adopt a catalog class or set {deferred_attr} and ledger.deferred"
            )

        # Fail closed on createElement('button') / <button> windows whose nearest className is empty or unknown.
        for button_match in BUTTON_CREATE_RE.finditer(text):
            window = text[button_match.start() : min(len(text), button_match.start() + 500)]
            class_match = CLASSNAME_RE.search(window)
            deferred_match = DEFERRED_RE.search(window)
            deferred_id = None
            if deferred_match:
                deferred_id = deferred_match.group(1) or deferred_match.group(2)
            if class_match is None:
                # Parent-scoped HTML buttons inside known styled shells are tolerated only when deferred.
                if deferred_id and deferred_id in deferred_ids:
                    warnings.append(f"{rel}: classless button deferred as {deferred_id}")
                    continue
                # Heuristic: template fragments that rely on parent selectors still need deferred or class.
                if "<button" in button_match.group(0).lower() and "class=" not in button_match.group(0).lower():
                    findings.append(
                        {
                            "path": rel,
                            "kind": "classless-button",
                            "snippet": button_match.group(0)[:120],
                            "deferred_id": deferred_id,
                        }
                    )
                    errors.append(
                        f"{rel}: classless <button> must use a catalog class or {deferred_attr} + deferred ledger row"
                    )
                continue

            raw = class_match.group(1) or class_match.group(2) or ""
            tokens = tokenize_classes(raw)
            if not tokens:
                if deferred_id and deferred_id in deferred_ids:
                    warnings.append(f"{rel}: empty className deferred as {deferred_id}")
                    continue
                errors.append(
                    f"{rel}: empty button className requires {deferred_attr} + deferred ledger row"
                )
                continue

            if any(token in forbidden for token in tokens):
                # Already handled by forbidden scan with richer messaging.
                continue

            if any(class_allowed(token, allowed, prefixes) for token in tokens):
                continue

            if deferred_id and deferred_id in deferred_ids:
                warnings.append(
                    f"{rel}: uncatalogued classes {tokens} deferred as {deferred_id} (PR fodder)"
                )
                continue

            findings.append(
                {
                    "path": rel,
                    "kind": "uncatalogued-class",
                    "classes": tokens,
                    "deferred_id": deferred_id,
                }
            )
            errors.append(
                f"{rel}: button classes {tokens} are outside the formatting catalog; "
                f"add them to the contract allowlist, or mark {deferred_attr} and ledger.deferred"
            )

    # Required aligned rows for the known Storage/Resources neighbor pair.
    required_aligned = {
        "header-storage-utility",
        "header-resources-utility",
        "storage-modal-surface",
    }
    missing_required = sorted(required_aligned - aligned_ids)
    if missing_required:
        errors.append("ledger.aligned missing required rows: " + ", ".join(missing_required))

    storage_runtime = ROOT / "docs/prompt-kit-storage-lifecycle.js"
    if require_implementation and storage_runtime.exists():
        storage_text = storage_runtime.read_text(encoding="utf-8")
        if "className='btn'" in storage_text or 'className="btn"' in storage_text:
            errors.append(
                "docs/prompt-kit-storage-lifecycle.js still assigns className='btn' (out of formatting sequence)"
            )

    ok = not errors
    return {
        "ok": ok,
        "schema_version": "prompt-kit-ui-format-alignment-result/v1",
        "contract_id": contract.get("contract_id"),
        "aligned_count": len(aligned_ids),
        "deferred_count": len(deferred_ids),
        "findings": findings,
        "warnings": warnings,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--require-implementation", action="store_true", default=False)
    parser.add_argument(
        "--output",
        default="Outputs/prompt-kit-ui-format-alignment.json",
        help="Audit receipt path",
    )
    args = parser.parse_args(argv)
    result = validate(require_implementation=True)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        status = "PASS" if result["ok"] else "FAIL"
        print(
            f"{status} prompt-kit-ui-format-alignment aligned={result['aligned_count']} "
            f"deferred={result['deferred_count']} errors={len(result['errors'])}"
        )
        for err in result["errors"][:20]:
            print(f"  - {err}")
        for warn in result["warnings"][:10]:
            print(f"  ! {warn}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
