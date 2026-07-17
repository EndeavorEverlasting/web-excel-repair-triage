"""Package-preserving prompt-tab copy-range hyperlinks for AI Harness Prompt Kits.

The accepted prompt workbook already contains exact full-range links in
``Prompt_Library``. This module mirrors each library target into the top and
bottom ``Copy A1:A<n> only`` cells of every ``P##_COPY_SAFE`` sheet without an
Excel/openpyxl serializer round trip.

Only the prompt worksheet parts and, when present, ``xl/calcChain.xml`` may
change. The workbook, relationships, content types, styles, shared strings,
theme, properties, sheet order, protection metadata, and ZIP member set remain
byte-for-byte inherited from the accepted source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS}
PROMPT_LIBRARY = "Prompt_Library"
PROMPT_SHEET_RE = re.compile(r"^P\d{2,}_COPY_SAFE$")
PROMPT_ID_RE = re.compile(r"^P\d{2,}$")
PROMPT_RANGE_RE = re.compile(r"^A1:A([1-9]\d*)$")
LIBRARY_LINK_RE = re.compile(
    r'^HYPERLINK\("#\'(?P<sheet>[^\']+)\'!(?P<range>A1:A[1-9]\d*)","(?P<id>P\d{2,})"\)$',
    re.IGNORECASE,
)
SELF_LINK_RE = re.compile(
    r'^HYPERLINK\("#\'(?P<sheet>[^\']+)\'!(?P<range>A1:A[1-9]\d*)","(?P<label>Copy A1:A[1-9]\d* only)"\)$',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CopyRangeLink:
    prompt_id: str
    sheet: str
    prompt_range: str
    last_row: int
    top_cell: str
    bottom_cell: str


@dataclass(frozen=True)
class CopyRangeLinkResult:
    source: str
    output: str
    source_sha256: str
    output_sha256: str
    prompt_count: int
    links_written: int
    changed_parts: tuple[str, ...]
    calc_chain_updated: bool
    formula_count_before: int
    formula_count_after: int
    validation_passed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _root(data: bytes, part: str) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML part {part}: {exc}") from exc


def _sheet_map(parts: Mapping[str, bytes]) -> tuple[list[str], dict[str, str], dict[str, int]]:
    workbook = _root(parts["xl/workbook.xml"], "xl/workbook.xml")
    rels = _root(parts["xl/_rels/workbook.xml.rels"], "xl/_rels/workbook.xml.rels")
    targets = {rel.attrib["Id"]: rel.attrib.get("Target", "") for rel in rels}
    order: list[str] = []
    mapping: dict[str, str] = {}
    sheet_ids: dict[str, int] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        name = sheet.attrib["name"]
        rid = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = targets.get(rid, "")
        if not target:
            raise ValueError(f"worksheet relationship missing for {name}")
        if target.startswith("/"):
            part = target.lstrip("/")
        elif target.startswith("xl/"):
            part = target
        else:
            part = posixpath.normpath(posixpath.join("xl", target))
        if part not in parts:
            raise ValueError(f"worksheet part missing for {name}: {part}")
        order.append(name)
        mapping[name] = part
        sheet_ids[name] = int(sheet.attrib["sheetId"])
    return order, mapping, sheet_ids


def _shared_strings(parts: Mapping[str, bytes]) -> tuple[str, ...]:
    data = parts.get("xl/sharedStrings.xml")
    if data is None:
        return ()
    root = _root(data, "xl/sharedStrings.xml")
    return tuple(
        "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    )


def _cell_text(cell: ET.Element, shared: Sequence[str]) -> str:
    formula = cell.find("m:f", NS)
    if formula is not None and formula.text:
        return formula.text
    if cell.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(value.text)]
        except (IndexError, ValueError):
            return ""
    return value.text


def discover_copy_range_links(parts: Mapping[str, bytes]) -> tuple[CopyRangeLink, ...]:
    _, sheets, _ = _sheet_map(parts)
    if PROMPT_LIBRARY not in sheets:
        raise ValueError(f"missing required sheet: {PROMPT_LIBRARY}")
    library = _root(parts[sheets[PROMPT_LIBRARY]], sheets[PROMPT_LIBRARY])
    links: list[CopyRangeLink] = []
    seen: set[str] = set()
    for cell in library.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        if not ref.startswith("C"):
            continue
        formula = cell.find("m:f", NS)
        if formula is None or not formula.text:
            continue
        match = LIBRARY_LINK_RE.fullmatch(formula.text)
        if not match:
            continue
        prompt_id = match.group("id").upper()
        sheet = match.group("sheet")
        prompt_range = match.group("range").upper()
        if not PROMPT_ID_RE.fullmatch(prompt_id) or not PROMPT_SHEET_RE.fullmatch(sheet):
            continue
        if sheet != f"{prompt_id}_COPY_SAFE":
            raise ValueError(f"{prompt_id} library link targets unexpected sheet: {sheet}")
        if sheet not in sheets:
            raise ValueError(f"{prompt_id} library link targets missing sheet: {sheet}")
        if prompt_id in seen:
            raise ValueError(f"duplicate Prompt Library link: {prompt_id}")
        seen.add(prompt_id)
        range_match = PROMPT_RANGE_RE.fullmatch(prompt_range)
        if range_match is None:
            raise ValueError(f"invalid Prompt Library range for {prompt_id}: {prompt_range}")
        last_row = int(range_match.group(1))
        links.append(CopyRangeLink(prompt_id, sheet, prompt_range, last_row, "C1", f"C{last_row}"))
    if not links:
        raise ValueError("Prompt Library contains no exact P##_COPY_SAFE full-range links")
    return tuple(sorted(links, key=lambda item: int(item.prompt_id[1:])))


def _coerce_links(items: Iterable[object]) -> tuple[CopyRangeLink, ...]:
    result: list[CopyRangeLink] = []
    for item in items:
        prompt_id = str(getattr(item, "prompt_id"))
        sheet = str(getattr(item, "sheet"))
        prompt_range = str(getattr(item, "range", getattr(item, "prompt_range", "")))
        match = PROMPT_RANGE_RE.fullmatch(prompt_range)
        if not match:
            raise ValueError(f"invalid prompt range for {prompt_id}: {prompt_range}")
        last_row = int(match.group(1))
        result.append(CopyRangeLink(prompt_id, sheet, prompt_range, last_row, "C1", f"C{last_row}"))
    return tuple(result)


def _find_cell(root: ET.Element, ref: str) -> ET.Element:
    cell = root.find(f".//m:c[@r='{ref}']", NS)
    if cell is None:
        raise ValueError(f"required copy-range label cell is missing: {ref}")
    return cell


def _validate_label_cells(parts: Mapping[str, bytes], sheets: Mapping[str, str], links: Sequence[CopyRangeLink]) -> None:
    shared = _shared_strings(parts)
    for link in links:
        root = _root(parts[sheets[link.sheet]], sheets[link.sheet])
        expected_label = f"Copy {link.prompt_range} only"
        for ref in (link.top_cell, link.bottom_cell):
            cell = _find_cell(root, ref)
            actual = _cell_text(cell, shared)
            formula = cell.find("m:f", NS)
            if formula is not None and formula.text:
                match = SELF_LINK_RE.fullmatch(formula.text)
                if not match or match.group("sheet") != link.sheet or match.group("range").upper() != link.prompt_range:
                    raise ValueError(f"{link.sheet}!{ref} contains an unexpected formula: {formula.text}")
            elif actual != expected_label:
                raise ValueError(f"{link.sheet}!{ref} label {actual!r} != {expected_label!r}")


def _patch_cell_xml(data: bytes, ref: str, formula: str, cached_value: str) -> tuple[bytes, bool]:
    ref_bytes = re.escape(ref.encode("ascii"))
    pattern = re.compile(
        rb'<(?P<prefix>(?:[A-Za-z_][\w.-]*:)?)c\b(?P<attrs>[^>]*\br="' + ref_bytes + rb'"[^>]*)>'
        rb'(?P<body>.*?)</(?P=prefix)c>',
        re.DOTALL,
    )
    match = pattern.search(data)
    if match is None:
        raise ValueError(f"cannot patch missing worksheet cell: {ref}")
    attrs = re.sub(rb'\s+t="[^"]*"', b"", match.group("attrs")) + b' t="str"'
    prefix = match.group("prefix")
    body = (
        b"<" + prefix + b"f>" + escape(formula).encode("utf-8") + b"</" + prefix + b"f>"
        + b"<" + prefix + b"v>" + escape(cached_value).encode("utf-8") + b"</" + prefix + b"v>"
    )
    replacement = b"<" + prefix + b"c" + attrs + b">" + body + b"</" + prefix + b"c>"
    if match.group(0) == replacement:
        return data, False
    return data[: match.start()] + replacement + data[match.end() :], True


def _formula_cells(
    parts: Mapping[str, bytes],
    order: Sequence[str],
    sheets: Mapping[str, str],
    sheet_ids: Mapping[str, int],
) -> set[tuple[int, str]]:
    result: set[tuple[int, str]] = set()
    for name in order:
        root = _root(parts[sheets[name]], sheets[name])
        for cell in root.findall(".//m:c", NS):
            formula = cell.find("m:f", NS)
            if formula is not None and formula.text:
                result.add((sheet_ids[name], cell.attrib["r"]))
    return result


def _sync_calc_chain(parts: dict[str, bytes], formulas: set[tuple[int, str]]) -> bool:
    part = "xl/calcChain.xml"
    if part not in parts:
        return False
    root = _root(parts[part], part)
    existing: set[tuple[int, str]] = set()
    current_sheet = 0
    for cell in root.findall("m:c", NS):
        if "i" in cell.attrib:
            current_sheet = int(cell.attrib["i"])
        existing.add((current_sheet, cell.attrib["r"]))
    stale = existing - formulas
    if stale:
        raise ValueError(f"calc chain contains stale formula cells: {sorted(stale)[:10]}")
    missing = sorted(formulas - existing, key=lambda item: (-item[0], item[1]))
    if not missing:
        return False
    closing = b"</calcChain>"
    location = parts[part].rfind(closing)
    if location < 0:
        raise ValueError("calcChain.xml has no closing calcChain element")
    additions = b"".join(f'<c r="{ref}" i="{sheet_id}"/>'.encode("ascii") for sheet_id, ref in missing)
    parts[part] = parts[part][:location] + additions + parts[part][location:]
    return True


def _write_preserving_package(source: Path, output: Path, replacements: Mapping[str, bytes]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    same_path = source.resolve() == output.resolve()
    target = output
    temporary: Path | None = None
    if same_path:
        fd, name = tempfile.mkstemp(prefix=source.stem + "-", suffix=".xlsx", dir=str(source.parent))
        os.close(fd)
        temporary = Path(name)
        target = temporary
    try:
        with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(target, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, replacements.get(info.filename, src.read(info.filename)))
        if same_path and temporary is not None:
            os.replace(temporary, output)
            temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def apply_copy_range_links(source: Path, output: Path, prompt_ranges: Iterable[object] | None = None) -> CopyRangeLinkResult:
    source = Path(source)
    output = Path(output)
    if not source.exists():
        raise FileNotFoundError(source)
    with zipfile.ZipFile(source, "r") as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"invalid ZIP member: {bad_member}")
        original_order = [info.filename for info in archive.infolist()]
        parts = {name: archive.read(name) for name in original_order}
    order, sheets, sheet_ids = _sheet_map(parts)
    links = _coerce_links(prompt_ranges) if prompt_ranges is not None else discover_copy_range_links(parts)
    _validate_label_cells(parts, sheets, links)
    formula_before = len(_formula_cells(parts, order, sheets, sheet_ids))
    changed: set[str] = set()
    for link in links:
        part = sheets[link.sheet]
        data = parts[part]
        formula = f'HYPERLINK("#\'{link.sheet}\'!{link.prompt_range}","Copy {link.prompt_range} only")'
        for ref in (link.top_cell, link.bottom_cell):
            data, did_change = _patch_cell_xml(data, ref, formula, f"Copy {link.prompt_range} only")
            if did_change:
                changed.add(part)
        parts[part] = data
    formulas = _formula_cells(parts, order, sheets, sheet_ids)
    calc_changed = _sync_calc_chain(parts, formulas)
    if calc_changed:
        changed.add("xl/calcChain.xml")
    formula_after = len(formulas)
    expected_delta = 2 * len(links)
    if formula_after - formula_before not in (0, expected_delta):
        raise ValueError(
            f"unexpected formula delta: before={formula_before}, after={formula_after}, expected +{expected_delta} or idempotent +0"
        )
    _write_preserving_package(source, output, {name: parts[name] for name in changed})

    with zipfile.ZipFile(output, "r") as archive:
        if [info.filename for info in archive.infolist()] != original_order:
            raise ValueError("ZIP member order changed")
        final_parts = {name: archive.read(name) for name in original_order}
    final_order, final_sheets, final_sheet_ids = _sheet_map(final_parts)
    final_formulas = _formula_cells(final_parts, final_order, final_sheets, final_sheet_ids)
    for link in links:
        root = _root(final_parts[final_sheets[link.sheet]], final_sheets[link.sheet])
        expected = f'HYPERLINK("#\'{link.sheet}\'!{link.prompt_range}","Copy {link.prompt_range} only")'
        for ref in (link.top_cell, link.bottom_cell):
            cell = _find_cell(root, ref)
            formula = cell.find("m:f", NS)
            value = cell.find("m:v", NS)
            if formula is None or formula.text != expected:
                raise ValueError(f"final link formula mismatch: {link.sheet}!{ref}")
            if value is None or value.text != f"Copy {link.prompt_range} only":
                raise ValueError(f"final cached label mismatch: {link.sheet}!{ref}")
    if "xl/calcChain.xml" in final_parts:
        chain = _root(final_parts["xl/calcChain.xml"], "xl/calcChain.xml")
        chain_entries: set[tuple[int, str]] = set()
        current_sheet = 0
        for cell in chain.findall("m:c", NS):
            if "i" in cell.attrib:
                current_sheet = int(cell.attrib["i"])
            chain_entries.add((current_sheet, cell.attrib["r"]))
        if chain_entries != final_formulas:
            missing = final_formulas - chain_entries
            stale = chain_entries - final_formulas
            raise ValueError(
                f"calc chain does not exactly match formula cells; missing={sorted(missing)[:10]}, stale={sorted(stale)[:10]}"
            )

    return CopyRangeLinkResult(
        source=str(source),
        output=str(output),
        source_sha256=_sha256(source),
        output_sha256=_sha256(output),
        prompt_count=len(links),
        links_written=2 * len(links),
        changed_parts=tuple(sorted(changed)),
        calc_chain_updated=calc_changed,
        formula_count_before=formula_before,
        formula_count_after=len(final_formulas),
        validation_passed=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = apply_copy_range_links(args.source, args.output)
    except Exception as exc:
        print(f"prompt copy-range link patch failed: {exc}")
        return 1
    payload = result.to_dict()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
