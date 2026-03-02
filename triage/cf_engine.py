"""
triage/cf_engine.py
-------------------
Conditional Formatting engine for .xlsx workbooks.

Extracts CF rules + their DXF (differential formatting) styles from a
workbook into a CF dictionary.  The dictionary is JSON-serialisable so it
can be versioned, edited, and re-applied to future workbook iterations.

Design constraint: each CF rule is *unique* — when you create a new rule
you must add it to the dictionary.  The engine never invents rules.

All manipulation is byte/string-level — no openpyxl, no lxml.
"""
from __future__ import annotations

import io
import json
import re
import uuid
import zipfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from triage.xlsx_utils import (
    read_text, read_bytes, sheet_parts, sheet_name_map,
    extract_blocks, extract_blocks_with_pos, get_attr,
)


# ──────────────────────── data structures ────────────────────────


@dataclass
class CFRule:
    """One <cfRule> element with its associated DXF style."""
    id: str = ""
    rule_type: str = ""          # expression | cellIs | colorScale | dataBar | …
    dxf_id: Optional[int] = None
    priority: int = 0
    operator: str = ""           # equal | greaterThan | lessThan | between | …
    text: str = ""               # for containsText / notContainsText
    formula: str = ""            # primary formula
    formula2: str = ""           # second formula (for between)
    stop_if_true: bool = False
    # The raw DXF XML block that this rule references (resolved from styles.xml)
    dxf_xml: str = ""
    # The raw <cfRule …>…</cfRule> XML for faithful round-tripping
    raw_xml: str = ""


@dataclass
class CFBlock:
    """One <conditionalFormatting sqref="…"> block containing 1+ rules."""
    id: str = ""
    sheet_part: str = ""
    sheet_name: str = ""
    sqref: str = ""
    rules: List[CFRule] = field(default_factory=list)
    # Raw XML for the whole block — enables exact round-trip
    raw_xml: str = ""


@dataclass
class CFDictionary:
    """Full CF specification for a workbook — the 'CF dictionary'."""
    source_file: str = ""
    dxf_styles: List[str] = field(default_factory=list)   # ordered list of <dxf>…</dxf> XML
    blocks: List[CFBlock] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "CFDictionary":
        d = json.loads(text)
        blocks = []
        for b in d.get("blocks", []):
            rules = [CFRule(**r) for r in b.pop("rules", [])]
            blocks.append(CFBlock(**b, rules=rules))
        return cls(
            source_file=d.get("source_file", ""),
            dxf_styles=d.get("dxf_styles", []),
            blocks=blocks,
        )

    def blocks_for_sheet(self, part: str) -> List[CFBlock]:
        return [b for b in self.blocks if b.sheet_part == part]

    def add_rule(self, block: CFBlock) -> None:
        """Add a new CF block to the dictionary."""
        if not block.id:
            block.id = str(uuid.uuid4())[:8]
        self.blocks.append(block)

    @property
    def summary(self) -> Dict[str, Any]:
        sheets = {}
        for b in self.blocks:
            key = b.sheet_name or b.sheet_part
            sheets.setdefault(key, {"blocks": 0, "rules": 0})
            sheets[key]["blocks"] += 1
            sheets[key]["rules"] += len(b.rules)
        return {
            "total_blocks": len(self.blocks),
            "total_rules": sum(len(b.rules) for b in self.blocks),
            "total_dxf_styles": len(self.dxf_styles),
            "per_sheet": sheets,
        }


# ──────────────────── extraction ────────────────────


def extract_cf_dictionary(path: str) -> CFDictionary:
    """Extract the full CF dictionary from an .xlsx file."""
    cfd = CFDictionary(source_file=path)

    with zipfile.ZipFile(path, "r") as z:
        # 1. Extract DXF styles from styles.xml
        if "xl/styles.xml" in z.namelist():
            styles_xml = read_text(z, "xl/styles.xml")
            cfd.dxf_styles = _extract_dxf_list(styles_xml)

        # 2. Extract CF blocks from each sheet
        name_map = sheet_name_map(z)
        for part in sheet_parts(z):
            xml = read_text(z, part)
            friendly = name_map.get(part, part)
            blocks = _parse_cf_blocks(xml, part, friendly, cfd.dxf_styles)
            cfd.blocks.extend(blocks)

    return cfd


# ──────────────────── application ────────────────────


