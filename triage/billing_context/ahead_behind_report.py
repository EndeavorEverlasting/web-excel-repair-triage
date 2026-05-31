"""Generate an HTML ahead/behind report from billing context mismatch JSON."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


def load_mismatches(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _severity_badge(severity: str) -> str:
    colors = {
        "red": "#dc3545",
        "amber": "#fd7e14",
        "blue": "#0d6efd",
        "gray": "#6c757d",
    }
    return f'<span style="background:{colors.get(severity,colors["gray"])};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;text-transform:uppercase;">{severity}</span>'


def build_report(mismatches: list[dict[str, Any]], manifest: list[dict[str, Any]]) -> str:
    # --- Compute ahead/behind stats ---
    by_type: Counter[str] = Counter()
    by_tech: defaultdict[str, list[dict]] = defaultdict(list)
    by_pair: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    ahead_counts: defaultdict[str, int] = defaultdict(int)
    behind_counts: defaultdict[str, int] = defaultdict(int)

    for m in mismatches:
        mt = m.get("mismatch_type", "")
        by_type[mt] += 1
        by_tech[m.get("tech", "Unknown")].append(m)
        pair = (m.get("source_a", "?"), m.get("source_b", "?"))
        by_pair[pair].append(m)
        if mt == "missing_in_source":
            # source_a has it, source_b is missing it
            ahead_counts[m.get("source_a", "?")] += 1
            behind_counts[m.get("source_b", "?")] += 1
        elif mt == "hours_delta":
            ahead_counts[m.get("source_a", "?")] += 1
            ahead_counts[m.get("source_b", "?")] += 1

    # --- Build HTML ---
    html_parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8"><title>Billing Context Ahead/Behind</title>',
        '<style>',
        'body{font-family:system-ui,-apple-system,sans-serif;margin:24px auto;max-width:1100px;background:#f8f9fa;color:#212529;line-height:1.5}',
        'h1,h2{margin:0 0 12px}',
        'h1{font-size:28px}h2{font-size:20px;border-bottom:2px solid #dee2e6;padding-bottom:6px;margin-top:32px}',
        '.card{background:#fff;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,.06)}',
        '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}',
        '.stat{text-align:center;padding:16px;background:#f1f3f5;border-radius:6px}',
        '.stat .num{font-size:32px;font-weight:700;color:#0d6efd}',
        '.stat .lbl{font-size:13px;color:#495057;text-transform:uppercase;letter-spacing:.5px}',
        'table{width:100%;border-collapse:collapse;font-size:14px;margin-top:12px}',
        'th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #dee2e6}',
        'th{background:#e9ecef;font-weight:600;font-size:13px;text-transform:uppercase;color:#495057}',
        'tr:hover{background:#f8f9fa}',
        '.fix-box{background:#fff3cd;border-left:4px solid #fd7e14;padding:12px 16px;border-radius:0 6px 6px 0;margin:8px 0}',
        '.fix-box strong{color:#856404}',
        '.ahead{color:#198754;font-weight:700}.behind{color:#dc3545;font-weight:700}',
        '.pair-cell{font-family:ui-monospace,SFMono-Regular,monospace;font-size:13px}',
        '</style></head><body>',
    ]

    # Header
    html_parts.append(f'<div class="card"><h1>📊 Billing Context Ahead / Behind Report</h1>')
    html_parts.append(f'<p style="color:#6c757d;margin:0">Generated {date.today().isoformat()} &middot; {len(mismatches)} mismatches across {len(by_tech)} technicians</p></div>')

    # Summary stats
    html_parts.append('<div class="card"><div class="grid">')
    total_ahead = sum(ahead_counts.values())
    total_behind = sum(behind_counts.values())
    html_parts.append(f'<div class="stat"><div class="num">{len(mismatches)}</div><div class="lbl">Total Mismatches</div></div>')
    html_parts.append(f'<div class="stat"><div class="num" style="color:#dc3545">{by_type.get("missing_in_source",0)}</div><div class="lbl">Missing Entries</div></div>')
    html_parts.append(f'<div class="stat"><div class="num" style="color:#fd7e14">{by_type.get("hours_delta",0)}</div><div class="lbl">Hour Deltas</div></div>')
    html_parts.append(f'<div class="stat"><div class="num" style="color:#6c757d">{by_type.get("partial_hours",0)}</div><div class="lbl">Partial Days</div></div>')
    html_parts.append('</div></div>')

    # Manifest status
    html_parts.append('<div class="card"><h2>📁 Output Manifest</h2><table><thead><tr><th>Artifact</th><th>Path</th><th>Size</th><th>Status</th></tr></thead><tbody>')
    for item in manifest:
        exists = item.get("exists", False)
        badge = '<span style="background:#198754;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">OK</span>' if exists else '<span style="background:#dc3545;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">MISSING</span>'
        size = item.get("bytes", 0)
        html_parts.append(f'<tr><td>{item.get("name","?")}</td><td style="font-size:12px;color:#495057">{Path(item.get("path","")).name}</td><td>{size:,}</td><td>{badge}</td></tr>')
    html_parts.append('</tbody></table></div>')

    # Ahead / Behind matrix
    html_parts.append('<div class="card"><h2>🔄 Ahead / Behind Matrix</h2>')
    html_parts.append('<p style="margin-top:0;font-size:14px;color:#495057">A source is <strong class="ahead">ahead</strong> when it contains entries another source lacks. A source is <strong class="behind">behind</strong> when it lacks entries another source has.</p>')
    html_parts.append('<table><thead><tr><th>Source Pair</th><th>Ahead</th><th>Behind</th><th>Issue</th></tr></thead><tbody>')

    # Sort pairs by total count descending
    sorted_pairs = sorted(by_pair.items(), key=lambda kv: -len(kv[1]))
    for (src_a, src_b), items in sorted_pairs:
        ahead_n = sum(1 for m in items if m.get("mismatch_type") == "missing_in_source" and m.get("source_a") == src_a)
        behind_n = sum(1 for m in items if m.get("mismatch_type") == "missing_in_source" and m.get("source_b") == src_b)
        delta_n = sum(1 for m in items if m.get("mismatch_type") == "hours_delta")
        total = len(items)
        html_parts.append(
            f'<tr><td class="pair-cell">{src_a} ↔ {src_b}</td>'
            f'<td class="ahead">+{ahead_n}</td>'
            f'<td class="behind">-{behind_n}</td>'
            f'<td>{delta_n} hour deltas, {total} total</td></tr>'
        )
    html_parts.append('</tbody></table></div>')

    # Top technicians with issues
    html_parts.append('<div class="card"><h2>👥 Technicians With Most Issues</h2>')
    top_techs = sorted(by_tech.items(), key=lambda kv: -len(kv[1]))[:15]
    html_parts.append('<table><thead><tr><th>Technician</th><th>Missing</th><th>Hour Delta</th><th>Partial</th><th>Total</th></tr></thead><tbody>')
    for tech, items in top_techs:
        miss = sum(1 for m in items if m.get("mismatch_type") == "missing_in_source")
        delta = sum(1 for m in items if m.get("mismatch_type") == "hours_delta")
        partial = sum(1 for m in items if m.get("mismatch_type") == "partial_hours")
        html_parts.append(f'<tr><td><strong>{tech}</strong></td><td>{miss}</td><td>{delta}</td><td>{partial}</td><td>{len(items)}</td></tr>')
    html_parts.append('</tbody></table></div>')

    # Actionable fixes
    html_parts.append('<div class="card"><h2>🔧 What To Fix</h2>')
    fixes: list[str] = []
    if by_type.get("missing_in_source", 0) > 0:
        fixes.append(f'<div class="fix-box"><strong>{by_type["missing_in_source"]} missing entries</strong> &mdash; Add these technician+date rows to <code>roster_log</code> and <code>admin_copy</code> so they match <code>track_hours</code>.</div>')
    if by_type.get("hours_delta", 0) > 0:
        fixes.append(f'<div class="fix-box"><strong>{by_type["hours_delta"]} hour deltas</strong> &mdash; Reconcile daily hour totals between track_hours and roster_log/admin_copy. Check for lunch deductions, overtime rounding, or split shifts.</div>')
    if by_type.get("partial_hours", 0) > 0:
        fixes.append(f'<div class="fix-box"><strong>{by_type["partial_hours"]} partial day</strong> &mdash; Ensure shifts under 8 hours are intentional (PTO, half-day, late start). If not, investigate missing clock-in/out records.</div>')
    if by_type.get("placeholder_assignment_replaced", 0) > 0:
        fixes.append(f'<div class="fix-box"><strong>Placeholder assignments detected</strong> &mdash; Replace generic assignments like "Neuron Installation" with resolved work context in the task tracker before re-running.</div>')
    if by_type.get("missing_work_context", 0) > 0:
        fixes.append(f'<div class="fix-box"><strong>Missing work context</strong> &mdash; Add descriptive task text to the April context workbook so the resolver can classify hours correctly.</div>')
    if not fixes:
        fixes.append('<div class="fix-box" style="background:#d1e7dd;border-color:#198754"><strong>All clear!</strong> &mdash; No actionable mismatches found.</div>')
    html_parts.extend(fixes)
    html_parts.append('</div>')

    # Detail table
    html_parts.append('<div class="card"><h2>📋 Mismatch Detail (Top 50)</h2>')
    html_parts.append('<table><thead><tr><th>Severity</th><th>Type</th><th>Tech</th><th>Date</th><th>Sources</th><th>Values</th><th>Recommendation</th></tr></thead><tbody>')
    for m in mismatches[:50]:
        html_parts.append(
            f'<tr>'
            f'<td>{_severity_badge(m.get("severity","gray"))}</td>'
            f'<td>{m.get("mismatch_type","?")}</td>'
            f'<td>{m.get("tech","?")}</td>'
            f'<td>{m.get("work_date","?")}</td>'
            f'<td class="pair-cell">{m.get("source_a","?")} → {m.get("source_b","?")}</td>'
            f'<td style="font-size:12px">{m.get("source_a_value","?")} ≠ {m.get("source_b_value","?")}</td>'
            f'<td style="font-size:13px">{m.get("recommendation","")}</td>'
            f'</tr>'
        )
    html_parts.append('</tbody></table></div>')

    html_parts.append('</body></html>')
    return "\n".join(html_parts)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Build ahead/behind HTML report from billing context outputs")
    ap.add_argument("--mismatches", default="Outputs/billing_context_mismatches.json")
    ap.add_argument("--manifest", default="Outputs/billing_context_manifest.json")
    ap.add_argument("--out", default="Outputs/billing_context_ahead_behind.html")
    args = ap.parse_args(argv)

    mm_path = Path(args.mismatches)
    manifest_path = Path(args.manifest)
    out_path = Path(args.out)

    mismatches = load_mismatches(mm_path) if mm_path.exists() else []

    manifest: list[dict[str, Any]] = []
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            manifest = raw if isinstance(raw, list) else raw.get("manifest", [])

    # If no standalone manifest, try to reconstruct from mismatch path companion or CLI stdout
    if not manifest and mm_path.exists():
        # look for a CLI stdout JSON nearby
        for candidate in mm_path.parent.glob("billing_context_*.json"):
            if candidate.name == mm_path.name:
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    manifest = raw.get("manifest", [])
                    break
            except Exception:
                continue

    html = build_report(mismatches, manifest)
    out_path.write_text(html, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
