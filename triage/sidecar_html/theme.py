"""DeployAxis-inspired dark ops dashboard CSS (aligned with billing_context)."""

PORTAL_CSS = """
:root {
  --bg: #0b1220;
  --panel: #111827;
  --panel2: #1f2937;
  --border: #334155;
  --text: #e5e7eb;
  --muted: #9ca3af;
  --accent: #38bdf8;
  --pass: #34d399;
  --fail: #f87171;
  --warn: #fbbf24;
  --mono: ui-monospace, SFMono-Regular, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, "Segoe UI", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}
header {
  padding: 20px 28px;
  border-bottom: 1px solid var(--border);
  background: #020617;
  position: sticky;
  top: 0;
  z-index: 20;
}
header h1 { margin: 0 0 6px; font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }
header .subtle { color: var(--muted); font-size: 14px; }
header .path { font-family: var(--mono); font-size: 12px; color: var(--accent); margin-top: 8px; word-break: break-all; }
nav.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 28px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
  position: sticky;
  top: 88px;
  z-index: 15;
}
nav.tabs button {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  padding: 8px 16px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
nav.tabs button.active {
  background: var(--accent);
  color: #0b1220;
  border-color: var(--accent);
}
main { padding: 24px 28px 48px; max-width: 1400px; margin: 0 auto; }
.panel {
  display: none;
  animation: fade 0.2s ease;
}
.panel.active { display: block; }
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
.section {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}
.section h2 {
  margin: 0 0 12px;
  font-size: 18px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}
.section .hint { color: var(--muted); font-size: 13px; margin: -6px 0 14px; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}
.card {
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
}
.card .lbl { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
.card .val { font-size: 28px; font-weight: 800; margin-top: 6px; color: var(--accent); }
.card .val.pass { color: var(--pass); }
.card .val.fail { color: var(--fail); }
.toolbar { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; align-items: center; }
.toolbar input, .toolbar select {
  background: #020617;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
}
.table-wrap { overflow: auto; max-height: 520px; border-radius: 12px; border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 9px 11px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
th {
  background: var(--panel2);
  position: sticky;
  top: 0;
  z-index: 2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--muted);
}
tr:hover td { background: rgba(56, 189, 248, 0.06); }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.badge-override_applied, .badge-override { background: #1e3a5f; color: var(--accent); }
.badge-long_shift { background: #422006; color: var(--warn); }
.badge-unassigned, .badge-malformed { background: #450a0a; color: var(--fail); }
.badge-default { background: var(--panel2); color: var(--muted); }
.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.pill-pass { background: rgba(52, 211, 153, 0.15); color: var(--pass); }
.pill-fail { background: rgba(248, 113, 113, 0.15); color: var(--fail); }
.bar-row { display: grid; grid-template-columns: 200px 1fr 72px; gap: 10px; align-items: center; margin: 8px 0; }
.bar { height: 14px; background: #1e293b; border-radius: 999px; overflow: hidden; }
.bar span { display: block; height: 100%; background: var(--accent); border-radius: 999px; }
.json-tree {
  font-family: var(--mono);
  font-size: 12px;
  background: #020617;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  overflow: auto;
  max-height: 400px;
  white-space: pre-wrap;
  word-break: break-word;
}
.links { margin-top: 10px; }
.links a { color: var(--accent); text-decoration: none; font-size: 13px; margin-right: 14px; }
.links a:hover { text-decoration: underline; }
footer { padding: 16px 28px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--border); }
"""
