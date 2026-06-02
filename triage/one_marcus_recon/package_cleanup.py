"""Package-level surgical cleanup for Web Excel safety.

- Drop stale ``xl/calcChain.xml`` so Excel for Web rebuilds formulas.
- Strip unused ``xl/externalLinks/*`` parts after formula localization.
- Repair the relationship and content-type references those removals dangle.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple


class Package:
    """Mutable, order-preserving view over an OOXML (xlsx) ZIP package."""

    def __init__(self, names: List[str], parts: Dict[str, bytes]):
        self.names = list(names)
        self.parts = dict(parts)

    @classmethod
    def from_path(cls, path: str) -> "Package":
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
            parts = {n: z.read(n) for n in names}
        return cls(names, parts)

    @classmethod
    def from_bytes(cls, data: bytes) -> "Package":
        with zipfile.ZipFile(io.BytesIO(data), "r") as z:
            names = z.namelist()
            parts = {n: z.read(n) for n in names}
        return cls(names, parts)

    def text(self, name: str) -> str:
        return self.parts[name].decode("utf-8", errors="ignore")

    def set_text(self, name: str, value: str) -> None:
        self.parts[name] = value.encode("utf-8")

    def has(self, name: str) -> bool:
        return name in self.parts

    def remove(self, name: str) -> bool:
        if name in self.parts:
            del self.parts[name]
            self.names = [n for n in self.names if n != name]
            return True
        return False

    def worksheet_parts(self) -> List[str]:
        return [
            n
            for n in self.names
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
        ]

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for n in self.names:
                z.writestr(n, self.parts[n])
        return buf.getvalue()

    def write(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(self.to_bytes())


def remove_calc_chain(pkg: Package) -> bool:
    """Remove calcChain.xml and its content-type override + workbook rel."""
    removed = pkg.remove("xl/calcChain.xml")
    if not removed:
        return False

    ct_name = "[Content_Types].xml"
    if pkg.has(ct_name):
        ct = pkg.text(ct_name)
        ct = re.sub(r'<Override\b[^>]*calcChain\.xml[^>]*/>', "", ct)
        pkg.set_text(ct_name, ct)

    rels_name = "xl/_rels/workbook.xml.rels"
    if pkg.has(rels_name):
        rels = pkg.text(rels_name)
        rels = re.sub(r'<Relationship\b[^>]*Target="[^"]*calcChain\.xml"[^>]*/>', "", rels)
        pkg.set_text(rels_name, rels)
    return True


def remove_external_links(pkg: Package) -> List[str]:
    """Remove xl/externalLinks/* parts and repair dangling references."""
    ext_parts = [n for n in pkg.names if n.startswith("xl/externalLinks/")]
    if not ext_parts:
        return []

    for n in ext_parts:
        pkg.remove(n)

    # Content types: drop externalLink overrides.
    ct_name = "[Content_Types].xml"
    if pkg.has(ct_name):
        ct = pkg.text(ct_name)
        ct = re.sub(r'<Override\b[^>]*externalLink[^>]*/>', "", ct)
        pkg.set_text(ct_name, ct)

    # Workbook rels: drop relationships targeting externalLinks/*, and collect
    # the rIds so we can strip <externalReference r:id=...> from workbook.xml.
    rels_name = "xl/_rels/workbook.xml.rels"
    dropped_rids: List[str] = []
    if pkg.has(rels_name):
        rels = pkg.text(rels_name)

        def _drop(m: re.Match) -> str:
            frag = m.group(0)
            if "externalLink" in frag:
                rid = re.search(r'Id="([^"]+)"', frag)
                if rid:
                    dropped_rids.append(rid.group(1))
                return ""
            return frag

        rels = re.sub(r"<Relationship\b[^>]*/>", _drop, rels)
        pkg.set_text(rels_name, rels)

    # Workbook.xml: remove externalReference entries (and empty container).
    wb_name = "xl/workbook.xml"
    if pkg.has(wb_name):
        wb = pkg.text(wb_name)
        for rid in dropped_rids:
            wb = re.sub(
                r'<externalReference\b[^>]*r:id="' + re.escape(rid) + r'"[^>]*/>',
                "",
                wb,
            )
        # Drop any leftover externalReference tags, then empty wrapper.
        wb = re.sub(r"<externalReference\b[^>]*/>", "", wb)
        wb = re.sub(r"<externalReferences\b[^>]*>\s*</externalReferences>", "", wb)
        wb = re.sub(r"<externalReferences\b[^>]*/>", "", wb)
        pkg.set_text(wb_name, wb)

    return ext_parts


def broken_relationship_targets(pkg: Package) -> List[str]:
    """Return workbook relationship targets that no longer resolve to a part."""
    rels_name = "xl/_rels/workbook.xml.rels"
    if not pkg.has(rels_name):
        return []
    rels = pkg.text(rels_name)
    broken: List[str] = []
    for t in re.findall(r'Target="([^"]+)"', rels):
        if t.startswith("http") or t.startswith("/"):
            continue
        norm = ("xl/" + t).replace("xl/./", "xl/")
        norm = re.sub(r"xl/\.\./", "", norm)
        if norm not in pkg.parts and t not in pkg.parts:
            broken.append(t)
    return broken
