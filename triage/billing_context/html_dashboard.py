from __future__ import annotations

import json
from pathlib import Path

from .exporters import summarize_by_batch, summarize_by_context, summarize_by_tech
from .models import Mismatch, WorkEntry


def export_html_dashboard(entries: list[WorkEntry], mismatches: list[Mismatch], out_path: str) -> str:
    payload = {
        "entries": [e.to_dict() for e in entries],
        "mismatches": [m.to_dict() for m in mismatches],
        "summary": {
            "total_hours": round(sum(e.hours for e in entries), 2),
            "row_count": len(entries),
            "by_context": summarize_by_context(entries),
            "by_tech": summarize_by_tech(entries),
            "by_batch": summarize_by_batch(entries),
        },
    }

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Billing Context Dashboard</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --panel2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #38bdf8;
      --red: #f87171;
      --amber: #fbbf24;
      --blue: #60a5fa;
      --green: #34d399;
      --gray: #94a3b8;
    }}
    body {{
      margin: 0;
      font-family: system-ui, Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      padding: 24px;
      border-bottom: 1px solid #334155;
      background: #020617;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .subtle {{ color: var(--muted); }}
    main {{ padding: 24px; display: grid; gap: 20px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 8px 22px rgba(0,0,0,.22);
    }}
    .card .value {{ font-size: 30px; font-weight: 800; margin-top: 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 20px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #334155;
      text-align: left;
      font-size: 13px;
      vertical-align: top;
    }}
    th {{ background: var(--panel2); position: sticky; top: 0; }}
    input, select {{
      background: #020617;
      color: var(--text);
      border: 1px solid #475569;
      border-radius: 10px;
      padding: 9px 10px;
      margin-right: 10px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 220px 1fr 80px;
      align-items: center;
      gap: 10px;
      margin: 10px 0;
    }}
    .bar {{
      height: 16px;
      background: #1e293b;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar span {{
      display: block;
      height: 100%;
      background: var(--accent);
      border-radius: 999px;
    }}
    .severity-red {{ color: var(--red); font-weight: 700; }}
    .severity-amber {{ color: var(--amber); font-weight: 700; }}
    .severity-blue {{ color: var(--blue); font-weight: 700; }}
    .severity-gray {{ color: var(--gray); font-weight: 700; }}
  </style>
</head>
<body>
<header>
  <h1>Billing Context Dashboard</h1>
  <div class="subtle">Self-contained browser review: no Office license required.</div>
</header>
<main>
  <section class="cards" id="cards"></section>
  <section class="grid">
    <div class="card"><h2>Hours by Work Context</h2><div id="contextBars"></div></div>
    <div class="card"><h2>Top Technician Hours</h2><div id="techBars"></div></div>
  </section>
  <section class="card">
    <h2>Mismatches</h2>
    <div>
      <input id="mismatchSearch" placeholder="Search mismatches">
      <select id="severityFilter">
        <option value="">All severities</option>
        <option value="red">Red</option>
        <option value="amber">Amber</option>
        <option value="blue">Blue</option>
        <option value="gray">Gray</option>
      </select>
    </div>
    <div id="mismatchTable"></div>
  </section>
  <section class="card">
    <h2>Row-Level Work Context</h2>
    <div>
      <input id="entrySearch" placeholder="Search entries">
      <select id="monthFilter">
        <option value="">All months</option>
        <option value="04">April</option>
        <option value="05">May</option>
      </select>
    </div>
    <div id="entryTable"></div>
  </section>
</main>
<script>
const DATA = {json.dumps(payload, ensure_ascii=False)};

function money(n) {{ return Number(n || 0).toFixed(2); }}

function renderCards() {{
  document.getElementById("cards").innerHTML = `
    <div class="card"><div class="subtle">Total Hours</div><div class="value">${{money(DATA.summary.total_hours)}}</div></div>
    <div class="card"><div class="subtle">Rows</div><div class="value">${{DATA.summary.row_count}}</div></div>
    <div class="card"><div class="subtle">Mismatches</div><div class="value">${{DATA.mismatches.length}}</div></div>`;
}}

function renderBars(targetId, rows, labelKey) {{
  const max = Math.max(...rows.map(r => Number(r.Hours || 0)), 1);
  document.getElementById(targetId).innerHTML = rows.map(r => {{
    const width = (Number(r.Hours || 0) / max) * 100;
    return `<div class="bar-row"><div>${{r[labelKey]}}</div><div class="bar"><span style="width:${{width}}%"></span></div><div>${{money(r.Hours)}}</div></div>`;
  }}).join("");
}}

function renderMismatchTable() {{
  const q = document.getElementById("mismatchSearch").value.toLowerCase();
  const sev = document.getElementById("severityFilter").value;
  const rows = DATA.mismatches.filter(r => {{
    const blob = Object.values(r).join(" ").toLowerCase();
    return (!sev || r.severity === sev) && (!q || blob.includes(q));
  }});
  document.getElementById("mismatchTable").innerHTML = `
    <table><thead><tr><th>Severity</th><th>Type</th><th>Tech</th><th>Date</th><th>From</th><th>To</th><th>Recommendation</th></tr></thead>
    <tbody>${{rows.map(r => `<tr>
      <td class="severity-${{r.severity}}">${{r.severity}}</td><td>${{r.mismatch_type}}</td><td>${{r.tech}}</td>
      <td>${{r.work_date}}</td><td>${{r.source_a_value}}</td><td>${{r.source_b_value}}</td><td>${{r.recommendation}}</td></tr>`).join("")}}</tbody></table>`;
}}

function renderEntryTable() {{
  const q = document.getElementById("entrySearch").value.toLowerCase();
  const month = document.getElementById("monthFilter").value;
  const rows = DATA.entries.filter(r => {{
    const blob = Object.values(r).join(" ").toLowerCase();
    return (!month || String(r.work_date).slice(5,7) === month) && (!q || blob.includes(q));
  }});
  document.getElementById("entryTable").innerHTML = `
    <table><thead><tr><th>Date</th><th>Tech</th><th>Hours</th><th>Context</th><th>Reason</th><th>Original Assignment</th></tr></thead>
    <tbody>${{rows.map(r => `<tr><td>${{r.work_date}}</td><td>${{r.tech}}</td><td>${{money(r.hours)}}</td>
      <td>${{r.work_context}}</td><td>${{r.context_reason}}</td><td>${{r.original_assignment}}</td></tr>`).join("")}}</tbody></table>`;
}}

renderCards();
renderBars("contextBars", DATA.summary.by_context, "Work Context");
renderBars("techBars", DATA.summary.by_tech.slice(0, 12), "Tech");
renderMismatchTable();
renderEntryTable();
document.getElementById("mismatchSearch").addEventListener("input", renderMismatchTable);
document.getElementById("severityFilter").addEventListener("change", renderMismatchTable);
document.getElementById("entrySearch").addEventListener("input", renderEntryTable);
document.getElementById("monthFilter").addEventListener("change", renderEntryTable);
</script>
</body>
</html>
"""

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding="utf-8")
    return out_path
