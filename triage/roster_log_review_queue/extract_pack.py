"""Extract operator CF pack and review configs from blessed reference ZIP."""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from triage.cf_engine import _extract_dxf_list, _parse_cf_blocks
from triage.xlsx_utils import read_text, sheet_name_map

REVIEW_RULE_CODES = [
    "MISSING_PROJECT_CORRECTION",
    "PROJECT_CONFLICT",
    "PARTIAL_HOURS_REVIEW",
    "LONG_SHIFT_REVIEW",
    "OT_REVIEW",
    "PTO_ACCEPTED",
    "OFF_DAY_ACCEPTED",
    "DAY_OFF_EVIDENCE_ACCEPTED",
    "NOTE_BEARING_PUNCH",
    "CASR_DAY_OFF_ACCEPTED",
    "INVALID_PUNCH_PAIR",
    "MISSING_EXPECTED_HOURS",
    "STALE_EXPECTED_HOURS_SNAPSHOT",
    "UNASSIGNED_WORKED_HOURS",
    "TECH_WITHOUT_DEFAULT_PROJECT",
    "UNALLOCATED_TECHNICIAN",
    "MISSING_REZAUL_NEURON_ATTRIBUTION",
]


def _xlsx_from_zip(z: zipfile.ZipFile) -> bytes:
    for name in z.namelist():
        if name.lower().endswith(".xlsx"):
            return z.read(name)
    raise FileNotFoundError("No .xlsx in reference ZIP")


def extract_operator_cf_pack(xlsx_bytes: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        styles = read_text(z, "xl/styles.xml")
        dxf_styles = _extract_dxf_list(styles)
        nm = sheet_name_map(z)
        part = [p for p, n in nm.items() if n == "Live - June 2026"][0]
        xml = read_text(z, part)
        blocks = _parse_cf_blocks(xml, part, "Live - June 2026", dxf_styles)

    # Appended operator blocks start at index 64 (project + clock pairs)
    project_block = blocks[64]
    pair_block = blocks[65]

    used_dxf: set = set()
    for b in (project_block, pair_block):
        for r in b.rules:
            if r.dxf_id is not None:
                used_dxf.add(r.dxf_id)

    template_dxf = [dxf_styles[i] for i in sorted(used_dxf)]
    dxf_id_map = {str(i): idx for idx, i in enumerate(sorted(used_dxf))}

    return {
        "source": "Live - June 2026 appended blocks 64-65",
        "data_row_start": 3,
        "data_row_end": 202,
        "project_column_block": {
            "sqref_template": "B3:B{end_row}",
            "raw_xml": project_block.raw_xml,
            "rules_count": len(project_block.rules),
        },
        "clock_pair_block": {
            "sqref_template": "{in_col}3:{out_col}{end_row}",
            "raw_xml": pair_block.raw_xml,
            "rules_count": len(pair_block.rules),
            "reference_in_col": "C",
            "reference_out_col": "D",
        },
        "dxf_styles": template_dxf,
        "dxf_id_map": dxf_id_map,
    }


def extract_cf_markers(pack: dict) -> dict:
    substrings = [
        "AND($A3<>\"\",$B3=\"\")",
        'OR($C3="",$D3="")',
        "MOD($D3-$C3,1)*24>=12",
        "MOD($D3-$C3,1)*24>8,MOD($D3-$C3,1)*24<12",
        'SEARCH("PTO"',
        'SEARCH("OUT SICK"',
        'SEARCH("CASR"',
        'SEARCH("DAY OFF"',
        'SEARCH("/",C3)',
    ]
    return {"formula_substrings": substrings, "rule_intents": []}


def extract_review_rules_seed() -> dict:
    return {"rule_codes": REVIEW_RULE_CODES, "rows": []}


def extract_all(reference_zip: str, out_dir: str) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(reference_zip, "r") as z:
        xlsx = _xlsx_from_zip(z)

    pack = extract_operator_cf_pack(xlsx)
    (out / "operator_cf_pack.json").write_text(
        json.dumps(pack, indent=2), encoding="utf-8"
    )
    (out / "cf_markers.json").write_text(
        json.dumps(extract_cf_markers(pack), indent=2), encoding="utf-8"
    )
    (out / "review_rules_seed.json").write_text(
        json.dumps(extract_review_rules_seed(), indent=2), encoding="utf-8"
    )
    (out / "priority_policy.json").write_text(
        json.dumps(
            {
                "priority_policy": "Sequential operator CF priorities across Live tabs.",
                "data_row_end": 202,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "operator_cf_pack": str(out / "operator_cf_pack.json"),
        "dxf_styles": len(pack["dxf_styles"]),
        "rule_codes": len(REVIEW_RULE_CODES),
    }
