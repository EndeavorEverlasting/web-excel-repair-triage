'use strict';

class HotkeyError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'HotkeyError';
    this.code = code;
  }
}

function normalizeGesture(raw) {
  return String(raw || '').trim().toLowerCase();
}

function normalizePromptId(raw) {
  var value = String(raw || '').trim().toUpperCase();
  if (!/^P\d+$/.test(value)) throw new HotkeyError('INVALID_PROMPT_ID', 'Prompt identifiers must look like P95.');
  return value;
}

function isEditableTarget(target) {
  if (!target) return false;
  var tag = String(target.tagName || '').toUpperCase();
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || !!target.isContentEditable;
}

class ShortcutPolicy {
  constructor(options) {
    options = options || {};
    this.reserved = new Set((options.reserved || ['f', '[', ']']).map(normalizeGesture));
  }

  validateBinding(binding, effectiveBindings, promptCatalog) {
    var gesture = normalizeGesture(binding.gesture);
    if (!gesture) throw new HotkeyError('INVALID_GESTURE', 'Shortcut gesture is empty.');
    if (this.reserved.has(gesture) || effectiveBindings.has(gesture)) {
      throw new HotkeyError('RESERVED_COLLISION', 'Shortcut collides with an existing binding.');
    }
    if (binding.command === 'OPEN_PROMPT') {
      var promptId = normalizePromptId(binding.promptId);
      if (!promptCatalog.has(promptId)) throw new HotkeyError('UNKNOWN_PROMPT', 'Prompt does not exist in the canonical catalog.');
      return { gesture: gesture, command: binding.command, promptId: promptId };
    }
    throw new HotkeyError('UNKNOWN_COMMAND', 'Unsupported user shortcut command.');
  }
}

class ShortcutRegistry {
  constructor(options) {
    this.policy = options.policy;
    this.store = options.store;
    this.promptCatalog = options.promptCatalog;
    this.builtIns = new Map([
      ['f', { gesture: 'f', command: 'FILTER_TOGGLE' }],
      ['[', { gesture: '[', command: 'FILTER_HIDE' }],
      [']', { gesture: ']', command: 'FILTER_SHOW' }]
    ]);
    this.userBindings = new Map();
    this.trace = options.trace || [];
  }

  effectiveBindings() {
    var merged = new Map(this.builtIns);
    this.userBindings.forEach(function(value, key) { merged.set(key, value); });
    return merged;
  }

  configure(binding) {
    var candidate = this.policy.validateBinding(binding, this.effectiveBindings(), this.promptCatalog);
    var next = new Map(this.userBindings);
    next.set(candidate.gesture, candidate);
    var serialized = Array.from(next.values());
    try {
      this.store.save(serialized);
    } catch (error) {
      this.trace.push({ layer: 'registry', event: 'configure_failed', code: 'PERSISTENCE_FAILED', gesture: candidate.gesture });
      throw new HotkeyError('PERSISTENCE_FAILED', String(error && error.message || error));
    }
    this.userBindings = next;
    this.trace.push({ layer: 'registry', event: 'configured', gesture: candidate.gesture, command: candidate.command, promptId: candidate.promptId || null });
    return candidate;
  }
}

class FilterVisibility {
  constructor(initialVisible, trace) {
    this.visible = initialVisible !== false;
    this.trace = trace || [];
  }
  show() { return this.setVisible(true, 'FILTER_SHOW'); }
  hide() { return this.setVisible(false, 'FILTER_HIDE'); }
  toggle() { return this.setVisible(!this.visible, 'FILTER_TOGGLE'); }
  setVisible(value, command) {
    this.visible = !!value;
    var result = { visible: this.visible };
    this.trace.push({ layer: 'filter', event: 'visibility_changed', command: command, visible: this.visible });
    return result;
  }
}

class ShortcutDispatcher {
  constructor(options) {
    this.registry = options.registry;
    this.filterVisibility = options.filterVisibility;
    this.promptNavigator = options.promptNavigator;
    this.trace = options.trace || [];
    this.buffer = '';
  }

  resetSequence(reason) {
    if (this.buffer) this.trace.push({ layer: 'dispatcher', event: 'sequence_reset', reason: reason, buffer: this.buffer });
    this.buffer = '';
  }

  execute(binding) {
    var result;
    if (binding.command === 'FILTER_HIDE') result = this.filterVisibility.hide();
    else if (binding.command === 'FILTER_SHOW') result = this.filterVisibility.show();
    else if (binding.command === 'FILTER_TOGGLE') result = this.filterVisibility.toggle();
    else if (binding.command === 'OPEN_PROMPT') result = this.promptNavigator.openPrompt(binding.promptId);
    else throw new HotkeyError('UNKNOWN_COMMAND', binding.command);
    this.trace.push({ layer: 'dispatcher', event: 'dispatched', command: binding.command, promptId: binding.promptId || null });
    return { handled: true, binding: binding, result: result };
  }

  handleKey(event) {
    event = event || {};
    if (event.defaultPrevented || event.altKey || event.metaKey || event.ctrlKey) return { handled: false, reason: 'MODIFIED_OR_PREVENTED' };
    if (isEditableTarget(event.target)) return { handled: false, reason: 'EDITABLE_TARGET' };

    var key = normalizeGesture(event.key);
    if (key === 'escape') {
      this.resetSequence('escape');
      return { handled: false, reason: 'SEQUENCE_CANCELLED' };
    }

    var bindings = this.registry.effectiveBindings();
    if (bindings.has(key)) {
      this.resetSequence('direct_command');
      return this.execute(bindings.get(key));
    }

    if (/^[a-z0-9]$/.test(key)) {
      this.buffer += key;
      var exact = bindings.get(this.buffer);
      if (exact) {
        this.buffer = '';
        return this.execute(exact);
      }
      var hasPrefix = Array.from(bindings.keys()).some(function(gesture) { return gesture.length > 1 && gesture.indexOf(this.buffer) === 0; }, this);
      if (hasPrefix) return { handled: true, pending: true, buffer: this.buffer };
      this.resetSequence('no_match');
    }
    return { handled: false, reason: 'NO_MATCH' };
  }
}

