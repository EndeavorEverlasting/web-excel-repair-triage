"""Web Excel and audience-boundary preflight for admin billing summaries."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Dict

from triage.webexcel_semantic_gate import run_semantic_gate

_INLINE_CELL = 't="inlineStr"'
_STOP_SHIP = ["ns0:", "xmlns:ns0"]
_CLIENT_FORBIDDEN_TABS = {
    "Tech Project Summary",
    "Review Flags",
    "CF Dictionary",
    "WebExcel QC",
}
_CLIENT_FORBIDDEN_TEXT = (
    "Clock In",
    "Clock Out",
    "Review Net Hours",
    "Review row count",
    "Source roster",
    "Override > Worked > Assignment > Live default",
)


def preflight_billing_summary(path: str, *, variant: str, expect_neuron_tab: str) -> Dict[str, Any]:
    """Validate package structure and the Internal/Client disclosure contract."""
    p = Path(path)
    res: Dict[str, Any] = {
        "artifact": p.name,
        "path": str(p.resolve()),
        "variant": variant,
        "exists": p.exists(),
        "zip_valid": False,
        "token_failures": [],
        "has_calc_chain": False,
        "has_external_links": False,
        "sharedstrings_count_ok": True,
        "native_table_count": 0,
        "tabs": [],
        "expected_neuron_tab": expect_neuron_tab,
        "client_hygiene_pass": None if variant != "client" else False,
        "client_hygiene_failures": [],
        "semantic_integrity": "FAIL",
        "sentinel_failures": [],
        "shared_string_count": 0,
        "generic_column_string_count": 0,
        "meaningful_shared_string_count": 0,
        "meaningful_shared_string_ratio": 1.0,
        "generic_column_strings_only": False,
        "post_repair_text_loss": False,
        "excel_for_web_manual_check": "NOT_PROVEN",
        "preflight_pass": False,
    }
    if not p.exists():
        res["error"] = "file_not_found"
        return res

    try:
        with zipfile.ZipFile(path, "r") as z:
            res["zip_valid"] = z.testzip() is None
            names = z.namelist()
            res["has_calc_chain"] = "xl/calcChain.xml" in names
            res["has_external_links"] = any("externalLink" in n for n in names)
            res["native_table_count"] = len([n for n in names if n.startswith("xl/tables/")])
            all_text = ""
            wb_xml = ""
            for name in names:
                if not (name.endswith(".xml") or name.endswith(".rels")):
                    continue
                text = z.read(name).decode("utf-8", errors="ignore")
                all_text += text
                if name == "xl/workbook.xml":
                    wb_xml = text

            for name in names:
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    if _INLINE_CELL in z.read(name).decode("utf-8", errors="ignore"):
                        res["token_failures"].append("inlineStr")
                        break
            for tok in _STOP_SHIP:
                if tok in all_text:
                    res["token_failures"].append(tok)

            res["tabs"] = re.findall(r'<sheet[^>]*name="([^"]+)"', wb_xml)
            if expect_neuron_tab not in res["tabs"]:
                res["token_failures"].append(f"missing_tab:{expect_neuron_tab}")

            if variant == "client":
                failures = res["client_hygiene_failures"]
                required = {"Start Here", "Executive Dashboard", "Monthly Summary", "Project Summary", "Tech Summary", expect_neuron_tab}
                for tab in sorted(required):
                    if tab not in res["tabs"]:
                        failures.append(f"missing_client_tab:{tab}")
                for tab in sorted(_CLIENT_FORBIDDEN_TABS):
                    if tab in res["tabs"]:
                        failures.append(f"forbidden_client_tab:{tab}")
                month_detail = [t for t in res["tabs"] if t.endswith(" Neuron Hours")]
                for tab in month_detail:
                    failures.append(f"forbidden_client_tab:{tab}")
                for text in _CLIENT_FORBIDDEN_TEXT:
                    if text in all_text:
                        failures.append(f"forbidden_client_text:{text}")
                res["client_hygiene_pass"] = not failures
                if failures:
                    res["token_failures"].extend(failures)

            refs = sum(
                z.read(n).decode("utf-8", errors="ignore").count('t="s"')
                for n in names
                if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
            )
            res["sharedstrings_actual_refs"] = refs
            if "xl/sharedStrings.xml" in names:
                ss = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                m = re.search(r'\bcount="(\d+)"', ss)
                declared = int(m.group(1)) if m else -1
                res["sharedstrings_declared_count"] = declared
                res["sharedstrings_count_ok"] = declared == refs
            elif refs > 0:
                res["sharedstrings_count_ok"] = False

            min_tables = 6 if variant == "client" else 9
            if res["native_table_count"] < min_tables:
                res["token_failures"].append(
                    f"native_tables<{min_tables} (got {res['native_table_count']})"
                )
    except zipfile.BadZipFile:
        res["error"] = "bad_zip"
        return res

    gate = run_semantic_gate(path, profile="admin_billing")
    res.update(gate)
    audience_ok = variant != "client" or res.get("client_hygiene_pass") is True
    res["preflight_pass"] = (
        bool(res["zip_valid"])
        and not res["token_failures"]
        and not res["has_calc_chain"]
        and not res["has_external_links"]
        and bool(res["sharedstrings_count_ok"])
        and res["semantic_integrity"] == "PASS"
        and not res["generic_column_strings_only"]
        and audience_ok
    )
    return res
