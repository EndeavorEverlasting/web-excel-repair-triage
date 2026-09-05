(function () {
  'use strict';

  var KIND_ORDER = ['invocation', 'run_result', 'failure', 'critique', 'favorite', 'feedback', 'eval', 'proof_receipt'];
  var LOCAL_FAVORITES_SOURCE = 'promptKit.favoritePromptIds.v1';
  var PROOF_EFFECT_LABELS = {
    none: 'no proof',
    support_or_block: 'may support or block',
    lower_or_block: 'lowers or blocks; never raises',
    none_without_independent_verification: 'not proof without independent verification',
    supports_observed_claim: 'supports observed claim only'
  };

  function proofLabel(kind, recordKinds) {
    var meta = (recordKinds && recordKinds[kind]) || {};
    var effect = meta.proof_effect || 'none';
    return PROOF_EFFECT_LABELS[effect] || effect;
  }

  function projectLocalFavorites(favoriteMap, implementations) {
    var ids = [];
    var store = favoriteMap && typeof favoriteMap === 'object' ? favoriteMap : {};
    Object.keys(store).forEach(function (id) {
      if (store[id] === true && String(id || '').trim()) ids.push(String(id).trim().toUpperCase());
    });
    ids.sort();
    var byPrompt = {};
    (implementations || []).forEach(function (item) {
      if (!item || !item.prompt_id) return;
      var key = String(item.prompt_id).toUpperCase();
      if (!byPrompt[key]) byPrompt[key] = [];
      if (item.capability_id && byPrompt[key].indexOf(item.capability_id) < 0) {
        byPrompt[key].push(item.capability_id);
      }
    });
    return ids.map(function (id) {
      var caps = byPrompt[id] || [];
      return {
        record_id: 'local-favorite:' + id,
        record_kind: 'favorite',
        capability_id: caps.length ? caps.join(', ') : 'unlinked',
        implementation_locator: id,
        observed_at: 'local-storage',
        source: LOCAL_FAVORITES_SOURCE,
        subject_ref: id,
        class: 'preference',
        proof_effect: 'none',
        preference_signal: true
      };
    });
  }

  window.PROMPT_KIT_ONTOLOGY_HISTORY = {
    KIND_ORDER: KIND_ORDER,
    LOCAL_FAVORITES_SOURCE: LOCAL_FAVORITES_SOURCE,
    proofLabel: proofLabel,
    projectLocalFavorites: projectLocalFavorites
  };

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
      '.ontology-badge.preference{border-color:rgba(245,158,11,.45);color:#fbbf24}',
      '.ontology-badge.negative_evidence{border-color:rgba(248,113,113,.45);color:#fca5a5}',
      '.ontology-badge.proof{border-color:rgba(52,211,153,.45);color:#6ee7b7}',
      '.ontology-operation{color:var(--text-secondary);font-size:12px;line-height:1.55;margin:8px 0 11px}',
      '.ontology-row{display:grid;grid-template-columns:86px minmax(0,1fr);gap:8px;margin-top:7px;font-size:11px;line-height:1.45}',
      '.ontology-label{color:var(--text-muted);font-weight:700;text-transform:uppercase;font-size:9px;letter-spacing:.05em}',
      '.ontology-value{color:var(--text-secondary);overflow-wrap:anywhere}',
      '.ontology-proof{border-top:1px solid var(--border);margin-top:11px;padding-top:10px;color:var(--text-secondary);font-size:11px;line-height:1.45}',
      '.ontology-link{border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--accent);padding:4px 7px;font-size:10px;cursor:pointer}',
      '.ontology-empty{color:var(--text-muted);font-size:12px;padding:18px;border:1px dashed var(--border);border-radius:9px}',
      '.ontology-section-title{margin:18px 0 8px;color:var(--text-primary);font-size:13px;letter-spacing:.04em;text-transform:uppercase}',
      '.ontology-kind-group{margin-top:12px}',
      '.ontology-kind-title{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;color:var(--text-secondary);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}',
      '.ontology-kind-title span{font-weight:600;text-transform:none;letter-spacing:0;color:var(--text-muted)}',
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

  function evidenceModel() {
    return model.evidence || {};
  }

  function recordKinds() {
    var kinds = evidenceModel().record_kinds;
    return kinds && typeof kinds === 'object' ? kinds : {};
  }

  function historyRecords() {
    var history = evidenceModel().history || {};
    return Array.isArray(history.records) ? history.records : [];
  }

  function localFavoriteStore() {
    if (typeof favoritePromptIds === 'object' && favoritePromptIds) return favoritePromptIds;
    return {};
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
  function ensureOntologyTab() {
    var host = document.querySelector('.cat-tabs');
    if (!host) return;
    var missing = !document.body.contains(topButton);
    if (missing) host.appendChild(topButton);
    if (missing && view && view.classList.contains('active')) deactivate();
  }

  var view = document.createElement('section');
  view.id = 'ontologyView';
  view.className = 'ontology-view';
  view.setAttribute('aria-labelledby', 'ontologyTitle');
  view.innerHTML = [
    '<div class="ontology-hero">',
      '<div class="ontology-kicker">Repository-backed agentic map</div>',
      '<h2 id="ontologyTitle">Capabilities, skills, implementations, and proof</h2>',
      '<p>This view is generated from canonical repository owners. It shows what an operation promises, which reusable skill guides it, how it is implemented, and what its declared proof ceiling allows you to claim. Observed history is distinct from declared proof ceilings.</p>',
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
    '<span class="ontology-stat">' + promptBacked + ' prompt-backed</span>',
    '<span class="ontology-stat">' + historyRecords().length + ' observed history records</span>'
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

  function historyCard(record) {
    var kind = record.record_kind || 'unknown';
    var meta = recordKinds()[kind] || {};
    var effect = meta.proof_effect || record.proof_effect || 'none';
    var klass = meta.class || record.class || 'observation';
    var promptControl = '';
    if (record.implementation_locator && /^P\d+$/i.test(String(record.implementation_locator))) {
      promptControl = ' <button type="button" class="ontology-link" data-prompt-id="' + esc(record.implementation_locator) + '">Open ' + esc(record.implementation_locator) + '</button>';
    }
    return '<article class="ontology-card" data-kind="' + esc(kind) + '"><div class="ontology-card-head"><h3>' + esc(record.record_id || kind) + '</h3><span class="ontology-badge ' + esc(klass) + '">' + esc(kind.replace('_', ' ')) + '</span></div>' +
      '<div class="ontology-operation">' + esc(meta.description || '') + '</div>' +
      '<div class="ontology-row"><span class="ontology-label">Capability</span><span class="ontology-value">' + esc(record.capability_id || 'unlinked') + '</span></div>' +
      '<div class="ontology-row"><span class="ontology-label">Subject</span><span class="ontology-value">' + esc(record.subject_ref || '') + promptControl + '</span></div>' +
      '<div class="ontology-row"><span class="ontology-label">Source</span><span class="ontology-value">' + esc(record.source || '') + '</span></div>' +
      '<div class="ontology-row"><span class="ontology-label">Observed</span><span class="ontology-value">' + esc(record.observed_at || '') + '</span></div>' +
      '<div class="ontology-proof"><span class="ontology-label">Proof effect</span><br>' + esc(proofLabel(kind, recordKinds()) || effect) + (klass === 'preference' ? '. This is a preference signal, not correctness proof.' : '') + '</div></article>';
  }

  function renderCapabilities(query) {
    var items = model.capabilities.filter(function (item) {
      return containsQuery([item.id, item.operation, item.skill, JSON.stringify(item.implementation || {}), (item.trigger_ids || []).join(' '), item.proof_ceiling || ''], query);
    });
    body.innerHTML = '<div class="ontology-note"><strong>Capability answers:</strong> “What operation can I rely on, and where is its boundary?” Implementation details are shown as relationships rather than treated as the capability itself.</div>' +
      (items.length ? '<div class="ontology-grid">' + items.map(function (item) { return capabilityCard(item, false); }).join('') + '</div>' : '<div class="ontology-empty">No matching capabilities.</div>');
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

  function renderKindGroup(kind, records, query) {
    var meta = recordKinds()[kind] || {};
    var items = records.filter(function (record) {
      return record.record_kind === kind && containsQuery([
        record.record_id || '',
        kind,
        record.capability_id || '',
        record.implementation_locator || '',
        record.subject_ref || '',
        record.source || '',
        meta.class || '',
        proofLabel(kind, recordKinds())
      ], query);
    });
    var empty = '<div class="ontology-empty">No observed ' + esc(kind.replace('_', ' ')) + ' records.</div>';
    return '<section class="ontology-kind-group" data-kind="' + esc(kind) + '"><div class="ontology-kind-title">' + esc(kind.replace('_', ' ')) + ' · ' + esc(meta.class || 'observation') + '<span> · ' + esc(proofLabel(kind, recordKinds())) + '</span></div>' +
      (items.length ? '<div class="ontology-grid">' + items.map(historyCard).join('') + '</div>' : empty) +
      '</section>';
  }

  function renderEvidence(query) {
    var declared = model.capabilities.filter(function (item) {
      return containsQuery([item.id, item.operation, item.proof_ceiling || ''], query);
    });
    var ledger = historyRecords();
    var localFavorites = projectLocalFavorites(localFavoriteStore(), model.implementations);
    var note = '<div class="ontology-note"><strong>Declared proof, not run history.</strong> These ceilings state the maximum claim each registered capability can support. Observed history is distinct from declared proof ceilings. Invocation does not prove success. Favorites remain a preference signal, not correctness proof. Feedback transport stays out of this view.</div>';
    var declaredSection = '<h3 class="ontology-section-title">Declared proof ceilings</h3>' +
      (declared.length ? '<div class="ontology-grid">' + declared.map(function (item) { return capabilityCard(item, true); }).join('') + '</div>' : '<div class="ontology-empty">No matching declared ceilings.</div>');
    var historyNote = ledger.length
      ? '<p class="ontology-operation">Repository ledger records remain append-only. Failures stay visible and can lower or block proof, never raise it.</p>'
      : '<p class="ontology-operation">No observed invocation, run result, failure, critique, favorite, feedback, eval, or proof receipt is registered in the repository ledger.</p>';
    var historySection = '<h3 class="ontology-section-title">Observed history</h3>' + historyNote + KIND_ORDER.map(function (kind) {
      return renderKindGroup(kind, ledger, query);
    }).join('');
    var favoriteItems = localFavorites.filter(function (record) {
      return containsQuery([record.record_id, record.implementation_locator, record.capability_id, record.source], query);
    });
    var localSection = '<h3 class="ontology-section-title">Local preference signals</h3><p class="ontology-operation">Local Favorites are read from <code>' + esc(LOCAL_FAVORITES_SOURCE) + '</code>. They are a preference signal, not correctness proof, and they are not copied into the repository ledger.</p>' +
      (favoriteItems.length
        ? '<div class="ontology-grid">' + favoriteItems.map(historyCard).join('') + '</div>'
        : '<div class="ontology-empty">No local Favorites on this device.</div>');
    body.innerHTML = note + declaredSection + historySection + localSection;
  }

  function renderBody() {
    var query = String(search.value || '').trim().toLowerCase();
    if (lens === 'skills') renderSkills(query);
    else if (lens === 'implementations') renderImplementations(query);
    else if (lens === 'evidence') renderEvidence(query);
    else renderCapabilities(query);
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
  ensureOntologyTab();
  if (typeof MutationObserver === 'function') {
    new MutationObserver(ensureOntologyTab).observe(tabs, { childList: true });
  }
  renderBody();
})();
