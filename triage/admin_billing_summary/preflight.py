"""Web Excel preflight for OpenAI-format admin billing summaries."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

_INLINE_CELL = 't="inlineStr"'
_STOP_SHIP = ["ns0:", "xmlns:ns0"]


def preflight_billing_summary(
    path: str,
    *,
    variant: str,
    expect_neuron_tab: str,
) -> Dict[str, Any]:
    """Validate package structure for Internal or Client billing workbook."""
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
        "preflight_pass": False,
    }
    if not p.exists():
        res["error"] = "file_not_found"
        return res
    try:
        with zipfile.ZipFile(path, "r") as z:
            res["zip_valid"] = z.testzip() is None
            names = z.namelist()
            if "xl/calcChain.xml" in names:
                res["has_calc_chain"] = True
            if any("externalLink" in n for n in names):
                res["has_external_links"] = True
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
            if _INLINE_CELL in all_text:
                res["token_failures"].append("inlineStr")
            for tok in _STOP_SHIP:
                if tok in all_text:
                    res["token_failures"].append(tok)
            res["tabs"] = re.findall(r'<sheet[^>]*name="([^"]+)"', wb_xml)
            if expect_neuron_tab not in res["tabs"]:
                res["token_failures"].append(f"missing_tab:{expect_neuron_tab}")
            if "xl/sharedStrings.xml" in names:
                ss = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                m = re.search(r'\bcount="(\d+)"', ss)
                declared = int(m.group(1)) if m else -1
                refs = sum(
                    z.read(n).decode("utf-8", errors="ignore").count('t="s"')
                    for n in names
                    if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
                )
                res["sharedstrings_declared_count"] = declared
                res["sharedstrings_actual_refs"] = refs
                res["sharedstrings_count_ok"] = declared == refs
            min_tables = 6 if variant == "client" else 9
            if res["native_table_count"] < min_tables:
                res["token_failures"].append(
                    f"native_tables<{min_tables} (got {res['native_table_count']})"
                )
    except zipfile.BadZipFile:
        res["error"] = "bad_zip"
        return res

    res["preflight_pass"] = (
        bool(res["zip_valid"])
        and not res["token_failures"]
        and not res["has_calc_chain"]
        and not res["has_external_links"]
        and bool(res["sharedstrings_count_ok"])
    )
    return res
