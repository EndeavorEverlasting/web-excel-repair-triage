(() => {
  "use strict";

  const SCHEMA = "roster-log-v2/v1";
  const REPORT_VERSION = "roster-log-v2-project-report/v1";
  const STORAGE_KEY = "roster-log-v2-state-v1";
  const BASES = new Set(["DEFAULT", "EXPLICIT", "OVERRIDE"]);
  const $ = (id) => document.getElementById(id);
  const els = {
    date: $("workDate"), staff: $("staff"), clockIn: $("clockIn"), clockOut: $("clockOut"),
    paid: $("paidHours"), defaultProject: $("defaultProject"), notes: $("attendanceNotes"),
    allocations: $("allocations"), template: $("allocationTemplate"), projects: $("projectNames"),
    paidTotal: $("paidTotal"), allocatedTotal: $("allocatedTotal"), variance: $("variance"),
    reconcileState: $("reconcileState"), rows: $("dayRows"), message: $("message"), cache: $("cacheStatus"),
    reportRows: $("projectReportRows"), reportPaid: $("reportPaid"), reportAllocated: $("reportAllocated"),
    reportVariance: $("reportVariance"), reportMulti: $("reportMulti")
  };

  let state = loadState();
  let editingKey = null;

  function emptyState() {
    return { schema_version: SCHEMA, projects: [], workstreams: [], attendance: [], allocations: [] };
  }

  // Permissive conversion is intentionally limited to live form math where an
  // empty number field should temporarily behave like zero while the user edits.
  function n(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function strictNumber(value, field, fallback = 0) {
    const candidate = value === undefined || value === null ? fallback : value;
    if (typeof candidate === "boolean" || candidate === "") throw new Error(`${field} must be numeric`);
    const parsed = Number(candidate);
    if (!Number.isFinite(parsed)) throw new Error(`${field} must be numeric`);
    if (parsed < 0) throw new Error(`${field} must be >= 0`);
    return +parsed.toFixed(4);
  }

  function validIsoDate(value) {
    const text = String(value || "").trim();
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
    if (!match) return false;
    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);
    const candidate = new Date(Date.UTC(year, month - 1, day));
    return candidate.getUTCFullYear() === year && candidate.getUTCMonth() === month - 1 && candidate.getUTCDate() === day;
  }

  function cmp(a, b) {
    const left = String(a ?? "");
    const right = String(b ?? "");
    return left === right ? 0 : left < right ? -1 : 1;
  }

  function keyOf(date, staff) { return `${date}::${String(staff).trim()}`; }

  function cleanBasis(value, fallback = "EXPLICIT") {
    let basis;
    if (value === undefined || value === null || (typeof value === "string" && !value.trim())) basis = fallback;
    else if (typeof value !== "string") throw new Error("Allocation basis must be a string when provided");
    else basis = value.trim().toUpperCase();
    if (!BASES.has(basis)) throw new Error(`Unknown allocation basis: ${basis || "<blank>"}`);
    return basis;
  }

  function normalizeLocalState(payload) {
    if (!payload || payload.schema_version !== SCHEMA || !Array.isArray(payload.attendance) || !Array.isArray(payload.allocations)) {
      throw new Error("Not a roster-log-v2/v1 state file");
    }
    const normalized = {
      schema_version: SCHEMA,
      projects: Array.isArray(payload.projects) ? [...payload.projects] : [],
      workstreams: Array.isArray(payload.workstreams) ? [...payload.workstreams] : [],
      attendance: payload.attendance.map((raw) => ({
        ...raw,
        staff: String(raw.staff || "").trim(),
        date: String(raw.date || "").trim(),
        paid_hours: strictNumber(raw.paid_hours, "paid_hours"),
        default_project: String(raw.default_project || "").trim()
      })),
      allocations: payload.allocations.map((raw) => ({
        ...raw,
        staff: String(raw.staff || "").trim(),
        date: String(raw.date || "").trim(),
        project: String(raw.project || "").trim(),
        hours: strictNumber(raw.hours, "allocation hours"),
        basis: cleanBasis(raw.basis, "EXPLICIT")
      }))
    };

    const attendanceKeys = new Set();
    normalized.attendance.forEach((row) => {
      if (!validIsoDate(row.date) || !row.staff) throw new Error("Attendance rows require a valid ISO date and staff.");
      if (row.paid_hours > 0 && !row.default_project) throw new Error(`Default / fallback project required: ${row.date} / ${row.staff}`);
      const key = keyOf(row.date, row.staff);
      if (attendanceKeys.has(key)) throw new Error(`Duplicate attendance day: ${row.date} / ${row.staff}`);
      attendanceKeys.add(key);
    });

    const allocationIds = new Set();
    const allocatedDays = new Set();
    normalized.allocations.forEach((row, index) => {
      if (!validIsoDate(row.date) || !row.staff) throw new Error("Allocation rows require a valid ISO date and staff.");
      const key = keyOf(row.date, row.staff);
      if (!attendanceKeys.has(key)) throw new Error(`Allocation without attendance day: ${row.date} / ${row.staff}`);
      if (!row.project) throw new Error(`Allocation project required: ${row.date} / ${row.staff}`);
      row.allocation_id = String(row.allocation_id || `LOCAL-${row.date.replaceAll("-", "")}-${index + 1}`).trim();
      if (allocationIds.has(row.allocation_id)) throw new Error(`Duplicate allocation ID: ${row.allocation_id}`);
      allocationIds.add(row.allocation_id);
      row.workstream = String(row.workstream || "").trim();
      row.status = String(row.status || "RECONCILED").trim();
      row.notes = String(row.notes || "").trim();
      allocatedDays.add(key);
    });

    normalized.attendance.forEach((row, index) => {
      const key = keyOf(row.date, row.staff);
      if (row.paid_hours <= 0 || allocatedDays.has(key)) return;
      let allocationId = `DEFAULT-${row.date.replaceAll("-", "")}-${index + 1}`;
      while (allocationIds.has(allocationId)) allocationId += "D";
      normalized.allocations.push({
        allocation_id: allocationId,
        date: row.date,
        staff: row.staff,
        project: row.default_project,
        basis: "DEFAULT",
        workstream: "",
        hours: row.paid_hours,
        status: "RECONCILED",
        notes: "Default single-project allocation"
      });
      allocationIds.add(allocationId);
    });
    return normalized;
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyState();
      return normalizeLocalState(JSON.parse(raw));
    } catch (_) {
      return emptyState();
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    els.cache.textContent = `Saved locally · ${state.attendance.length} day${state.attendance.length === 1 ? "" : "s"}`;
  }

  function sortedAttendance(source = state) {
    return [...source.attendance].sort((a, b) => cmp(a.date, b.date) || cmp(a.staff, b.staff));
  }

  function sortedAllocations(source = state) {
    return [...source.allocations].sort((a, b) => cmp(a.date, b.date) || cmp(a.staff, b.staff) || cmp(a.project, b.project) || cmp(a.allocation_id, b.allocation_id));
  }

  function projectList() {
    const names = new Set(state.projects || []);
    state.attendance.forEach((row) => row.default_project && names.add(row.default_project));
    state.allocations.forEach((row) => row.project && names.add(row.project));
    return [...names].filter(Boolean).sort(cmp);
  }

  function canonicalState() {
    const normalized = normalizeLocalState(state);
    const projects = new Set(normalized.projects || []);
    normalized.attendance.forEach((row) => row.default_project && projects.add(row.default_project));
    normalized.allocations.forEach((row) => row.project && projects.add(row.project));
    return {
      ...normalized,
      projects: [...projects].filter(Boolean).sort(cmp),
      workstreams: [...new Set(normalized.workstreams || [])].filter(Boolean).sort(cmp),
      attendance: sortedAttendance(normalized),
      allocations: sortedAllocations(normalized)
    };
  }

  function refreshDatalist() {
    els.projects.replaceChildren(...projectList().map((name) => {
      const option = document.createElement("option");
      option.value = name;
      return option;
    }));
  }

  function allocationCards() { return [...els.allocations.querySelectorAll(".allocation-card")]; }

  function addAllocation(values = {}) {
    const node = els.template.content.firstElementChild.cloneNode(true);
    const project = node.querySelector(".project");
    const basis = node.querySelector(".basis");
    project.value = values.project || els.defaultProject.value || "";
    basis.value = cleanBasis(values.basis, values.project ? "EXPLICIT" : "DEFAULT");
    node.querySelector(".workstream").value = values.workstream || "";
    node.querySelector(".hours").value = values.hours ?? "";
    node.querySelector(".notes").value = values.notes || "";
    node.querySelector(".remove").addEventListener("click", () => {
      if (allocationCards().length === 1) return;
      node.remove();
      renumberAllocations();
      recalc();
    });
    project.addEventListener("input", () => {
      if (basis.value === "DEFAULT" && project.value.trim() !== els.defaultProject.value.trim()) basis.value = "EXPLICIT";
      recalc();
    });
    node.querySelectorAll("input,select").forEach((input) => input.addEventListener("input", recalc));
    els.allocations.appendChild(node);
    renumberAllocations();
    recalc();
  }

  function renumberAllocations() {
    const cards = allocationCards();
    cards.forEach((card, index) => {
      card.querySelector(".allocation-number").textContent = `PROJECT ${index + 1}`;
      card.querySelector(".remove").disabled = cards.length === 1;
    });
  }

  function readAllocations() {
    return allocationCards().map((card) => ({
      project: card.querySelector(".project").value.trim(),
      basis: cleanBasis(card.querySelector(".basis").value),
      workstream: card.querySelector(".workstream").value.trim(),
      hours: n(card.querySelector(".hours").value),
      notes: card.querySelector(".notes").value.trim()
    }));
  }

  function recalc() {
    const paid = n(els.paid.value);
    const allocated = readAllocations().reduce((sum, row) => sum + n(row.hours), 0);
    const variance = +(paid - allocated).toFixed(4);
    els.paidTotal.textContent = paid.toFixed(2);
    els.allocatedTotal.textContent = allocated.toFixed(2);
    els.variance.textContent = variance.toFixed(2);
    const good = Math.abs(variance) <= 0.01;
    els.reconcileState.textContent = good ? "RECONCILED" : "DRAFT — ADJUST ALLOCATION";
    els.reconcileState.className = `state ${good ? "good" : "bad"}`;
  }

  function makeSingleProject() {
    const project = els.defaultProject.value.trim();
    const paid = n(els.paid.value);
    els.allocations.replaceChildren();
    addAllocation({ project, basis: "EXPLICIT", hours: paid, notes: "Explicit full-day project decision" });
  }

  function syncDefault() {
    if (allocationCards().length !== 1) return;
    const card = allocationCards()[0];
    if (card.querySelector(".basis").value !== "DEFAULT") return;
    card.querySelector(".project").value = els.defaultProject.value;
  }

  function saveDay() {
    const workDate = els.date.value;
    const staff = els.staff.value.trim();
    const paid = n(els.paid.value);
    const defaultProject = els.defaultProject.value.trim();
    if (!validIsoDate(workDate) || !staff || !defaultProject || paid <= 0) {
      show("Valid date, staff, paid hours, and default / fallback project are required.", true);
      return;
    }
    const allocations = readAllocations();
    if (allocations.some((row) => !row.project || row.hours < 0 || !BASES.has(row.basis))) {
      show("Every allocation needs a project, basis, and non-negative hours.", true);
      return;
    }
    const allocated = allocations.reduce((sum, item) => sum + item.hours, 0);
    const status = Math.abs(paid - allocated) <= 0.01 ? "RECONCILED" : "DRAFT";
    const newKey = keyOf(workDate, staff);
    if (editingKey && editingKey !== newKey) removeDay(editingKey, false);
    else removeDay(newKey, false);

    state.attendance.push({
      date: workDate,
      staff,
      clock_in: els.clockIn.value,
      clock_out: els.clockOut.value,
      paid_hours: paid,
      default_project: defaultProject,
      notes: els.notes.value.trim()
    });
    allocations.forEach((row, index) => state.allocations.push({
      allocation_id: `LOCAL-${workDate.replaceAll("-", "")}-${staff.replace(/[^A-Za-z0-9]/g, "").slice(0, 12)}-${index + 1}`,
      date: workDate,
      staff,
      project: row.project,
      basis: row.basis,
      workstream: row.workstream,
      hours: row.hours,
      status,
      notes: row.notes
    }));
    state = normalizeLocalState(state);
    state.projects = projectList();
    persist();
    render();
    show("Day saved to local cache.");
    clearEditor();
  }

  function removeDay(key, persistAfter = true) {
    const [date, staff] = key.split("::");
    state.attendance = state.attendance.filter((row) => !(row.date === date && row.staff === staff));
    state.allocations = state.allocations.filter((row) => !(row.date === date && row.staff === staff));
    if (persistAfter) { persist(); render(); }
  }

  function editDay(key) {
    const [date, staff] = key.split("::");
    const attendance = state.attendance.find((row) => row.date === date && row.staff === staff);
    if (!attendance) return;
    const allocations = state.allocations.filter((row) => row.date === date && row.staff === staff);
    editingKey = key;
    els.date.value = attendance.date;
    els.staff.value = attendance.staff;
    els.clockIn.value = attendance.clock_in || "";
    els.clockOut.value = attendance.clock_out || "";
    els.paid.value = attendance.paid_hours;
    els.defaultProject.value = attendance.default_project;
    els.notes.value = attendance.notes || "";
    els.allocations.replaceChildren();
    (allocations.length ? allocations : [{ project: attendance.default_project, basis: "DEFAULT", hours: attendance.paid_hours }]).forEach(addAllocation);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function clearEditor() {
    editingKey = null;
    els.date.value = new Date().toISOString().slice(0, 10);
    els.staff.value = "";
    els.clockIn.value = "";
    els.clockOut.value = "";
    els.paid.value = "8";
    els.defaultProject.value = "";
    els.notes.value = "";
    els.allocations.replaceChildren();
    addAllocation({ basis: "DEFAULT", hours: 8 });
  }

  function reconciliation(row, source = state) {
    const rows = source.allocations.filter((a) => a.date === row.date && a.staff === row.staff);
    const allocated = rows.reduce((sum, a) => sum + n(a.hours), 0);
    const projects = [...new Set(rows.map((a) => a.project).filter(Boolean))].sort(cmp);
    return { allocated, variance: +(row.paid_hours - allocated).toFixed(4), mode: projects.length > 1 ? "MULTI" : "SINGLE", projects };
  }

  function reportSnapshot() {
    const normalized = canonicalState();
    const grouped = new Map();
    normalized.allocations.forEach((row) => {
      if (!grouped.has(row.project)) grouped.set(row.project, { project: row.project, allocated_hours: 0, days: new Set(), staff: new Set(), allocation_count: 0 });
      const item = grouped.get(row.project);
      item.allocated_hours += n(row.hours);
      item.days.add(keyOf(row.date, row.staff));
      item.staff.add(row.staff);
      item.allocation_count += 1;
    });
    const projects = [...grouped.values()].sort((a, b) => cmp(a.project, b.project)).map((row) => ({
      project: row.project,
      allocated_hours: +row.allocated_hours.toFixed(4),
      day_count: row.days.size,
      staff_count: row.staff.size,
      allocation_count: row.allocation_count
    }));
    const paid = normalized.attendance.reduce((sum, row) => sum + n(row.paid_hours), 0);
    const allocated = normalized.allocations.reduce((sum, row) => sum + n(row.hours), 0);
    const multi = normalized.attendance.reduce((sum, row) => sum + (reconciliation(row, normalized).mode === "MULTI" ? 1 : 0), 0);
    const unreconciled = normalized.attendance.reduce((sum, row) => sum + (Math.abs(reconciliation(row, normalized).variance) > 0.01 ? 1 : 0), 0);
    return {
      report_version: REPORT_VERSION,
      schema_version: SCHEMA,
      attendance_days: normalized.attendance.length,
      allocation_rows: normalized.allocations.length,
      paid_hours: +paid.toFixed(4),
      allocated_hours: +allocated.toFixed(4),
      variance: +(paid - allocated).toFixed(4),
      multi_project_days: multi,
      unreconciled_days: unreconciled,
      projects
    };
  }

  function renderProjectReport() {
    const report = reportSnapshot();
    els.reportPaid.textContent = report.paid_hours.toFixed(2);
    els.reportAllocated.textContent = report.allocated_hours.toFixed(2);
    els.reportVariance.textContent = report.variance.toFixed(2);
    els.reportMulti.textContent = String(report.multi_project_days);
    els.reportRows.replaceChildren();
    report.projects.forEach((row) => {
      const tr = document.createElement("tr");
      [row.project, row.allocated_hours.toFixed(2), row.day_count, row.staff_count, row.allocation_count].forEach((value) => {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });
      els.reportRows.appendChild(tr);
    });
  }

  function render() {
    refreshDatalist();
    els.rows.replaceChildren();
    sortedAttendance().forEach((row) => {
      const r = reconciliation(row);
      const tr = document.createElement("tr");
      const values = [row.date, row.staff, n(row.paid_hours).toFixed(2), r.mode, r.allocated.toFixed(2), r.variance.toFixed(2), r.projects.join(" · ")];
      values.forEach((value, index) => {
        const td = document.createElement("td");
        td.textContent = value;
        if (index === 5 && Math.abs(r.variance) > 0.01) td.className = "bad-text";
        tr.appendChild(td);
      });
      const actions = document.createElement("td");
      const edit = document.createElement("button"); edit.textContent = "Edit"; edit.className = "tiny secondary"; edit.onclick = () => editDay(keyOf(row.date, row.staff));
      const del = document.createElement("button"); del.textContent = "Delete"; del.className = "tiny danger"; del.onclick = () => removeDay(keyOf(row.date, row.staff));
      actions.append(edit, del); tr.appendChild(actions); els.rows.appendChild(tr);
    });
    renderProjectReport();
    persist();
  }

  function csvEscape(value) {
    const text = String(value ?? "");
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = document.createElement("a"); a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function exportJson() { download("roster-log-v2-state.json", JSON.stringify(canonicalState(), null, 2), "application/json"); }
  function exportAttendance() {
    const header = ["date","staff","clock_in","clock_out","paid_hours","default_project","notes"];
    const lines = [header.join(","), ...sortedAttendance().map((row) => header.map((k) => csvEscape(row[k])).join(","))];
    download("roster-log-v2-attendance.csv", lines.join("\n"), "text/csv");
  }
  function exportAllocations() {
    const header = ["allocation_id","date","staff","project","basis","workstream","hours","status","notes"];
    const lines = [header.join(","), ...sortedAllocations().map((row) => header.map((k) => csvEscape(row[k])).join(","))];
    download("roster-log-v2-project-allocations.csv", lines.join("\n"), "text/csv");
  }
  function exportProjectReportCsv() {
    const report = reportSnapshot();
    const header = ["project","allocated_hours","day_count","staff_count","allocation_count"];
    const lines = [header.join(","), ...report.projects.map((row) => header.map((k) => csvEscape(row[k])).join(","))];
    download("roster-log-v2-project-report.csv", lines.join("\n"), "text/csv");
  }
  function exportProjectReportJson() {
    download("roster-log-v2-project-report.json", JSON.stringify(reportSnapshot(), null, 2), "application/json");
  }

  async function importJson(event) {
    const file = event.target.files[0]; if (!file) return;
    try {
      state = normalizeLocalState(JSON.parse(await file.text()));
      persist(); render(); clearEditor(); show("Imported and normalized state into local cache.");
    } catch (error) { show(error.message, true); }
    event.target.value = "";
  }

  function show(text, bad = false) { els.message.textContent = text; els.message.className = bad ? "bad-text" : ""; }

  $("addProject").onclick = () => addAllocation({ basis: "EXPLICIT", hours: 0 });
  $("singleProject").onclick = makeSingleProject;
  $("saveDay").onclick = saveDay;
  $("clearEditor").onclick = clearEditor;
  $("exportJson").onclick = exportJson;
  $("exportAttendance").onclick = exportAttendance;
  $("exportAllocations").onclick = exportAllocations;
  $("exportProjectReportCsv").onclick = exportProjectReportCsv;
  $("exportProjectReportJson").onclick = exportProjectReportJson;
  $("importJson").addEventListener("change", importJson);
  els.paid.addEventListener("input", recalc);
  els.defaultProject.addEventListener("input", syncDefault);

  clearEditor();
  render();
})();
