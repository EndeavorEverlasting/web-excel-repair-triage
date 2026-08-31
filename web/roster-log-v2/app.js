(() => {
  "use strict";

  const SCHEMA = "roster-log-v2/v1";
  const STORAGE_KEY = "roster-log-v2-state-v1";
  const $ = (id) => document.getElementById(id);
  const els = {
    date: $("workDate"), staff: $("staff"), clockIn: $("clockIn"), clockOut: $("clockOut"),
    paid: $("paidHours"), defaultProject: $("defaultProject"), notes: $("attendanceNotes"),
    allocations: $("allocations"), template: $("allocationTemplate"), projects: $("projectNames"),
    paidTotal: $("paidTotal"), allocatedTotal: $("allocatedTotal"), variance: $("variance"),
    reconcileState: $("reconcileState"), rows: $("dayRows"), message: $("message"), cache: $("cacheStatus")
  };

  let state = loadState();
  let editingKey = null;

  function emptyState() {
    return { schema_version: SCHEMA, projects: [], workstreams: [], attendance: [], allocations: [] };
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyState();
      const parsed = JSON.parse(raw);
      return parsed && parsed.schema_version === SCHEMA ? parsed : emptyState();
    } catch (_) {
      return emptyState();
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    els.cache.textContent = `Saved locally · ${state.attendance.length} day${state.attendance.length === 1 ? "" : "s"}`;
  }

  function n(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function keyOf(date, staff) { return `${date}::${staff.trim()}`; }

  function projectList() {
    const names = new Set(state.projects || []);
    state.attendance.forEach((row) => row.default_project && names.add(row.default_project));
    state.allocations.forEach((row) => row.project && names.add(row.project));
    return [...names].filter(Boolean).sort((a, b) => a.localeCompare(b));
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
    node.querySelector(".project").value = values.project || els.defaultProject.value || "";
    node.querySelector(".workstream").value = values.workstream || "";
    node.querySelector(".hours").value = values.hours ?? "";
    node.querySelector(".notes").value = values.notes || "";
    node.querySelector(".remove").addEventListener("click", () => {
      if (allocationCards().length === 1) return;
      node.remove();
      renumberAllocations();
      recalc();
    });
    node.querySelectorAll("input").forEach((input) => input.addEventListener("input", recalc));
    els.allocations.appendChild(node);
    renumberAllocations();
    recalc();
  }

  function renumberAllocations() {
    allocationCards().forEach((card, index) => {
      card.querySelector(".allocation-number").textContent = `PROJECT ${index + 1}`;
      card.querySelector(".remove").disabled = allocationCards().length === 1;
    });
  }

  function readAllocations() {
    return allocationCards().map((card) => ({
      project: card.querySelector(".project").value.trim(),
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
    addAllocation({ project, hours: paid, notes: "Full-day project decision" });
  }

  function syncDefault() {
    if (allocationCards().length !== 1) return;
    const projectInput = allocationCards()[0].querySelector(".project");
    if (!projectInput.value || projectInput.dataset.auto !== "off") projectInput.value = els.defaultProject.value;
  }

  function saveDay() {
    const workDate = els.date.value;
    const staff = els.staff.value.trim();
    const paid = n(els.paid.value);
    const defaultProject = els.defaultProject.value.trim();
    if (!workDate || !staff || !defaultProject || paid <= 0) {
      show("Date, staff, paid hours, and default project are required.", true);
      return;
    }
    const allocations = readAllocations();
    if (allocations.some((row) => !row.project || row.hours < 0)) {
      show("Every allocation needs a project and non-negative hours.", true);
      return;
    }
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
      workstream: row.workstream,
      hours: row.hours,
      status: Math.abs(paid - allocations.reduce((sum, item) => sum + item.hours, 0)) <= 0.01 ? "RECONCILED" : "DRAFT",
      notes: row.notes
    }));
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
    (allocations.length ? allocations : [{ project: attendance.default_project, hours: attendance.paid_hours }]).forEach(addAllocation);
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
    addAllocation({ hours: 8 });
  }

  function reconciliation(row) {
    const rows = state.allocations.filter((a) => a.date === row.date && a.staff === row.staff);
    const allocated = rows.reduce((sum, a) => sum + n(a.hours), 0);
    const projects = new Set(rows.map((a) => a.project).filter(Boolean));
    return { allocated, variance: +(row.paid_hours - allocated).toFixed(4), mode: projects.size > 1 ? "MULTI" : "SINGLE", projects: [...projects] };
  }

  function render() {
    refreshDatalist();
    els.rows.replaceChildren();
    [...state.attendance].sort((a, b) => a.date.localeCompare(b.date) || a.staff.localeCompare(b.staff)).forEach((row) => {
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

  function exportJson() { download("roster-log-v2-state.json", JSON.stringify(state, null, 2), "application/json"); }
  function exportAttendance() {
    const header = ["date","staff","clock_in","clock_out","paid_hours","default_project","notes"];
    const lines = [header.join(","), ...state.attendance.map((row) => header.map((k) => csvEscape(row[k])).join(","))];
    download("roster-log-v2-attendance.csv", lines.join("\n"), "text/csv");
  }
  function exportAllocations() {
    const header = ["allocation_id","date","staff","project","workstream","hours","status","notes"];
    const lines = [header.join(","), ...state.allocations.map((row) => header.map((k) => csvEscape(row[k])).join(","))];
    download("roster-log-v2-project-allocations.csv", lines.join("\n"), "text/csv");
  }

  async function importJson(event) {
    const file = event.target.files[0]; if (!file) return;
    try {
      const incoming = JSON.parse(await file.text());
      if (incoming.schema_version !== SCHEMA || !Array.isArray(incoming.attendance) || !Array.isArray(incoming.allocations)) throw new Error("Not a roster-log-v2/v1 state file");
      state = incoming; persist(); render(); clearEditor(); show("Imported state into local cache.");
    } catch (error) { show(error.message, true); }
    event.target.value = "";
  }

  function show(text, bad = false) { els.message.textContent = text; els.message.className = bad ? "bad-text" : ""; }

  $("addProject").onclick = () => addAllocation({ hours: 0 });
  $("singleProject").onclick = makeSingleProject;
  $("saveDay").onclick = saveDay;
  $("clearEditor").onclick = clearEditor;
  $("exportJson").onclick = exportJson;
  $("exportAttendance").onclick = exportAttendance;
  $("exportAllocations").onclick = exportAllocations;
  $("importJson").addEventListener("change", importJson);
  els.paid.addEventListener("input", recalc);
  els.defaultProject.addEventListener("input", syncDefault);

  clearEditor();
  render();
})();
