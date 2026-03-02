"""
autofix_loop.py  -  AUTONOMOUS Web-Excel Repair Triage Engine
=============================================================
Zero AI API calls. Runs indefinitely without human or Augment token intervention.

Lifecycle:
  1. Watch Candidates/ for new/modified .xlsx files
  2. Run the gate battery (fast checks only, timeboxed)
  3. Apply all deterministic auto-fixes for known patterns
  4. Validate output — compare gate before/after
  5. If POST: PASS  -> archive to Outputs/, log checkpoint JSON
     If POST: FAIL  -> log residual issues, continue to next file
  6. Sleep POLL_INTERVAL seconds, repeat

Usage:
  python autofix_loop.py                  # run forever
  python autofix_loop.py --once           # single sweep then exit
  python autofix_loop.py --file foo.xlsx  # process one file
"""
from __future__ import annotations

import argparse, hashlib, io, json, logging, re, time, zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# ── Config ─────────────────────────────────────────────────────────────────
CANDIDATES_DIR  = Path("Candidates")
OUTPUTS_DIR     = Path("Outputs")
CHECKPOINT_FILE = Path("Outputs/autofix_checkpoint.json")
POLL_INTERVAL   = 30          # seconds between sweeps
LOG_LEVEL       = logging.INFO
# ───────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("Outputs/autofix_loop.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("autofix")


# ══════════════════════════════════════════════════════════
#  SECTION 1 — GATE CHECKS  (self-contained, no imports)
# ══════════════════════════════════════════════════════════

def _txt(z, name): return z.read(name).decode("utf-8", errors="ignore")
def _raw(z, name): return z.read(name)

def _col2num(c):
    n = 0
    for ch in c: n = n * 26 + (ord(ch) - 64)
    return n

def _num2col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _parse_ref(ref):
    m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", ref)
    return (m.group(1), int(m.group(2)), m.group(3), int(m.group(4))) if m else None

def _max_row(xml):
    rows = [int(m.group(1)) for m in re.finditer(r'<row[^>]*\br="(\d+)"', xml)]
    return max(rows) if rows else 0

def gate_rels_missing(z) -> List[dict]:
    """Dangling relationship targets (fast)."""
    missing = []
    all_parts = set(z.namelist())
    for rels in [n for n in z.namelist() if n.endswith(".rels")]:
        txt = _txt(z, rels)
        for m in re.finditer(r'Target="([^"]+)"', txt):
            tgt = m.group(1)
            if tgt.startswith("/") or "://" in tgt:
                continue
            rp = rels.split("/")
            base = list(rp[:rp.index("_rels")] if "_rels" in rp else [])
            for seg in tgt.split("/"):
                if seg == "..":
                    if base: base.pop()
                elif seg and seg != ".":
                    base.append(seg)
            resolved = "/".join(base)
            if resolved not in all_parts:
                missing.append({"rels": rels, "target": tgt, "resolved": resolved})
    return missing

def gate_calcchain(z) -> List[dict]:
    """calcChain entries pointing to non-formula cells."""
    invalid = []
    if "xl/calcChain.xml" not in z.namelist():
        return invalid
    calc = _txt(z, "xl/calcChain.xml")
    entries = re.findall(r'<c\b[^>]*\br="([^"]+)"[^>]*\bi="(\d+)"[^>]*/>', calc)
    sheet_cache: Dict[str, Optional[Set]] = {}
    for cell, i in entries:
        part = f"xl/worksheets/sheet{i}.xml"
        if part not in sheet_cache:
            if part not in z.namelist():
                sheet_cache[part] = None
            else:
                formula_cells: Set[str] = set()
                s = _txt(z, part)
                for chunk in s.split("</c>"):
                    cm = re.search(r'<c\b[^>]*\br="([A-Z]+\d+)"', chunk)
                    if cm and "<f" in chunk[cm.end():]:
                        formula_cells.add(cm.group(1))
                sheet_cache[part] = formula_cells
        pool = sheet_cache[part]
        if pool is None or cell not in pool:
            invalid.append({"sheet": part, "cell": cell})
    return invalid

