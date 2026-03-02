"""
triage/dv_engine.py
-------------------
Data Validation engine for .xlsx workbooks.

Extracts, categorises, and applies data-validation rules so that:
  * Header rows are locked   ("This is a header row, foo 🤡")
  * Formula cells are locked  ("This is a formula cell, foo 🤡")
  * Automated fields are locked ("Automated field, foo 🤡")
  * List dropdowns are enforced (Yes/No, status codes, …)

The engine works at the byte/string level — no openpyxl, no lxml.
Rules are stored in a JSON-serialisable DV dictionary so new rules
can be added declaratively and re-applied across workbook iterations.
"""
from __future__ import annotations

import json
import re
import uuid
import zipfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from triage.xlsx_utils import (
    read_text, sheet_parts, sheet_name_map, extract_blocks, get_attr,
)

# ──────────────────────── DV categories ────────────────────────

HEADER_ROW_TITLE   = "This is a header row, foo \U0001f921"
HEADER_ROW_ERROR   = "Skedaddle \U0001f4a8"

FORMULA_CELL_TITLE = "This is a formula cell, foo \U0001f921"
FORMULA_CELL_ERROR = "Skedaddle \U0001f4a8"

AUTOMATED_TITLE    = "Automated field, foo \U0001f921"
AUTOMATED_ERROR    = "Skedaddle \U0001f4a8. Don\u2019t overwrite formulas \U0001f604"
# Note: the workbook uses a straight apostrophe — keep both variants
AUTOMATED_ERROR_ALT = "Skedaddle \U0001f4a8. Don't overwrite formulas \U0001f604"


@dataclass
class DVRule:
    """A single data-validation rule extracted or to be applied."""
    id: str = ""
    category: str = ""          # header_row | formula_cell | automated | list | custom | blank
    sheet_part: str = ""        # e.g. xl/worksheets/sheet10.xml
    sheet_name: str = ""        # human-readable
    sqref: str = ""             # cell range(s)
    dv_type: str = ""           # custom | list | whole | (empty)
    allow_blank: bool = True
    show_input: bool = False
    show_error: bool = False
    error_title: str = ""
    error_msg: str = ""
    prompt: str = ""
    formula1: str = ""
    formula2: str = ""
    show_dropdown: Optional[bool] = None   # only for list type
    uid: str = ""               # xr:uid from original XML

    def to_xml(self) -> str:
        """Render this rule as an OOXML <dataValidation …> element."""
        attrs: List[str] = []
        if self.dv_type:
            attrs.append(f'type="{_esc(self.dv_type)}"')
        if self.allow_blank:
            attrs.append('allowBlank="1"')
        if self.show_dropdown is not None and self.show_dropdown:
            attrs.append('showDropDown="1"')
        if self.show_input:
            attrs.append('showInputMessage="1"')
        if self.show_error:
            attrs.append('showErrorMessage="1"')
        if self.error_title:
            attrs.append(f'errorTitle="{_esc(self.error_title)}"')
        if self.error_msg:
            attrs.append(f'error="{_esc(self.error_msg)}"')
        if self.prompt:
            attrs.append(f'prompt="{_esc(self.prompt)}"')
        attrs.append(f'sqref="{self.sqref}"')
        # Generate a fresh UID for each rule
        uid = self.uid or "{" + str(uuid.uuid4()).upper() + "}"
        attrs.append(f'xr:uid="{uid}"')

        inner = ""
        if self.formula1:
            inner += f"<formula1>{_esc(self.formula1)}</formula1>"
        if self.formula2:
            inner += f"<formula2>{_esc(self.formula2)}</formula2>"

        attr_str = " ".join(attrs)
        if inner:
            return f"<dataValidation {attr_str}>{inner}</dataValidation>"
        else:
            return f"<dataValidation {attr_str}/>"


@dataclass
class DVSpec:
    """Full data-validation specification for a workbook."""
    source_file: str = ""
    rules: List[DVRule] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "DVSpec":
        d = json.loads(text)
        rules = [DVRule(**r) for r in d.get("rules", [])]
        return cls(source_file=d.get("source_file", ""), rules=rules)

    def rules_for_sheet(self, part: str) -> List[DVRule]:
        return [r for r in self.rules if r.sheet_part == part]


# ──────────────────── extraction from workbook ────────────────────


