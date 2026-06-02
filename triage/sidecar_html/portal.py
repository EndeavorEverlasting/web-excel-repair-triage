"""Build self-contained index.html review portals for artifact runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.sidecar_html.loaders import load_csv, load_json, safe_embed_json
from triage.sidecar_html.theme import PORTAL_CSS

TAB_ORDER = ("overview", "review", "preflight", "data")


@dataclass
class PortalSection:
    """Declarative section for the run portal."""

    id: str
    title: str
    tab: str  # overview | review | preflight | data
    kind: str  # kpis | table | preflight | delta | json | links
    # kind-specific (optional)
    items: List[Dict[str, Any]] = field(default_factory=list)
    csv_path: Optional[str] = None
    json_path: Optional[str] = None
    badge_column: Optional[str] = None
    hint: str = ""
    links: List[Dict[str, str]] = field(default_factory=list)


def _resolve_sections(sections: List[PortalSection]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in sections:
        block: Dict[str, Any] = {
            "id": s.id,
            "title": s.title,
            "tab": s.tab,
            "kind": s.kind,
            "hint": s.hint,
        }
        if s.kind == "kpis":
            block["items"] = s.items
        elif s.kind == "links":
            block["links"] = s.links
        elif s.kind == "table":
            rows = load_csv(s.csv_path)
            block["rows"] = rows
            block["truncated"] = len(rows) >= 2000
            block["source"] = str(s.csv_path) if s.csv_path else ""
            block["badge_column"] = s.badge_column or ""
        elif s.kind == "preflight":
            if s.json_path:
                block["entries"] = [{"name": s.title, "data": load_json(s.json_path)}]
            else:
                block["entries"] = s.items
        elif s.kind == "delta":
            block["data"] = load_json(s.json_path) if s.json_path else s.items
        elif s.kind == "json":
            block["data"] = load_json(s.json_path) if s.json_path else s.items
        out.append(block)
    return out


def build_run_portal(
    out_dir: str | Path,
    title: str,
    subtitle: str = "",
    sections: Optional[List[PortalSection]] = None,
    footer_note: str = "",
) -> Path:
    """Write ``{out_dir}/index.html`` and return its path."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sections = sections or []
    payload = {
        "title": title,
        "subtitle": subtitle,
        "sections": _resolve_sections(sections),
        "tabs": list(TAB_ORDER),
    }
    embedded = safe_embed_json(payload)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <style>{PORTAL_CSS}</style>
</head>
<body>
<header>
  <h1>{_esc(title)}</h1>
  <div class="subtle">{_esc(subtitle or "Artifact run review portal — open in any browser.")}</div>
  <div class="path">{_esc(str(out.resolve()))}</div>
</header>
<nav class="tabs" id="tabNav"></nav>
<main id="main"></main>
<footer>{_esc(footer_note or "JSON/CSV sidecars remain alongside this file for automation.")}</footer>
<script>
const PORTAL = {embedded};

function esc(v) {{
  return String(v == null ? "" : v).replace(/[&<>"']/g, c => ({{
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }}[c]));
}}

function badgeClass(cat) {{
  const k = String(cat || "").toLowerCase().replace(/[^a-z0-9_]/g, "_");
  return "badge badge-" + (k || "default");
}}

function showTab(tab) {{
  document.querySelectorAll("nav.tabs button").forEach(b => {{
    b.classList.toggle("active", b.dataset.tab === tab);
  }});
  document.querySelectorAll(".panel").forEach(p => {{
    p.classList.toggle("active", p.dataset.tab === tab);
  }});
}}

function renderKpis(sec) {{
  const cards = (sec.items || []).map(it => {{
    const cls = it.tone === "pass" ? "val pass" : it.tone === "fail" ? "val fail" : "val";
    return `<div class="card"><div class="lbl">${{esc(it.label)}}</div><div class="${{cls}}">${{esc(it.value)}}</div></div>`;
  }}).join("");
  return `<div class="cards">${{cards}}</div>`;
}}

function renderLinks(sec) {{
  return `<div class="links">${{(sec.links || []).map(l =>
    `<a href="${{esc(l.href)}}" target="_blank" rel="noopener">${{esc(l.label)}}</a>`).join("")}}</div>`;
}}

function renderTable(sec) {{
  const rows = sec.rows || [];
  if (!rows.length) return `<p class="hint">No rows in ${{esc(sec.source || "table")}}.</p>`;
  const cols = Object.keys(rows[0]);
  const badgeCol = sec.badge_column;
  const qid = "q-" + sec.id;
  const fid = "f-" + sec.id;
  const html = `
    <div class="toolbar">
      <input id="${{qid}}" placeholder="Search rows…" />
      ${{badgeCol ? `<select id="${{fid}}"><option value="">All categories</option></select>` : ""}}
      <span class="hint">${{rows.length}} rows${{sec.truncated ? " (truncated at 2000)" : ""}}</span>
    </div>
    <div class="table-wrap"><table><thead><tr>${{cols.map(c => `<th>${{esc(c)}}</th>`).join("")}}</tr></thead>
    <tbody id="tb-${{sec.id}}"></tbody></table></div>`;
  setTimeout(() => {{
    const q = document.getElementById(qid);
    const f = document.getElementById(fid);
    if (badgeCol && f) {{
      [...new Set(rows.map(r => r[badgeCol]).filter(Boolean))].sort().forEach(v => {{
        const o = document.createElement("option");
        o.value = v; o.textContent = v; f.appendChild(o);
      }});
    }}
    const paint = () => {{
      const qq = (q?.value || "").toLowerCase();
      const ff = f?.value || "";
      const filtered = rows.filter(r => {{
        const blob = Object.values(r).join(" ").toLowerCase();
        if (qq && !blob.includes(qq)) return false;
        if (ff && String(r[badgeCol] || "") !== ff) return false;
        return true;
      }});
      document.getElementById("tb-" + sec.id).innerHTML = filtered.map(r => `<tr>${{cols.map(c => {{
        let v = r[c];
        if (badgeCol && c === badgeCol) return `<td><span class="${{badgeClass(v)}}">${{esc(v)}}</span></td>`;
        return `<td>${{esc(v)}}</td>`;
      }}).join("")}}</tr>`).join("");
    }};
    q?.addEventListener("input", paint);
    f?.addEventListener("change", paint);
    paint();
  }}, 0);
  return html;
}}