def apply_cf_dictionary(xlsx_bytes: bytes, cfd: CFDictionary) -> bytes:
    """Apply a CF dictionary to an in-memory .xlsx, returning patched bytes.

    Strategy (safe, non-destructive):
    1. Read the active workbook's existing DXF styles.  Append the
       dictionary's DXF styles after them.  Build a dxf_offset so that
       ``deprecated_dxf_id + dxf_offset = new_id_in_active``.
    2. Match CF blocks to sheets BY NAME (from xl/workbook.xml), not by
       part filename — avoids injecting into the wrong sheet when zip
       numbering differs between the deprecated and active workbooks.
    3. Append the rewritten CF blocks AFTER existing CF in the target
       sheet — never removes existing formatting.
    """
    src = zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r")

    # ── build name→part map for the active workbook ───────────────
    active_name_to_part: Dict[str, str] = {}
    for part, name in sheet_name_map(src).items():
        active_name_to_part[name] = part

    # ── group dictionary blocks by sheet_name ─────────────────────
    blocks_by_name: Dict[str, List[CFBlock]] = {}
    for b in cfd.blocks:
        key = b.sheet_name or b.sheet_part
        blocks_by_name.setdefault(key, []).append(b)

    # ── step 1: compute DXF offset and merged list ─────────────────
    # Read existing DXF from active styles.xml; append deprecated styles after.
    styles_xml_raw: Optional[bytes] = None
    if "xl/styles.xml" in src.namelist():
        styles_xml_raw = src.read("xl/styles.xml")

    existing_dxf: List[str] = []
    if styles_xml_raw:
        existing_dxf = _extract_dxf_list(styles_xml_raw.decode("utf-8", errors="ignore"))
    dxf_offset = len(existing_dxf)
    merged_dxf = existing_dxf + list(cfd.dxf_styles)

    # ── build target parts set (sheets that will get new CF) ──────
    target_parts: set = set()
    for sheet_name, blocks in blocks_by_name.items():
        part = active_name_to_part.get(sheet_name)
        if part:
            target_parts.add(part)

    # ── build part→sheet_name map once (before ZIP iteration) ────
    # sheet_name_map reads workbook.xml.rels; must not be called mid-loop.
    active_part_to_name: Dict[str, str] = sheet_name_map(src)

    # ── write patched ZIP ─────────────────────────────────────────
    buf = io.BytesIO()
    dst = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    for item in src.infolist():
        data = src.read(item.filename)

        if item.filename == "xl/styles.xml":
            data = _patch_styles_dxf(data, merged_dxf)
        elif item.filename in target_parts:
            active_name = active_part_to_name.get(item.filename, "")
            blocks_for_part = blocks_by_name.get(active_name, [])
            if blocks_for_part:
                data = _append_cf_blocks(data, blocks_for_part, dxf_offset)

        dst.writestr(item, data)

    dst.close()
    src.close()
    return buf.getvalue()


# ──────────────────── internal helpers ────────────────────


def _extract_dxf_list(styles_xml: str) -> List[str]:
    """Extract ordered list of <dxf>…</dxf> blocks from styles.xml."""
    return re.findall(r"<dxf\b[^>]*>.*?</dxf>", styles_xml, re.DOTALL)


def _parse_cf_blocks(
    xml: str, part: str, sheet_name: str, dxf_styles: List[str]
) -> List[CFBlock]:
    """Parse all <conditionalFormatting> blocks from a sheet XML."""
    raw_blocks = extract_blocks(xml, "conditionalFormatting")
    result: List[CFBlock] = []

    for raw in raw_blocks:
        sqref = get_attr(raw, "sqref") or ""
        block = CFBlock(
            id=str(uuid.uuid4())[:8],
            sheet_part=part,
            sheet_name=sheet_name,
            sqref=sqref,
            raw_xml=raw,
        )

        # Parse individual <cfRule> elements inside this block
        rule_xmls = re.findall(
            r"<cfRule\b[^>]*(?:>.*?</cfRule>|/>)", raw, re.DOTALL
        )
        for rx in rule_xmls:
            rule = CFRule(
                id=str(uuid.uuid4())[:8],
                raw_xml=rx,
            )
            rule.rule_type = get_attr(rx, "type") or ""
            rule.operator = get_attr(rx, "operator") or ""
            rule.text = get_attr(rx, "text") or ""
            rule.stop_if_true = get_attr(rx, "stopIfTrue") == "1"

            pri = get_attr(rx, "priority")
            rule.priority = int(pri) if pri else 0

            dxf_str = get_attr(rx, "dxfId")
            if dxf_str is not None:
                rule.dxf_id = int(dxf_str)
                if 0 <= rule.dxf_id < len(dxf_styles):
                    rule.dxf_xml = dxf_styles[rule.dxf_id]

            # Extract formulas
            formulas = re.findall(r"<formula>(.*?)</formula>", rx, re.DOTALL)
            if formulas:
                rule.formula = formulas[0]
            if len(formulas) > 1:
                rule.formula2 = formulas[1]

            block.rules.append(rule)

        result.append(block)

    return result