class MemoryStore {
  constructor(options) {
    this.value = [];
    this.fail = !!(options && options.fail);
    this.saveCalls = 0;
  }
  save(value) {
    this.saveCalls += 1;
    if (this.fail) throw new Error('storage unavailable');
    this.value = JSON.parse(JSON.stringify(value));
  }
}

class PromptNavigatorFake {
  constructor(trace) {
    this.opened = [];
    this.trace = trace || [];
  }
  openPrompt(promptId) {
    this.opened.push(promptId);
    this.trace.push({ layer: 'navigator', event: 'prompt_opened', promptId: promptId });
    return { promptId: promptId };
  }
}

function buildProgram(options) {
  options = options || {};
  var trace = [];
  var catalog = new Set(options.promptIds || ['P95']);
  var policy = new ShortcutPolicy();
  var store = options.store || new MemoryStore();
  var registry = new ShortcutRegistry({ policy: policy, store: store, promptCatalog: catalog, trace: trace });
  var filterVisibility = new FilterVisibility(true, trace);
  var promptNavigator = new PromptNavigatorFake(trace);
  var dispatcher = new ShortcutDispatcher({ registry: registry, filterVisibility: filterVisibility, promptNavigator: promptNavigator, trace: trace });
  return { trace: trace, catalog: catalog, policy: policy, store: store, registry: registry, filterVisibility: filterVisibility, promptNavigator: promptNavigator, dispatcher: dispatcher };
}

function assert(condition, message) {
  if (!condition) throw new Error('ASSERTION_FAILED: ' + message);
}

function expectHotkeyError(code, fn) {
  try { fn(); } catch (error) {
    assert(error instanceof HotkeyError, 'expected HotkeyError');
    assert(error.code === code, 'expected ' + code + ', got ' + error.code);
    return error;
  }
  throw new Error('ASSERTION_FAILED: expected error ' + code);
}

function runSelfTest() {
  var program = buildProgram({ promptIds: ['P95', 'P07'] });

  program.dispatcher.handleKey({ key: '[' });
  assert(program.filterVisibility.visible === false, 'explicit hide should own filter state');
  program.dispatcher.handleKey({ key: ']' });
  assert(program.filterVisibility.visible === true, 'explicit show should own filter state');
  program.dispatcher.handleKey({ key: 'f' });
  assert(program.filterVisibility.visible === false, 'toggle should use the same state owner');

  var configured = program.registry.configure({ gesture: 'p95', command: 'OPEN_PROMPT', promptId: 'p95' });
  assert(configured.promptId === 'P95', 'prompt id should normalize to canonical identity');
  assert(program.store.saveCalls === 1, 'validated configuration should persist once');

  var p1 = program.dispatcher.handleKey({ key: 'p' });
  var p2 = program.dispatcher.handleKey({ key: '9' });
  var p3 = program.dispatcher.handleKey({ key: '5' });
  assert(p1.pending && p2.pending, 'partial prompt id should remain pending');
  assert(p3.handled && program.promptNavigator.opened[0] === 'P95', 'p95 should traverse dispatcher to PromptNavigator');

  var beforeEditable = program.promptNavigator.opened.length;
  var editable = program.dispatcher.handleKey({ key: 'p', target: { tagName: 'INPUT' } });
  assert(editable.reason === 'EDITABLE_TARGET', 'typing in inputs must be ignored');
  assert(program.promptNavigator.opened.length === beforeEditable, 'editable target must not navigate');

  expectHotkeyError('RESERVED_COLLISION', function() {
    program.registry.configure({ gesture: 'f', command: 'OPEN_PROMPT', promptId: 'P95' });
  });
  expectHotkeyError('UNKNOWN_PROMPT', function() {
    program.registry.configure({ gesture: 'p999', command: 'OPEN_PROMPT', promptId: 'P999' });
  });

  var failingStore = new MemoryStore({ fail: true });
  var failing = buildProgram({ promptIds: ['P95'], store: failingStore });
  expectHotkeyError('PERSISTENCE_FAILED', function() {
    failing.registry.configure({ gesture: 'p95', command: 'OPEN_PROMPT', promptId: 'P95' });
  });
  assert(!failing.registry.userBindings.has('p95'), 'failed persistence must not publish in-memory binding');

  return {
    status: 'PASS',
    assertions: 13,
    success_paths: ['FILTER_HIDE', 'FILTER_SHOW', 'FILTER_TOGGLE', 'OPEN_PROMPT(P95)'],
    failure_paths: ['EDITABLE_TARGET', 'RESERVED_COLLISION', 'UNKNOWN_PROMPT', 'PERSISTENCE_FAILED'],
    trace: program.trace
  };
}

if (require.main === module) {
  process.stdout.write(JSON.stringify(runSelfTest()));
}

module.exports = {
  HotkeyError: HotkeyError,
  ShortcutPolicy: ShortcutPolicy,
  ShortcutRegistry: ShortcutRegistry,
  ShortcutDispatcher: ShortcutDispatcher,
  FilterVisibility: FilterVisibility,
  MemoryStore: MemoryStore,
  PromptNavigatorFake: PromptNavigatorFake,
  buildProgram: buildProgram,
  normalizeGesture: normalizeGesture,
  normalizePromptId: normalizePromptId,
  isEditableTarget: isEditableTarget,
  runSelfTest: runSelfTest
};