def extract_dv_spec(path: str) -> DVSpec:
    """Extract all data-validation rules from an .xlsx file."""
    spec = DVSpec(source_file=path)
    with zipfile.ZipFile(path, "r") as z:
        name_map = sheet_name_map(z)
        for part in sheet_parts(z):
            xml = read_text(z, part)
            dv_blocks = extract_blocks(xml, "dataValidation")
            friendly = name_map.get(part, part)
            for block in dv_blocks:
                # Skip the outer <dataValidations> wrapper — only want inner rules
                if block.strip().startswith("<dataValidations"):
                    continue
                rule = _parse_dv_element(block, part, friendly)
                spec.rules.append(rule)
    return spec


# ──────────────────── applying DV to a workbook ────────────────────


def apply_dv_spec(xlsx_bytes: bytes, spec: DVSpec) -> bytes:
    """Apply a DVSpec to an in-memory .xlsx, returning patched bytes.

    For each sheet in the spec, this replaces/inserts the
    <dataValidations> block with the rules from the spec.
    Byte-level manipulation — no XML parser.
    """
    import io

    src = zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r")
    buf = io.BytesIO()
    dst = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    parts_with_rules = {r.sheet_part for r in spec.rules}

    for item in src.infolist():
        data = src.read(item.filename)
        if item.filename in parts_with_rules:
            rules = spec.rules_for_sheet(item.filename)
            data = _inject_dv_block(data, rules)
        dst.writestr(item, data)

    dst.close()
    src.close()
    return buf.getvalue()


def _inject_dv_block(sheet_bytes: bytes, rules: List[DVRule]) -> bytes:
    """Replace or insert the <dataValidations> block in a sheet XML."""
    xml = sheet_bytes.decode("utf-8", errors="ignore")

    # Build the new block
    rule_xml = "".join(r.to_xml() for r in rules)
    new_block = (
        f'<dataValidations count="{len(rules)}">'
        f"{rule_xml}"
        f"</dataValidations>"
    )

    # Try to replace existing block
    pattern = r"<dataValidations\b[^>]*>.*?</dataValidations>"
    if re.search(pattern, xml, re.DOTALL):
        xml = re.sub(pattern, new_block, xml, count=1, flags=re.DOTALL)
    else:
        # Insert before </worksheet> or </sheetData> close — prefer before
        # pageMargins or before </worksheet>
        for anchor in ("</sheetData>", "<pageMargins", "<pageSetup", "</worksheet>"):
            idx = xml.find(anchor)
            if idx != -1:
                # For </sheetData>, insert after it
                if anchor == "</sheetData>":
                    idx += len(anchor)
                xml = xml[:idx] + new_block + xml[idx:]
                break

    return xml.encode("utf-8")


# ──────────────────── internal parsing helpers ────────────────────


def _parse_dv_element(xml_fragment: str, part: str, sheet_name: str) -> DVRule:
    """Parse a single <dataValidation …>…</dataValidation> element."""
    rule = DVRule(
        id=str(uuid.uuid4())[:8],
        sheet_part=part,
        sheet_name=sheet_name,
    )
    rule.dv_type = get_attr(xml_fragment, "type") or ""
    rule.sqref = get_attr(xml_fragment, "sqref") or ""
    rule.allow_blank = get_attr(xml_fragment, "allowBlank") == "1"
    rule.show_input = get_attr(xml_fragment, "showInputMessage") == "1"
    rule.show_error = get_attr(xml_fragment, "showErrorMessage") == "1"
    rule.error_title = get_attr(xml_fragment, "errorTitle") or ""
    rule.error_msg = get_attr(xml_fragment, "error") or ""
    rule.prompt = get_attr(xml_fragment, "prompt") or ""
    rule.uid = get_attr(xml_fragment, "xr:uid") or ""

    sd = get_attr(xml_fragment, "showDropDown")
    rule.show_dropdown = (sd == "1") if sd is not None else None

    # Extract formula1, formula2
    f1 = re.search(r"<formula1>(.*?)</formula1>", xml_fragment, re.DOTALL)
    rule.formula1 = f1.group(1) if f1 else ""
    f2 = re.search(r"<formula2>(.*?)</formula2>", xml_fragment, re.DOTALL)
    rule.formula2 = f2.group(1) if f2 else ""

    # Categorise
    rule.category = _categorise(rule)
    return rule


