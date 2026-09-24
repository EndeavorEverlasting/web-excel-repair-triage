"""Append operator global CF to every Live month tab (column-cloning patcher)."""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from triage.cf_engine import CFBlock, CFDictionary, apply_cf_dictionary
from triage.xlsx_utils import read_text

from .column_utils import substitute_column_refs, rewrite_priorities
from .live_column_map import detect_clock_pairs_from_workbook, last_clock_column
from .models import LiveCFPatchStats
from .priority_allocator import (
    count_cf_groups,
    live_sheet_names_in_order,
    load_cf_markers,
    max_operator_priority,
    next_priority_start,
    sheet_part_for_name,
)

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "roster_log_review_queue"


def load_operator_cf_pack() -> dict:
    path = _CONFIG_DIR / "operator_cf_pack.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing operator CF pack: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _remap_dxf_ids(xml: str, dxf_id_map: Dict[str, int]) -> str:
    def _repl(m: re.Match) -> str:
        old = m.group(1)
        new = dxf_id_map.get(old, old)
        return f'dxfId="{new}"'

    return re.sub(r'dxfId="(\d+)"', _repl, xml)


def _clone_block(
    template_xml: str,
    sqref: str,
    ref_in: str,
    ref_out: str,
    new_in: str,
    new_out: str,
    priority_start: int,
    dxf_id_map: Dict[str, int],
    end_row: int,
) -> Tuple[str, int, int]:
    xml = template_xml
    xml = re.sub(r'sqref="[^"]+"', f'sqref="{sqref}"', xml, count=1)
    xml = substitute_column_refs(xml, ref_in, ref_out, new_in, new_out)
    xml = _remap_dxf_ids(xml, dxf_id_map)
    xml, pri_end = rewrite_priorities(xml, priority_start)
    rules = len(re.findall(r"<cfRule\b", xml))
    return xml, pri_end, rules


def _sheet_already_patched(xml: str, markers: List[str]) -> bool:
    return any(m in xml for m in markers)


def build_blocks_for_sheet(
    pack: dict,
    pairs: list,
    project_col: str,
    data_row_end: int,
    priority_start: int,
) -> Tuple[List[CFBlock], int, LiveCFPatchStats]:
    ref_in = pack["clock_pair_block"]["reference_in_col"]
    ref_out = pack["clock_pair_block"]["reference_out_col"]
    dxf_map = {k: int(v) for k, v in pack.get("dxf_id_map", {}).items()}

    blocks: List[CFBlock] = []
    counter = priority_start
    pri_start = priority_start

    proj_sqref = f"{project_col}3:{project_col}{data_row_end}"
    proj_xml, counter, _ = _clone_block(
        pack["project_column_block"]["raw_xml"],
        proj_sqref,
        ref_in,
        ref_out,
        ref_in,
        ref_out,
        counter,
        dxf_map,
        data_row_end,
    )
    blocks.append(CFBlock(sqref=proj_sqref, raw_xml=proj_xml))

    for pair in pairs:
        sqref = f"{pair.in_col}3:{pair.out_col}{data_row_end}"
        pair_xml, counter, _ = _clone_block(
            pack["clock_pair_block"]["raw_xml"],
            sqref,
            ref_in,
            ref_out,
            pair.in_col,
            pair.out_col,
            counter,
            dxf_map,
            data_row_end,
        )
        blocks.append(CFBlock(sqref=sqref, raw_xml=pair_xml))

    stats = LiveCFPatchStats(
        sheet_name="",
        worksheet_part="",
        patched=True,
        clock_pairs=len(pairs),
        new_cf_groups=len(blocks),
        new_cf_rules=counter - priority_start,
        priority_start=pri_start,
        priority_end=counter - 1,
        last_clock_col=last_clock_column(pairs),
        last_data_row=data_row_end,
    )
    return blocks, counter, stats


def patch_live_cf(
    xlsx_bytes: bytes,
    *,
    scan_path: str,
    skip_patched: bool = True,
) -> Tuple[bytes, Dict[str, LiveCFPatchStats]]:
    """Append operator CF to all Live tabs; returns patched bytes + per-sheet stats."""
    pack = load_operator_cf_pack()
    markers = load_cf_markers()
    data_row_end = int(pack.get("data_row_end", 202))
    dxf_styles = pack.get("dxf_styles", [])

    live_names = live_sheet_names_in_order(xlsx_bytes)
    all_blocks: List[CFBlock] = []
    stats_map: Dict[str, LiveCFPatchStats] = {}
    counter = next_priority_start(xlsx_bytes)

    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        for sheet_name in live_names:
            part = sheet_part_for_name(xlsx_bytes, sheet_name)
            xml = read_text(z, part)
            before = len(re.findall(r"<conditionalFormatting\b", xml))

            if skip_patched and _sheet_already_patched(xml, markers):
                stats_map[sheet_name] = LiveCFPatchStats(
                    sheet_name=sheet_name,
                    worksheet_part=part,
                    patched=False,
                    cf_groups_before=before,
                    cf_groups_after=before,
                    clock_pairs=0,
                )
                continue

            pairs, _, project_col = detect_clock_pairs_from_workbook(scan_path, sheet_name)
            sheet_blocks, counter, stats = build_blocks_for_sheet(
                pack, pairs, project_col, data_row_end, counter
            )
            for b in sheet_blocks:
                b.sheet_name = sheet_name
            all_blocks.extend(sheet_blocks)

            stats.sheet_name = sheet_name
            stats.worksheet_part = part
            stats.cf_groups_before = before
            stats.cf_groups_after = before + stats.new_cf_groups
            stats_map[sheet_name] = stats

    if not all_blocks:
        return xlsx_bytes, stats_map

    cfd = CFDictionary(dxf_styles=dxf_styles, blocks=all_blocks)
    patched = apply_cf_dictionary(xlsx_bytes, cfd, mode="append")
    return patched, stats_map
