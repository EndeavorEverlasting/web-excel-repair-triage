"""triage/cf_policy_deploymenttracker.py
------------------------------------
Deployment Tracker conditional-formatting *policy* checks.

Goal
----
Users care about *endeavor-specific* failures. This module encodes a small,
explicit set of CF rules ("business rules") and can verify that a workbook
contains them with the intended severity → highlight color.

This is intentionally lightweight:
- read-only scanning (regex / byte-level)
- no openpyxl / lxml
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from triage.xlsx_utils import sheet_name_map, parse_ref, col_to_num, num_to_col


SEV_HIGH = {"name": "HIGH", "rgb": "FFFFC7CE"}   # light red
SEV_MED  = {"name": "MEDIUM", "rgb": "FF7030A0"} # deep purple
SEV_LOW  = {"name": "LOW", "rgb": "FFFFEB9C"}    # light yellow


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _xml_unescape(s: str) -> str:
    return (
        (s or "")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
    )


def _extract_dxf_list(styles_xml: str) -> List[str]:
    return re.findall(r"<dxf\b[^>]*>.*?</dxf>", styles_xml, re.DOTALL)


def _dxf_fill_rgb(dxf_xml: str) -> Optional[str]:
    # Look for either fgColor or bgColor in a solid fill; fall back to any rgb.
    m = re.search(r"<fgColor\b[^>]*\brgb=\"([0-9A-Fa-f]{8})\"", dxf_xml)
    if m:
        return m.group(1).upper()
    m = re.search(r"<bgColor\b[^>]*\brgb=\"([0-9A-Fa-f]{8})\"", dxf_xml)
    if m:
        return m.group(1).upper()
    m = re.search(r"\brgb=\"([0-9A-Fa-f]{8})\"", dxf_xml)
    return m.group(1).upper() if m else None


def _resolve_sheet_rels_path(sheet_part: str) -> str:
    # xl/worksheets/sheet12.xml -> xl/worksheets/_rels/sheet12.xml.rels
    base = sheet_part.split("/")[-1]
    return "xl/worksheets/_rels/" + base + ".rels"


def _resolve_ooxml_target(owner_part: str, target: str) -> str:
    """Resolve a relationship Target relative to the owning part."""
    target = (target or "").replace("\\", "/")
    while target.startswith("/"):
        target = target[1:]
    if "://" in target:
        return target
    base_dir = owner_part.rsplit("/", 1)[0] + "/"
    # Join + normalize .. segments
    parts: List[str] = [p for p in base_dir.split("/") if p]
    for seg in target.split("/"):
        if seg == "..":
            if parts:
                parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def _find_device_config_sheet(z: zipfile.ZipFile) -> Optional[str]:
    m = sheet_name_map(z)
    # Prefer exact-ish sheet naming
    for part, name in m.items():
        if "device_configuration" in _norm(name) or "deviceconfig" in _norm(name):
            return part
    # Fallback heuristic
    for part, name in m.items():
        n = _norm(name)
        if "device" in n and "config" in n:
            return part
    return None


def _find_tbl_device_config_part(z: zipfile.ZipFile, sheet_part: str) -> Optional[str]:
    rels_path = _resolve_sheet_rels_path(sheet_part)
    if rels_path not in z.namelist():
        return None
    rels = z.read(rels_path).decode("utf-8", errors="ignore")
    # Find any table relationship target (../tables/tableN.xml)
    for m in re.finditer(r"<Relationship\b[^>]*>", rels):
        frag = m.group(0)
        typ = re.search(r'Type="([^"]+)"', frag)
        if not typ or "relationships/table" not in typ.group(1):
            continue
        tm = re.search(r'Target="([^"]+)"', frag)
        if not tm:
            continue
        part = _resolve_ooxml_target(sheet_part, tm.group(1))
        if part.startswith("xl/") and part in z.namelist():
            # Prefer the table whose name/displayName is tblDeviceConfig
            t = z.read(part).decode("utf-8", errors="ignore")
            nm = re.search(r'\bname="([^"]+)"', t)
            dnm = re.search(r'\bdisplayName="([^"]+)"', t)
            if _norm((nm.group(1) if nm else "")) == _norm("tblDeviceConfig"):
                return part
            if _norm((dnm.group(1) if dnm else "")) == _norm("tblDeviceConfig"):
                return part
    # If not found by name, fall back to first table target.
    for m in re.finditer(r"<Relationship\b[^>]*>", rels):
        frag = m.group(0)
        typ = re.search(r'Type="([^"]+)"', frag)
        if not typ or "relationships/table" not in typ.group(1):
            continue
        tm = re.search(r'Target="([^"]+)"', frag)
        if tm:
            part = _resolve_ooxml_target(sheet_part, tm.group(1))
            if part.startswith("xl/") and part in z.namelist():
                return part
    return None


def _table_column_map(table_xml: str) -> Tuple[Dict[str, str], int, int]:
    """Return (normalized_header -> col_letter, data_row_start, data_row_end)."""
    ref = None
    mref = re.search(r'\bref="([A-Z]+\d+:[A-Z]+\d+)"', table_xml)
    if mref:
        ref = mref.group(1)
    pr = parse_ref(ref) if ref else None
    if not pr:
        # assume A1:A1 if missing
        start_col, start_row, end_col, end_row = ("A", 1, "A", 1)
    else:
        start_col, start_row, end_col, end_row = pr

    cols = re.findall(r'<tableColumn\b[^>]*\bname="([^"]*)"', table_xml)
    start_n = col_to_num(start_col)
    mapping: Dict[str, str] = {}
    for i, name in enumerate(cols):
        mapping[_norm(name)] = num_to_col(start_n + i)

    # data starts on the next row after header
    return mapping, start_row + 1, end_row


@dataclass(frozen=True)
class ExpectedRule:
    rule_id: str
    purpose: str
    severity_name: str
    expected_rgb: str
    sqref_col_headers: List[str]  # headers to apply highlight to (1+)
    formula: str                 # unescaped Excel formula (uses $col + row)


def _truthy(cell: str) -> str:
    # Excel formula snippet for a YES-ish checkbox/text.
    c = cell
    return f"OR({c}=TRUE,UPPER({c})=\"YES\",{c}=1)"


def _expected_rules(col: Dict[str, str], r0: int, r1: int) -> List[ExpectedRule]:
    # Fuzzy header lookup
    def h(*names: str) -> Optional[str]:
        for n in names:
            k = _norm(n)
            if k in col:
                return col[k]
        return None

    deployed = h("Deployed", "Is Deployed", "Deployment Status")
    installed = h("Installed", "Is Installed")
    device_type = h("Device Type", "Type")
    hostname = h("Hostname", "Host Name")
    mac = h("MAC", "MAC Address")
    ip = h("IP", "IP Address")
    pi_date = h("PI Validated Date", "PI Validated", "PI_Validated_Date")
    cur_bldg = h("Current Building", "Current Bldg", "Current_Building")
    inst_bldg = h("Install Building", "Installed Building", "Install_Building")
    med_class = h("Medical Device Class", "Med Device Class", "Medical_Class")
    anes_flag = h("Anesthesia Machine", "Anesthesia")
    anes_sn = h("Anesthesia Serial", "Anesthesia Serial Number", "Anes Serial")

    rules: List[ExpectedRule] = []
    if deployed and pi_date:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_001_DEPLOYED_REQUIRES_PI_DATE",
                purpose="If Deployed=Yes/True then PI Validated Date must be filled (high priority)",
                severity_name=SEV_HIGH["name"],
                expected_rgb=SEV_HIGH["rgb"],
                sqref_col_headers=["PI Validated Date"],
                formula=f"AND({_truthy(f'${deployed}{r0}')},${pi_date}{r0}=\"\")",
            )
        )

    if deployed and cur_bldg and inst_bldg:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_002_DEPLOYED_BUILDING_MISMATCH",
                purpose="If Deployed then Current Building must match Install Building (high priority)",
                severity_name=SEV_HIGH["name"],
                expected_rgb=SEV_HIGH["rgb"],
                sqref_col_headers=["Current Building", "Install Building"],
                formula=(
                    f"AND({_truthy(f'${deployed}{r0}')},"
                    f"${cur_bldg}{r0}<>\"\",${inst_bldg}{r0}<>\"\",${cur_bldg}{r0}<>${inst_bldg}{r0})"
                ),
            )
        )

    if installed and cur_bldg and inst_bldg:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_003_INSTALLED_BUILDING_MISMATCH",
                purpose="If Installed then Current Building must match Install Building (medium priority)",
                severity_name=SEV_MED["name"],
                expected_rgb=SEV_MED["rgb"],
                sqref_col_headers=["Current Building", "Install Building"],
                formula=(
                    f"AND({_truthy(f'${installed}{r0}')},"
                    f"${cur_bldg}{r0}<>\"\",${inst_bldg}{r0}<>\"\",${cur_bldg}{r0}<>${inst_bldg}{r0})"
                ),
            )
        )

    if device_type and hostname:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_004_HOSTNAME_REQUIRED_CYBERNET",
                purpose="If Device Type contains 'Cybernet' then Hostname required (high priority)",
                severity_name=SEV_HIGH["name"],
                expected_rgb=SEV_HIGH["rgb"],
                sqref_col_headers=["Hostname"],
                formula=(
                    f"AND(ISNUMBER(SEARCH(\"CYBERNET\",UPPER(${device_type}{r0}))),${hostname}{r0}=\"\")"
                ),
            )
        )
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_005_HOSTNAME_REQUIRED_NEURON",
                purpose="If Device Type contains 'Neuron' then Hostname required (medium priority)",
                severity_name=SEV_MED["name"],
                expected_rgb=SEV_MED["rgb"],
                sqref_col_headers=["Hostname"],
                formula=(
                    f"AND(ISNUMBER(SEARCH(\"NEURON\",UPPER(${device_type}{r0}))),${hostname}{r0}=\"\")"
                ),
            )
        )

    if hostname and mac:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_006_MAC_REQUIRED_IF_HOSTNAME",
                purpose="If Hostname present then MAC must be present (medium priority)",
                severity_name=SEV_MED["name"],
                expected_rgb=SEV_MED["rgb"],
                sqref_col_headers=["MAC"],
                formula=f"AND(${hostname}{r0}<>\"\",${mac}{r0}=\"\")",
            )
        )
    if hostname and ip:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_007_IP_REQUIRED_IF_HOSTNAME",
                purpose="If Hostname present then IP must be present (medium priority)",
                severity_name=SEV_MED["name"],
                expected_rgb=SEV_MED["rgb"],
                sqref_col_headers=["IP"],
                formula=f"AND(${hostname}{r0}<>\"\",${ip}{r0}=\"\")",
            )
        )

    if device_type and med_class:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_008_MEDCLASS_REQUIRED_FOR_TYPES",
                purpose="If Device Type is Cybernet/Neuron then Medical Device Class required (medium priority)",
                severity_name=SEV_MED["name"],
                expected_rgb=SEV_MED["rgb"],
                sqref_col_headers=["Medical Device Class"],
                formula=(
                    f"AND(OR(ISNUMBER(SEARCH(\"CYBERNET\",UPPER(${device_type}{r0}))),"
                    f"ISNUMBER(SEARCH(\"NEURON\",UPPER(${device_type}{r0})))),${med_class}{r0}=\"\")"
                ),
            )
        )

    if anes_flag and anes_sn:
        rules.append(
            ExpectedRule(
                rule_id="DT_CF_009_ANES_SN_REQUIRED",
                purpose="If Anesthesia Machine present then Anesthesia Serial required (high priority)",
                severity_name=SEV_HIGH["name"],
                expected_rgb=SEV_HIGH["rgb"],
                sqref_col_headers=["Anesthesia Serial"],
                formula=f"AND({_truthy(f'${anes_flag}{r0}')},${anes_sn}{r0}=\"\")",
            )
        )

    return rules


def check_cf_policy_deploymenttracker(z: zipfile.ZipFile) -> List[dict]:
    """Return findings for missing/misconfigured Deployment Tracker CF rules.

    If the workbook doesn't look like a Deployment Tracker (missing the
    Device_Configuration sheet or its table), returns [] (not applicable).
    """
    sheet_part = _find_device_config_sheet(z)
    if not sheet_part or sheet_part not in z.namelist():
        return []

    table_part = _find_tbl_device_config_part(z, sheet_part)
    if not table_part:
        return []

    table_xml = z.read(table_part).decode("utf-8", errors="ignore")
    colmap, data_row_start, data_row_end = _table_column_map(table_xml)
    if data_row_end < data_row_start:
        return []

    expected = _expected_rules(colmap, data_row_start, data_row_end)
    if not expected:
        return [{
            "endeavor": "CF_POLICY_DEPLOYMENTTRACKER",
            "issue": "policy_not_applicable_missing_columns",
            "sheet_part": sheet_part,
            "table_part": table_part,
        }]

    styles_xml = z.read("xl/styles.xml").decode("utf-8", errors="ignore") if "xl/styles.xml" in z.namelist() else ""
    dxfs = _extract_dxf_list(styles_xml)

    sheet_xml = z.read(sheet_part).decode("utf-8", errors="ignore")
    # Map found rules: norm(formula) -> list of (sqref, dxfId)
    found: Dict[str, List[Tuple[str, Optional[int]]]] = {}
    for cf_m in re.finditer(r"<conditionalFormatting\b[^>]*>.*?</conditionalFormatting>", sheet_xml, re.DOTALL):
        block = cf_m.group(0)
        sqref = re.search(r'\bsqref="([^"]+)"', block)
        sq = sqref.group(1) if sqref else ""
        for rm in re.finditer(r"<cfRule\b[^>]*>.*?</cfRule>", block, re.DOTALL):
            rule_xml = rm.group(0)
            fm = re.search(r"<formula>(.*?)</formula>", rule_xml, re.DOTALL)
            if not fm:
                continue
            ftxt = _xml_unescape(fm.group(1)).strip()
            did_m = re.search(r'\bdxfId="(\d+)"', rule_xml)
            did = int(did_m.group(1)) if did_m else None
            key = _norm(ftxt)
            found.setdefault(key, []).append((sq, did))

    findings: List[dict] = []
    for er in expected:
        exp_key = _norm(er.formula)
        matches = found.get(exp_key, [])
        if not matches:
            findings.append({
                "endeavor": "CF_POLICY_DEPLOYMENTTRACKER",
                "issue": "missing_rule",
                "rule_id": er.rule_id,
                "severity": er.severity_name,
                "expected_rgb": er.expected_rgb,
                "expected_formula": er.formula,
                "sheet_part": sheet_part,
                "table_part": table_part,
                "purpose": er.purpose,
            })
            continue

        # Pick first match; verify sqref includes at least one target column and color matches.
        sq, did = matches[0]
        if er.sqref_col_headers:
            ok_any = False
            for hdr in er.sqref_col_headers:
                letter = colmap.get(_norm(hdr))
                if letter and letter in sq:
                    ok_any = True
            if not ok_any:
                findings.append({
                    "endeavor": "CF_POLICY_DEPLOYMENTTRACKER",
                    "issue": "sqref_mismatch",
                    "rule_id": er.rule_id,
                    "expected_formula": er.formula,
                    "found_sqref": sq,
                    "expected_cols": er.sqref_col_headers,
                    "sheet_part": sheet_part,
                })

        found_rgb = None
        if did is not None and 0 <= did < len(dxfs):
            found_rgb = _dxf_fill_rgb(dxfs[did])
        if found_rgb and found_rgb.upper() != er.expected_rgb.upper():
            findings.append({
                "endeavor": "CF_POLICY_DEPLOYMENTTRACKER",
                "issue": "severity_color_mismatch",
                "rule_id": er.rule_id,
                "severity": er.severity_name,
                "expected_rgb": er.expected_rgb,
                "found_rgb": found_rgb,
                "dxfId": did,
                "sheet_part": sheet_part,
            })

    return findings