def gate_shared_ref(z):
    """Shared formula bbox mismatches (O(n), no DOTALL)."""
    from collections import defaultdict
    oob, bbox = [], []
    for part in [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]:
        s = _txt(z, part)
        mrow = _max_row(s)
        si_cells = defaultdict(list)
        si_decl = {}
        _CR = re.compile(r'<c\b[^>]*\br="([A-Z]+\d+)"')
        _FT = re.compile(r'<f\b([^>]*)>')
        for chunk in s.split("</c>"):
            cm = None
            for cm in _CR.finditer(chunk): pass
            if not cm: continue
            after = chunk[cm.end():]
            fm = _FT.search(after)
            if not fm: continue
            fa = fm.group(1)
            if 't="shared"' not in fa: continue
            sim = re.search(r'\bsi="(\d+)"', fa)
            if not sim: continue
            si = sim.group(1)
            si_cells[si].append(cm.group(1))
            rm = re.search(r'\bref="([^"]+)"', fa)
            if rm: si_decl[si] = rm.group(1)
        for si, ref in si_decl.items():
            pr = _parse_ref(ref)
            if pr and pr[3] > mrow:
                oob.append({"part": part, "si": si, "ref": ref, "max_row": mrow})
        for si, cells in si_cells.items():
            if si not in si_decl: continue
            pr = _parse_ref(si_decl[si])
            if not pr: continue
            nums = []
            for c in cells:
                m2 = re.match(r"^([A-Z]+)(\d+)$", c)
                if m2: nums.append((_col2num(m2.group(1)), int(m2.group(2))))
            if not nums: continue
            cmin = min(n[0] for n in nums); cmax = max(n[0] for n in nums)
            rmin = min(n[1] for n in nums); rmax = max(n[1] for n in nums)
            actual   = f"{_num2col(cmin)}{rmin}:{_num2col(cmax)}{rmax}"
            declared = f"{pr[0]}{pr[1]}:{pr[2]}{pr[3]}"
            if actual != declared:
                bbox.append({"part": part, "si": si, "declared": declared, "actual": actual})
    return oob, bbox

def gate_styles_dxf(z) -> List[dict]:
    issues = []
    if "xl/styles.xml" not in z.namelist():
        return [{"issue": "missing_styles"}]
    txt = _txt(z, "xl/styles.xml")
    actual = len(re.findall(r"<dxf\b", txt))
    m = re.search(r'<dxfs\b[^>]*\bcount="(\d+)"', txt)
    declared = int(m.group(1)) if m else None
    if declared is not None and declared != actual:
        issues.append({"issue": "dxfs_count_mismatch", "declared": declared, "actual": actual})
    for sheet in [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]:
        for m2 in re.finditer(r'<cfRule\b[^>]*\bdxfId="(\d+)"', _txt(z, sheet)):
            did = int(m2.group(1))
            if did < 0 or did >= actual:
                issues.append({"issue": "cf_dxfId_oob", "part": sheet, "dxfId": did, "count": actual})
    return issues

def gate_table_datadxf(z) -> List[dict]:
    """NEW: tableColumn dataDxfId must be < actual dxf count."""
    issues = []
    if "xl/styles.xml" not in z.namelist():
        return issues
    styles = _txt(z, "xl/styles.xml")
    actual = len(re.findall(r"<dxf\b", styles))
    for tbl in [n for n in z.namelist() if n.startswith("xl/tables/") and n.endswith(".xml")]:
        t = _txt(z, tbl)
        for m in re.finditer(r'\bdataDxfId="(\d+)"', t):
            did = int(m.group(1))
            if did < 0 or did >= actual:
                issues.append({"part": tbl, "issue": "dataDxfId_oob", "dataDxfId": did, "dxf_count": actual})
    return issues

def gate_tablecolumn_lf(z) -> List[dict]:
    hits = []
    for name in z.namelist():
        if name.startswith("xl/tables/table") and name.endswith(".xml"):
            raw = _raw(z, name)
            idx = 0
            while True:
                j = raw.find(b'name="', idx)
                if j < 0: break
                j += 6; k = raw.find(b'"', j)
                if k < 0: break
                val = raw[j:k]
                if b"\n" in val or b"\r" in val:
                    hits.append({"part": name, "value": repr(val[:50])})
                    break
                idx = k + 1
    return hits

