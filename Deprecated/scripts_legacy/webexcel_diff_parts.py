#!/usr/bin/env python3
"""
webexcel_diff_parts.py
Part-level diff between two XLSX files (candidate vs repaired).

Usage:
  python webexcel_diff_parts.py candidate.xlsx repaired.xlsx

Outputs:
  - summary to stdout
  - JSON report: <candidate>.diff_to_<repaired_basename>.json
"""

import json
import sys
import zipfile
import hashlib
import difflib

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def list_parts(path: str):
    out = {}
    with zipfile.ZipFile(path, "r") as z:
        for name in z.namelist():
            b = z.read(name)
            out[name] = {"size": len(b), "sha256": sha256(b)}
    return out

def read_part(path: str, part: str) -> bytes:
    with zipfile.ZipFile(path, "r") as z:
        return z.read(part)

def short_xml_diff(a_txt: str, b_txt: str, context=3, max_lines=120):
    a_lines = a_txt.splitlines()
    b_lines = b_txt.splitlines()
    diff = list(difflib.unified_diff(a_lines, b_lines, lineterm="", n=context))
    if len(diff) > max_lines:
        diff = diff[:max_lines] + ["... (diff truncated) ..."]
    return "\n".join(diff)

def main():
    if len(sys.argv) != 3:
        print("Usage: python webexcel_diff_parts.py candidate.xlsx repaired.xlsx")
        sys.exit(2)

    cand, rep = sys.argv[1], sys.argv[2]
    A = list_parts(cand)
    B = list_parts(rep)

    partsA = set(A.keys())
    partsB = set(B.keys())

    added = sorted(partsB - partsA)
    removed = sorted(partsA - partsB)
    common = sorted(partsA & partsB)

    changed = []
    same = []
    for p in common:
        if A[p]["sha256"] != B[p]["sha256"]:
            changed.append(p)
        else:
            same.append(p)

    report = {
        "candidate": cand,
        "repaired": rep,
        "counts": {
            "candidate_parts": len(partsA),
            "repaired_parts": len(partsB),
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(same),
        },
        "added": added,
        "removed": removed,
        "changed": [],
    }

    # For changed parts, capture size/hash delta; for XML, include a short unified diff snippet.
    for p in changed:
        entry = {
            "part": p,
            "candidate": A[p],
            "repaired": B[p],
        }
        if p.lower().endswith(".xml"):
            a_raw = read_part(cand, p)
            b_raw = read_part(rep, p)
            a_txt = a_raw.decode("utf-8", errors="ignore")
            b_txt = b_raw.decode("utf-8", errors="ignore")
            entry["xml_diff"] = short_xml_diff(a_txt, b_txt)
        report["changed"].append(entry)

    out = f"{cand}.diff_to_{rep.split('/')[-1]}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("DIFF REPORT:", out)
    print("added:", len(added))
    print("removed:", len(removed))
    print("changed:", len(changed))
    if changed:
        print("top changed parts:")
        for p in changed[:20]:
            print(" -", p)

if __name__ == "__main__":
    main()
