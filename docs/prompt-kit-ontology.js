(function () {
  'use strict';

  var model = window.PROMPT_KIT_ONTOLOGY;
  if (!model || !Array.isArray(model.capabilities) || !Array.isArray(model.skills)) return;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];
    });
  }

  function ensureStyles() {
    if (document.getElementById('prompt-kit-ontology-styles')) return;
    var style = document.createElement('style');
    style.id = 'prompt-kit-ontology-styles';
    style.textContent = [
      '.ontology-active #promptGrid,.ontology-active #doctrineView,.ontology-active .sections-nav,.ontology-active .type-nav{display:none!important}',
      '.ontology-tab{border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-muted);padding:7px 11px;font-size:11px;font-weight:700;cursor:pointer;white-space:nowrap;transition:all .2s}',
      '.ontology-tab:hover,.ontology-tab:focus-visible,.ontology-tab.active{outline:none;border-color:var(--accent);color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}',
      '.ontology-view{display:none;max-width:1500px;margin:14px auto 90px;padding:0 24px}',
      '.ontology-view.active{display:block}',
      '.ontology-hero{border:1px solid var(--border);border-radius:12px;background:var(--bg-secondary);padding:20px;margin-bottom:14px}',
      '.ontology-kicker{font-size:10px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--accent)}',
      '.ontology-hero h2{margin:6px 0 5px;font-size:24px;color:var(--text-primary)}',
      '.ontology-hero p{margin:0;color:var(--text-muted);font-size:13px;line-height:1.55}',
      '.ontology-stats{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}',
      '.ontology-stat{border:1px solid var(--border);border-radius:999px;padding:5px 9px;color:var(--text-secondary);font-size:10px}',
      '.ontology-controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 14px}',
      '.ontology-lens{border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-muted);padding:7px 10px;font-size:11px;font-weight:700;cursor:pointer}',
      '.ontology-lens.active,.ontology-lens:hover,.ontology-lens:focus-visible{outline:none;border-color:var(--accent);color:var(--accent)}',
      '.ontology-search{flex:1;min-width:220px;padding:8px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-primary);font-size:12px}',
      '.ontology-note{border:1px solid var(--border);border-radius:9px;background:var(--bg-secondary);padding:12px 14px;color:var(--text-muted);font-size:12px;line-height:1.5;margin-bottom:12px}',
      '.ontology-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}',
      '.ontology-card{border:1px solid var(--border);border-radius:10px;background:var(--bg-secondary);padding:14px;min-width:0}',
      '.ontology-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px}',
      '.ontology-card h3{margin:0;color:var(--text-primary);font-size:14px;overflow-wrap:anywhere}',
      '.ontology-badge{border:1px solid var(--border);border-radius:999px;padding:3px 7px;color:var(--text-muted);font-size:9px;text-transform:uppercase;white-space:nowrap}',
      '.ontology-operation{color:var(--text-secondary);font-size:12px;line-height:1.5;margin:8px 0 11px}',
      '.ontology-row{display:grid;grid-template-columns:86px minmax(0,1fr);gap:8px;margin-top:7px;font-size:11px;line-height:1.45}',
      '.ontology-label{color:var(--text-muted);font-weight:700;text-transform:uppercase;font-size:9px;letter-spacing:.05em}',
      '.ontology-value{color:var(--text-secondary);overflow-wrap:anywhere}',
      '.ontology-proof{border-top:1px solid var(--border);margin-top:11px;padding-top:10px;color:var(--text-secondary);font-size:11px;line-height:1.45}',
      '.ontology-link{border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--accent);padding:4px 7px;font-size:10px;cursor:pointer}',
      '.ontology-empty{color:var(--text-muted);font-size:12px;padding:18px;border:1px dashed var(--border);border-radius:9px}',
      '@media(max-width:760px){.ontology-view{padding:0 12px}.ontology-hero{padding:15px}.ontology-hero h2{font-size:19px}.ontology-grid{grid-template-columns:1fr}.ontology-controls{align-items:stretch}.ontology-search{flex-basis:100%;min-height:42px}.ontology-tab,.ontology-lens{min-height:40px}}'
    ].join('');
    document.head.appendChild(style);
  }

  function implementationLocator(implementation) {
    if (!implementation) return 'unregistered';
    if (implementation.prompt_id) return implementation.prompt_id;
    if (implementation.path) return implementation.path;
    return Object.keys(implementation).filter(function (key) { return key !== 'kind'; }).map(function (key) {
      return key + ': ' + implementation[key];
    }).join(', ') || 'registered without locator';
  }

  function containsQuery(values, query) {
    if (!query) return true;
    return values.join(' ').toLowerCase().indexOf(query) >= 0;
  }

  ensureStyles();
  var tabs = document.querySelector('.cat-tabs');
  var grid = document.getElementById('promptGrid');
  var doctrine = document.getElementById('doctrineView');
  var host = (doctrine && doctrine.parentNode) || (grid && grid.parentNode);
  if (!tabs || !host) return;

  var topButton = document.createElement('button');
  topButton.type = 'button';
  topButton.className = 'ontology-tab';
  topButton.id = 'ontologyTab';
  topButton.textContent = 'Ontology';
  topButton.setAttribute('aria-controls', 'ontologyView');
  topButton.setAttribute('aria-expanded', 'false');
  tabs.appendChild(topButton);

  var view = document.createElement('section');
  view.id = 'ontologyView';
  view.className = 'ontology-view';
  view.setAttribute('aria-labelledby', 'ontologyTitle');
  view.innerHTML = [
    '<div class="ontology-hero">',
      '<div class="ontology-kicker">Repository-backed agentic map</div>',
      '<h2 id="ontologyTitle">Capabilities, skills, implementations, and proof</h2>',
      '<p>This view is generated from canonical repository owners. It shows what an operation promises, which reusable skill guides it, how it is implemented, and what its declared proof ceiling allows you to claim.</p>',
      '<div class="ontology-stats" id="ontologyStats"></div>',
    '</div>',
    '<div class="ontology-controls" role="toolbar" aria-label="Ontology views">',
      '<button class="ontology-lens active" type="button" data-lens="capabilities">Capabilities</button>',
      '<button class="ontology-lens" type="button" data-lens="skills">Skills</button>',
      '<button class="ontology-lens" type="button" data-lens="implementations">Implementations</button>',
      '<button class="ontology-lens" type="button" data-lens="evidence">Evidence / Proof</button>',
      '<input class="ontology-search" id="ontologySearch" type="search" placeholder="Filter this ontology view" aria-label="Filter ontology view">',
    '</div>',
    '<div id="ontologyBody"></div>'
  ].join('');
  host.insertBefore(view, doctrine || grid || host.firstChild);

  var promptBacked = model.implementations.filter(function (item) { return item.kind === 'prompt'; }).length;
  document.getElementById('ontologyStats').innerHTML = [
    '<span class="ontology-stat">' + model.capabilities.length + ' capabilities</span>',
    '<span class="ontology-stat">' + model.skills.length + ' skills</span>',
    '<span class="ontology-stat">' + model.implementations.length + ' registered implementations</span>',
    '<span class="ontology-stat">' + promptBacked + ' prompt-backed</span>'
  ].join('');

  var lens = 'capabilities';
  var search = document.getElementById('ontologySearch');
  var body = document.getElementById('ontologyBody');

  function openPrompt(promptId, origin) {
    if (promptId && typeof window.showPromptDetail === 'function') {
      window.showPromptDetail(promptId, origin || null);
    }
  }

  function capabilityCard(item, evidenceOnly) {
    var implementation = item.implementation || {};
    var locator = implementationLocator(implementation);
    var promptControl = implementation.kind === 'prompt' && implementation.prompt_id
      ? ' <button type="button" class="ontology-link" data-prompt-id="' + esc(implementation.prompt_id) + '">Open ' + esc(implementation.prompt_id) + '</button>'
      : '';
    if (evidenceOnly) {
      return '<article class="ontology-card"><div class="ontology-card-head"><h3>' + esc(item.id) + '</h3><span class="ontology-badge">declared ceiling</span></div><div class="ontology-operation">' + esc(item.operation) + '</div><div class="ontology-proof"><span class="ontology-label">Proof ceiling</span><br>' + esc(item.proof_ceiling || 'No proof ceiling registered') + '</div></article>';
    }
    return '<article class="ontology-card"><div class="ontology-card-head"><h3>' + esc(item.id) + '</h3><span class="ontology-badge">' + esc(item.status || 'unknown') + '</span></div><div class="ontology-operation">' + esc(item.operation) + '</div>' +
      '<div class="ontology-row"><span class="ontology-label">Skill</span><span class="ontology-value">' + esc(item.skill) + '</span></div>' +
      '<div class="ontology-row"><span class="ontology-label">Implements</span><span class="ontology-value">' + esc(implementation.kind || 'unregistered') + ' · ' + esc(locator) + promptControl + '</span></div>' +
      '<div class="ontology-row"><span class="ontology-label">Triggers</span><span class="ontology-value">' + esc((item.trigger_ids || []).join(', ') || 'none registered') + '</span></div>' +
      '<div class="ontology-proof"><span class="ontology-label">Proof ceiling</span><br>' + esc(item.proof_ceiling || 'No proof ceiling registered') + '</div></article>';
  }

  function renderCapabilities(query, evidenceOnly) {
    var items = model.capabilities.filter(function (item) {
      return containsQuery([item.id, item.operation, item.skill, JSON.stringify(item.implementation || {}), (item.trigger_ids || []).join(' '), item.proof_ceiling || ''], query);
    });
    var note = evidenceOnly
      ? '<div class="ontology-note"><strong>Declared proof, not run history.</strong> These ceilings state the maximum claim each registered capability can support. Live invocation receipts, failures, critiques, and longitudinal metrics remain a separate future evidence/history layer.</div>'
      : '<div class="ontology-note"><strong>Capability answers:</strong> “What operation can I rely on, and where is its boundary?” Implementation details are shown as relationships rather than treated as the capability itself.</div>';
    body.innerHTML = note + (items.length ? '<div class="ontology-grid">' + items.map(function (item) { return capabilityCard(item, evidenceOnly); }).join('') + '</div>' : '<div class="ontology-empty">No matching capabilities.</div>');
  }

  function renderSkills(query) {
    var items = model.skills.filter(function (item) {
      return containsQuery([item.id, item.title, item.path, (item.capability_ids || []).join(' ')], query);
    });
    body.innerHTML = '<div class="ontology-note"><strong>Skill answers:</strong> “What reusable procedure or judgment can an agent apply across missions?” The inventory comes from actual <code>.ai/skills/*/SKILL.md</code> files; an unlinked skill is shown rather than silently invented into a capability.</div>' +
      (items.length ? '<div class="ontology-grid">' + items.map(function (item) {
        return '<article class="ontology-card"><div class="ontology-card-head"><h3>' + esc(item.title || item.id) + '</h3><span class="ontology-badge">skill</span></div><div class="ontology-row"><span class="ontology-label">ID</span><span class="ontology-value">' + esc(item.id) + '</span></div><div class="ontology-row"><span class="ontology-label">Path</span><span class="ontology-value">' + esc(item.path) + '</span></div><div class="ontology-row"><span class="ontology-label">Capabilities</span><span class="ontology-value">' + esc((item.capability_ids || []).join(', ') || 'no registered capability link') + '</span></div></article>';
      }).join('') + '</div>' : '<div class="ontology-empty">No matching skills.</div>');
  }

  function renderImplementations(query) {
    var items = model.implementations.filter(function (item) {
      return containsQuery([item.capability_id, item.kind, item.locator, item.prompt_name || '', item.skill || ''], query);
    });
    body.innerHTML = '<div class="ontology-note"><strong>Implementation answers:</strong> “What concrete mechanism realizes or orchestrates this capability?” Kinds stay heterogeneous—prompt, script, launcher, binary, or another registered form—so the viewer does not flatten mechanisms into one artifact class.</div>' +
      (items.length ? '<div class="ontology-grid">' + items.map(function (item) {
        var open = item.kind === 'prompt' && item.prompt_id ? '<button type="button" class="ontology-link" data-prompt-id="' + esc(item.prompt_id) + '">Open ' + esc(item.prompt_id) + '</button>' : '';
        return '<article class="ontology-card"><div class="ontology-card-head"><h3>' + esc(item.capability_id) + '</h3><span class="ontology-badge">' + esc(item.kind) + '</span></div><div class="ontology-row"><span class="ontology-label">Locator</span><span class="ontology-value">' + esc(item.locator) + ' ' + open + '</span></div><div class="ontology-row"><span class="ontology-label">Skill</span><span class="ontology-value">' + esc(item.skill || '') + '</span></div>' + (item.prompt_name ? '<div class="ontology-row"><span class="ontology-label">Prompt</span><span class="ontology-value">' + esc(item.prompt_name) + '</span></div>' : '') + '</article>';
      }).join('') + '</div>' : '<div class="ontology-empty">No matching implementations.</div>');
  }

  function renderBody() {
    var query = String(search.value || '').trim().toLowerCase();
    if (lens === 'skills') renderSkills(query);
    else if (lens === 'implementations') renderImplementations(query);
    else renderCapabilities(query, lens === 'evidence');
    body.querySelectorAll('[data-prompt-id]').forEach(function (button) {
      button.addEventListener('click', function () { openPrompt(button.getAttribute('data-prompt-id'), button); });
    });
  }

  function activate() {
    document.body.classList.add('ontology-active');
    view.classList.add('active');
    topButton.classList.add('active');
    topButton.setAttribute('aria-expanded', 'true');
    document.querySelectorAll('.cat-tab').forEach(function (button) { button.classList.remove('active'); });
    renderBody();
    try { view.scrollIntoView({block:'start',behavior:'smooth'}); } catch (e) { view.scrollIntoView(); }
  }

  function deactivate() {
    document.body.classList.remove('ontology-active');
    view.classList.remove('active');
    topButton.classList.remove('active');
    topButton.setAttribute('aria-expanded', 'false');
  }

  topButton.addEventListener('click', activate);
  document.querySelectorAll('.cat-tab').forEach(function (button) { button.addEventListener('click', deactivate); });
  var home = document.getElementById('homeReset') || document.querySelector('.logo');
  if (home) home.addEventListener('click', deactivate);
  search.addEventListener('input', renderBody);
  view.querySelectorAll('.ontology-lens').forEach(function (button) {
    button.addEventListener('click', function () {
      lens = button.getAttribute('data-lens');
      view.querySelectorAll('.ontology-lens').forEach(function (peer) { peer.classList.toggle('active', peer === button); });
      renderBody();
    });
  });
  renderBody();
})();