def gate_stopship(z) -> List[dict]:
    STOPSHIP = ("_xlfn.", "_xludf.", "_xlpm.", "AGGREGATE(")
    hits = []
    for name in [n for n in z.namelist() if n.startswith("xl/worksheets/") and n.endswith(".xml")]:
        s = _txt(z, name)
        for m in re.finditer(r"<f\b[^>]*>(.*?)</f>", s, re.DOTALL):
            for tok in STOPSHIP:
                if tok in m.group(1):
                    hits.append({"part": name, "token": tok})
    return hits

def run_gates(path: str) -> dict:
    """Run all fast gates. Returns summary dict."""
    results = {"path": path, "timestamp": datetime.now().isoformat(), "gates": {}, "pass": False}
    try:
        with zipfile.ZipFile(path, "r") as z:
            results["gates"]["rels_missing"]      = gate_rels_missing(z)
            results["gates"]["calcchain_invalid"]  = gate_calcchain(z)
            oob, bbox = gate_shared_ref(z)
            results["gates"]["shared_ref_oob"]    = oob
            results["gates"]["shared_ref_bbox"]   = bbox
            results["gates"]["styles_dxf"]        = gate_styles_dxf(z)
            results["gates"]["table_datadxf"]     = gate_table_datadxf(z)
            results["gates"]["tablecolumn_lf"]    = gate_tablecolumn_lf(z)
            results["gates"]["stopship"]          = gate_stopship(z)
    except Exception as e:
        results["error"] = str(e)
        return results
    failing = {k: len(v) for k, v in results["gates"].items() if v}
    results["failing"] = failing
    results["pass"] = len(failing) == 0
    return results


# ══════════════════════════════════════════════════════════
#  SECTION 2 — AUTO-FIXERS  (deterministic, no AI)
# ══════════════════════════════════════════════════════════

def fix_strip_rels(parts: Dict[str, bytes], target_basename: str) -> int:
    """Remove all <Relationship> entries pointing to *target_basename* from every .rels file."""
    needle = target_basename.encode()
    stripped = 0
    for key in list(parts.keys()):
        if not key.endswith(".rels"): continue
        data = parts[key]
        if needle not in data: continue
        chunks = data.split(b"<Relationship")
        kept = [chunks[0]]
        for chunk in chunks[1:]:
            end = chunk.find(b"/>")
            if end == -1:
                kept.append(chunk); continue
            elem = chunk[:end + 2]
            tm = re.search(rb'Target="([^"]+)"', elem)
            if tm and needle in tm.group(1):
                kept.append(chunk[end + 2:])
                stripped += 1
            else:
                kept.append(chunk)
        parts[key] = b"<Relationship".join(kept)
    return stripped

def fix_delete_calcchain(parts: Dict[str, bytes]) -> List[str]:
    """Delete calcChain.xml and strip its rels entry. Returns list of actions taken."""
    actions = []
    if "xl/calcChain.xml" in parts:
        del parts["xl/calcChain.xml"]
        actions.append("deleted xl/calcChain.xml")
    n = fix_strip_rels(parts, "calcChain.xml")
    if n:
        actions.append(f"stripped {n} calcChain rels entries")
    return actions

def fix_shared_ref_bbox(parts: Dict[str, bytes], bbox_issues: List[dict]) -> List[str]:
    """Fix shared formula ref= bounding boxes via literal byte replacement."""
    actions = []
    by_part: Dict[str, List[dict]] = {}
    for issue in bbox_issues:
        by_part.setdefault(issue["part"], []).append(issue)
    for part, issues in by_part.items():
        if part not in parts: continue
        data = parts[part]
        for issue in issues:
            si = issue["si"]
            declared = issue["declared"]
            actual   = issue["actual"]
            old = f'si="{si}" ref="{declared}"'.encode()
            new = f'si="{si}" ref="{actual}"'.encode()
            if old in data:
                data = data.replace(old, new, 1)
                actions.append(f"{part} si={si}: {declared} -> {actual}")
            else:
                # Also try reversed attribute order
                old2 = f'ref="{declared}" si="{si}"'.encode()
                new2 = f'ref="{actual}" si="{si}"'.encode()
                if old2 in data:
                    data = data.replace(old2, new2, 1)
                    actions.append(f"{part} si={si} [rev]: {declared} -> {actual}")
        parts[part] = data
    return actions