def _rewrite_dxf_ids(xml_fragment: str, offset: int) -> str:
    """Shift every dxfId="N" in *xml_fragment* by *offset*."""
    if offset == 0:
        return xml_fragment
    return re.sub(
        r'dxfId="(\d+)"',
        lambda m: f'dxfId="{int(m.group(1)) + offset}"',
        xml_fragment,
    )


def _append_cf_blocks(sheet_bytes: bytes, blocks: List[CFBlock], dxf_offset: int) -> bytes:
    """Append CF blocks to a sheet XML WITHOUT removing existing CF.

    The dxfId values in the new blocks are shifted by *dxf_offset* so they
    reference the correct position in the merged DXF list.
    """
    xml = sheet_bytes.decode("utf-8", errors="ignore")

    # Build new CF XML from the dictionary blocks (use raw_xml for fidelity)
    cf_xml = ""
    for b in blocks:
        if b.raw_xml:
            raw = _rewrite_dxf_ids(b.raw_xml, dxf_offset)
        else:
            rules_xml = "".join(
                _rewrite_dxf_ids(r.raw_xml, dxf_offset)
                for r in b.rules if r.raw_xml
            )
            raw = f'<conditionalFormatting sqref="{b.sqref}">{rules_xml}</conditionalFormatting>'
        cf_xml += raw

    # Insert AFTER existing CF if any, otherwise before pageMargins / </worksheet>
    last_cf = [m.end() for m in re.finditer(r"</conditionalFormatting>", xml)]
    if last_cf:
        insert_at = last_cf[-1]
        xml = xml[:insert_at] + cf_xml + xml[insert_at:]
    else:
        for anchor in ("<pageMargins", "<pageSetup", "<drawing", "</worksheet>"):
            idx = xml.find(anchor)
            if idx != -1:
                xml = xml[:idx] + cf_xml + xml[idx:]
                break

    return xml.encode("utf-8")


def _patch_styles_dxf(styles_bytes: bytes, merged_dxf_styles: List[str]) -> bytes:
    """Write the merged DXF list into styles.xml.

    *merged_dxf_styles* is already the complete list (existing + appended);
    this function just serialises it back into the XML.
    """
    xml = styles_bytes.decode("utf-8", errors="ignore")

    dxf_block = (
        f'<dxfs count="{len(merged_dxf_styles)}">'
        + "".join(merged_dxf_styles)
        + "</dxfs>"
    )

    pattern = r"<dxfs\b[^>]*>.*?</dxfs>"
    if re.search(pattern, xml, re.DOTALL):
        xml = re.sub(pattern, dxf_block, xml, count=1, flags=re.DOTALL)
    else:
        idx = xml.find("</styleSheet>")
        if idx != -1:
            xml = xml[:idx] + dxf_block + xml[idx:]

    return xml.encode("utf-8")


# ──────────────────── CLI ────────────────────


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m triage.cf_engine <path.xlsx> [--apply <dict.json> <out.xlsx>]")
        sys.exit(1)

    if sys.argv[1] == "--apply" and len(sys.argv) >= 4:
        dict_path = sys.argv[2]
        src_path = sys.argv[3]
        out_path = sys.argv[4] if len(sys.argv) > 4 else src_path.replace(".xlsx", "_cf.xlsx")
        cfd = CFDictionary.from_json(open(dict_path, encoding="utf-8").read())
        with open(src_path, "rb") as fh:
            patched = apply_cf_dictionary(fh.read(), cfd)
        with open(out_path, "wb") as fh:
            fh.write(patched)
        print(f"Applied CF dictionary ({len(cfd.blocks)} blocks, {len(cfd.dxf_styles)} DXF styles) → {out_path}")
    else:
        cfd = extract_cf_dictionary(sys.argv[1])
        s = cfd.summary
        print(f"Extracted CF dictionary from {sys.argv[1]}")
        print(f"  Total blocks: {s['total_blocks']}")
        print(f"  Total rules:  {s['total_rules']}")
        print(f"  DXF styles:   {s['total_dxf_styles']}")
        print(f"\n  Per sheet:")
        for sheet, info in s["per_sheet"].items():
            print(f"    {sheet:35s}  {info['blocks']:3d} blocks  {info['rules']:3d} rules")
        # Dump JSON
        print("\n" + cfd.to_json()[:2000] + "\n... (truncated)")