def _categorise(rule: DVRule) -> str:
    """Assign a human-readable category based on the rule's attributes."""
    title = rule.error_title.lower()
    if "header row" in title:
        return "header_row"
    if "formula cell" in title:
        return "formula_cell"
    if "automated field" in title or "automated" in title:
        return "automated"
    # Unlabelled custom FALSE rules are still protection rules
    if rule.dv_type == "custom" and rule.formula1.strip().upper() == "FALSE":
        return "protected"
    if rule.dv_type == "list":
        return "list"
    if rule.dv_type == "whole":
        return "whole_number"
    if rule.dv_type == "custom":
        return "custom"
    if rule.dv_type == "":
        # Blank type with error messages → still a protection rule
        if rule.error_title or rule.error_msg:
            return "automated"
        return "blank"
    return "other"


def _esc(s: str) -> str:
    """Minimal XML attribute escaping."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ──────────────────── convenience builders ────────────────────


def make_header_protection(sheet_part: str, sqref: str, sheet_name: str = "") -> DVRule:
    """Create a header-row protection rule."""
    return DVRule(
        category="header_row",
        sheet_part=sheet_part,
        sheet_name=sheet_name,
        sqref=sqref,
        dv_type="custom",
        allow_blank=True,
        show_input=True,
        show_error=True,
        error_title=HEADER_ROW_TITLE,
        error_msg=HEADER_ROW_ERROR,
        formula1="FALSE",
    )


def make_formula_protection(sheet_part: str, sqref: str, sheet_name: str = "") -> DVRule:
    """Create a formula-cell protection rule."""
    return DVRule(
        category="formula_cell",
        sheet_part=sheet_part,
        sheet_name=sheet_name,
        sqref=sqref,
        dv_type="custom",
        allow_blank=True,
        show_input=True,
        show_error=True,
        error_title=FORMULA_CELL_TITLE,
        error_msg=FORMULA_CELL_ERROR,
        formula1="FALSE",
    )


def make_automated_protection(sheet_part: str, sqref: str, sheet_name: str = "") -> DVRule:
    """Create an automated-field protection rule."""
    return DVRule(
        category="automated",
        sheet_part=sheet_part,
        sheet_name=sheet_name,
        sqref=sqref,
        dv_type="custom",
        allow_blank=True,
        show_input=True,
        show_error=True,
        error_title=AUTOMATED_TITLE,
        error_msg=AUTOMATED_ERROR_ALT,
        formula1="FALSE",
    )


def make_list_validation(
    sheet_part: str, sqref: str, items: List[str],
    sheet_name: str = "", show_dropdown_hidden: bool = False,
) -> DVRule:
    """Create a list (dropdown) validation rule."""
    formula = '"' + ",".join(items) + '"'
    return DVRule(
        category="list",
        sheet_part=sheet_part,
        sheet_name=sheet_name,
        sqref=sqref,
        dv_type="list",
        allow_blank=True,
        show_input=True,
        show_error=True,
        formula1=formula,
        show_dropdown=True if show_dropdown_hidden else None,
    )


# ──────────────────── CLI ────────────────────


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m triage.dv_engine <path.xlsx> [--apply <spec.json> <out.xlsx>]")
        sys.exit(1)

    if sys.argv[1] == "--apply" and len(sys.argv) >= 4:
        spec_path = sys.argv[2]
        src_path = sys.argv[3]
        out_path = sys.argv[4] if len(sys.argv) > 4 else src_path.replace(".xlsx", "_dv.xlsx")
        spec = DVSpec.from_json(open(spec_path, encoding="utf-8").read())
        with open(src_path, "rb") as fh:
            patched = apply_dv_spec(fh.read(), spec)
        with open(out_path, "wb") as fh:
            fh.write(patched)
        print(f"Applied {len(spec.rules)} DV rules → {out_path}")
    else:
        spec = extract_dv_spec(sys.argv[1])
        print(f"Extracted {len(spec.rules)} DV rules from {sys.argv[1]}")
        for r in spec.rules:
            print(f"  [{r.category:15s}] {r.sheet_name:30s} sqref={r.sqref[:40]}")
        # Print JSON
        print("\n" + spec.to_json())