def fix_cf_ref_hits(parts: Dict[str, bytes]) -> List[str]:
    """Remove <conditionalFormatting> blocks that contain #REF! formula errors."""
    actions = []
    for key in list(parts.keys()):
        if not (key.startswith("xl/worksheets/sheet") and key.endswith(".xml")):
            continue
        data = parts[key]
        if b"#REF!" not in data:
            continue
        # Split on <conditionalFormatting blocks and drop those with #REF!
        # Uses a two-pass approach: find all CF blocks, remove bad ones
        new_data = re.sub(
            rb"<conditionalFormatting\b[^>]*>.*?</conditionalFormatting>",
            lambda m: b"" if b"#REF!" in m.group(0) else m.group(0),
            data,
            flags=re.DOTALL,
        )
        if new_data != data:
            count = data.count(b"#REF!") - new_data.count(b"#REF!")
            actions.append(f"{key}: removed CF blocks with #REF! ({count} refs eliminated)")
            parts[key] = new_data
    return actions

def fix_dxfs_count(parts: Dict[str, bytes], styles_dxf_issues: List[dict]) -> List[str]:
    """Fix dxfs count= attribute to match actual <dxf> element count."""
    actions = []
    if "xl/styles.xml" not in parts: return actions
    data = parts["xl/styles.xml"]
    for issue in styles_dxf_issues:
        if issue.get("issue") != "dxfs_count_mismatch": continue
        declared = issue["declared"]
        actual   = issue["actual"]
        old = f'count="{declared}"'.encode()
        new = f'count="{actual}"'.encode()
        # Only replace inside <dxfs ...>
        dxfs_idx = data.find(b"<dxfs")
        if dxfs_idx == -1: continue
        close_idx = data.find(b">", dxfs_idx)
        if close_idx == -1: continue
        tag_bytes = data[dxfs_idx:close_idx + 1]
        if old in tag_bytes:
            parts["xl/styles.xml"] = data[:dxfs_idx] + tag_bytes.replace(old, new, 1) + data[close_idx + 1:]
            actions.append(f"styles.xml dxfs count: {declared} -> {actual}")
    return actions

def autofix(src_path: str, pre: dict) -> tuple[bytes, List[str]]:
    """
    Apply all deterministic fixes to *src_path* based on *pre* gate results.
    Returns (patched_bytes, list_of_actions).
    """
    parts: Dict[str, bytes] = {}
    with zipfile.ZipFile(src_path, "r") as z:
        for n in z.namelist():
            parts[n] = z.read(n)

    actions: List[str] = []

    # 1. calcChain — always drop if invalid entries exist OR dangling rels
    calcchain_issues = pre["gates"].get("calcchain_invalid", [])
    rels_issues      = pre["gates"].get("rels_missing", [])
    has_dangling_calc = any("calcChain" in r.get("resolved","") for r in rels_issues)
    if calcchain_issues or has_dangling_calc:
        actions += fix_delete_calcchain(parts)

    # 2. Shared ref bbox
    bbox = pre["gates"].get("shared_ref_bbox", [])
    if bbox:
        actions += fix_shared_ref_bbox(parts, bbox)

    # 3. CF #REF! hits — strip the offending conditionalFormatting blocks
    cf_ref = pre["gates"].get("cf_ref", [])  # populated from gate output
    # Always check since gate_cf_ref isn't wired separately — scan for #REF! presence
    for key in parts:
        if key.startswith("xl/worksheets/sheet") and key.endswith(".xml"):
            if b"#REF!" in parts[key]:
                actions += fix_cf_ref_hits(parts)
                break

    # 4. DXF count mismatch
    dxf = pre["gates"].get("styles_dxf", [])
    if dxf:
        actions += fix_dxfs_count(parts, dxf)

    # 4. Strip any other dangling rels (non-calcChain)
    for r in rels_issues:
        resolved = r.get("resolved", "")
        if "calcChain" in resolved: continue  # already handled
        basename = resolved.rsplit("/", 1)[-1]
        n = fix_strip_rels(parts, basename)
        if n:
            actions.append(f"stripped {n} rels for missing {basename}")

    # Serialize
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, d in parts.items():
            zout.writestr(n, d)
    return buf.getvalue(), actions