function renderPreflight(sec) {{
  const entries = sec.entries || [];
  return entries.map(e => {{
    const d = e.data || {{}};
    const pass = d.preflight_pass === true || d.webexcel_preflight_pass === true;
    const pill = `<span class="pill ${{pass ? "pill-pass" : "pill-fail"}}">${{pass ? "PASS" : "FAIL"}}</span>`;
    const rows = Object.entries(d).filter(([k]) => !["preflight_pass","webexcel_preflight_pass"].includes(k))
      .map(([k,v]) => `<tr><th>${{esc(k)}}</th><td>${{esc(typeof v === "object" ? JSON.stringify(v) : v)}}</td></tr>`).join("");
    return `<div style="margin-bottom:16px"><h3 style="margin:0 0 8px">${{esc(e.name || sec.title)}} ${{pill}}</h3>
      <div class="table-wrap"><table><tbody>${{rows}}</tbody></table></div></div>`;
  }}).join("");
}}

function renderDelta(sec) {{
  const d = sec.data || {{}};
  const rows = d.by_project || [];
  const max = Math.max(...rows.map(r => Math.abs(Number(r.Delta || 0))), 1);
  const bars = rows.map(r => {{
    const delta = Number(r.Delta || 0);
    const w = Math.min(100, (Math.abs(delta) / max) * 100);
    return `<div class="bar-row"><div>${{esc(r.Project)}}</div><div class="bar"><span style="width:${{w}}%;background:${{delta < 0 ? "var(--fail)" : "var(--pass)"}}"></span></div><div>${{esc(delta)}}</div></div>`;
  }}).join("");
  const table = `<div class="table-wrap"><table><thead><tr><th>Project</th><th>Prior Net</th><th>Current Net</th><th>Delta</th></tr></thead><tbody>
    ${{rows.map(r => `<tr><td>${{esc(r.Project)}}</td><td>${{esc(r["Prior Net"])}}</td><td>${{esc(r["Current Net"])}}</td><td>${{esc(r.Delta)}}</td></tr>`).join("")}}
  </tbody></table></div>`;
  return `<div class="cards">
    <div class="card"><div class="lbl">Total net delta</div><div class="val">${{esc(d.total_net_delta)}}</div></div>
    <div class="card"><div class="lbl">Prior total</div><div class="val">${{esc(d.prior_total_net)}}</div></div>
    <div class="card"><div class="lbl">Current total</div><div class="val">${{esc(d.current_total_net)}}</div></div>
  </div>${{bars}}${{table}}`;
}}

function renderJson(sec) {{
  return `<div class="json-tree">${{esc(JSON.stringify(sec.data, null, 2))}}</div>`;
}}

function renderSection(sec) {{
  let body = "";
  if (sec.kind === "kpis") body = renderKpis(sec);
  else if (sec.kind === "links") body = renderLinks(sec);
  else if (sec.kind === "table") body = renderTable(sec);
  else if (sec.kind === "preflight") body = renderPreflight(sec);
  else if (sec.kind === "delta") body = renderDelta(sec);
  else if (sec.kind === "json") body = renderJson(sec);
  return `<section class="section" id="sec-${{esc(sec.id)}}"><h2>${{esc(sec.title)}}</h2>
    ${{sec.hint ? `<p class="hint">${{esc(sec.hint)}}</p>` : ""}}${{body}}</section>`;
}}

function init() {{
  const usedTabs = [...new Set(PORTAL.sections.map(s => s.tab))];
  const nav = document.getElementById("tabNav");
  const labels = {{ overview: "Overview", review: "Review queue", preflight: "Preflight", data: "Data" }};
  usedTabs.forEach((tab, i) => {{
    const b = document.createElement("button");
    b.textContent = labels[tab] || tab;
    b.dataset.tab = tab;
    b.onclick = () => showTab(tab);
    if (i === 0) b.classList.add("active");
    nav.appendChild(b);
  }});
  const main = document.getElementById("main");
  PORTAL.tabs.filter(t => usedTabs.includes(t)).forEach(tab => {{
    const panel = document.createElement("div");
    panel.className = "panel" + (tab === usedTabs[0] ? " active" : "");
    panel.dataset.tab = tab;
    panel.innerHTML = PORTAL.sections.filter(s => s.tab === tab).map(renderSection).join("");
    main.appendChild(panel);
  }});
}}

init();
</script>
</body>
</html>
"""
    path = out / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