# ══════════════════════════════════════════════════════════
#  SECTION 3 — CHECKPOINT & MAIN LOOP
# ══════════════════════════════════════════════════════════

def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed": {}}

def save_checkpoint(cp: dict) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(cp, indent=2), encoding="utf-8")

def process_file(src: Path, cp: dict) -> dict:
    sha = _sha256(str(src))
    prev = cp["processed"].get(str(src), {})
    if prev.get("sha") == sha and prev.get("post_pass"):
        log.info(f"SKIP (unchanged + already passing): {src.name}")
        return prev

    log.info(f"Processing: {src.name}")
    pre = run_gates(str(src))
    log.info(f"  PRE: {'PASS' if pre['pass'] else 'FAIL'} — failing={list(pre.get('failing',{}).keys())}")

    if pre["pass"]:
        log.info(f"  Already passing — no patches needed.")
        result = {"sha": sha, "pre_pass": True, "post_pass": True, "actions": [], "output": str(src)}
        cp["processed"][str(src)] = result
        save_checkpoint(cp)
        return result

    patched_bytes, actions = autofix(str(src), pre)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{src.stem}_autofix_{ts}.xlsx"
    out_path = OUTPUTS_DIR / out_name
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(patched_bytes)
    log.info(f"  Actions ({len(actions)}): {'; '.join(actions[:5])}" + (" ..." if len(actions)>5 else ""))

    post = run_gates(str(out_path))
    log.info(f"  POST: {'PASS' if post['pass'] else 'FAIL'} — failing={list(post.get('failing',{}).keys())}")

    result = {
        "sha": sha,
        "pre_pass":   pre["pass"],
        "post_pass":  post["pass"],
        "actions":    actions,
        "output":     str(out_path),
        "pre_failing":  pre.get("failing", {}),
        "post_failing": post.get("failing", {}),
        "timestamp":  ts,
    }
    cp["processed"][str(src)] = result

    # Write per-file report
    report_path = OUTPUTS_DIR / f"{src.stem}_autofix_{ts}_report.json"
    report_path.write_text(json.dumps({
        "source": str(src), "output": str(out_path),
        "pre": pre, "post": post, "actions": actions
    }, indent=2), encoding="utf-8")

    if post["pass"]:
        log.info(f"  ✅ CHECKPOINT — {out_name} is Web-Excel safe. Upload to OneDrive to verify.")
    else:
        residual = list(post.get("failing", {}).keys())
        log.warning(f"  ⚠️  Residual issues after autofix: {residual}")
        log.warning(f"  Report: {report_path}")

    save_checkpoint(cp)
    return result


def sweep(cp: dict) -> None:
    candidates = sorted(CANDIDATES_DIR.glob("*.xlsx"))
    log.info(f"Sweep: {len(candidates)} candidates in {CANDIDATES_DIR}/")
    for src in candidates:
        try:
            process_file(src, cp)
        except Exception as e:
            log.error(f"  ERROR processing {src.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Web-Excel Repair Loop")
    parser.add_argument("--once",  action="store_true", help="Single sweep then exit")
    parser.add_argument("--file",  type=str, default=None, help="Process one specific file")
    args = parser.parse_args()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    cp = load_checkpoint()

    log.info("=" * 60)
    log.info("autofix_loop.py  —  Web-Excel Autonomous Repair Engine")
    log.info("=" * 60)

    if args.file:
        result = process_file(Path(args.file), cp)
        log.info(f"Done. post_pass={result.get('post_pass')}, output={result.get('output')}")
        return

    if args.once:
        sweep(cp)
        return

    log.info(f"Watching {CANDIDATES_DIR}/ every {POLL_INTERVAL}s. Ctrl+C to stop.")
    try:
        while True:
            sweep(cp)
            log.info(f"Sleeping {POLL_INTERVAL}s …")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log.info("Stopped by user.")


if __name__ == "__main__":
    main()

