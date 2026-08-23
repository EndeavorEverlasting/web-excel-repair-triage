'use strict';

class HotkeyError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'HotkeyError';
    this.code = code;
  }
}

const normalizeGesture = raw => String(raw || '').trim().toLowerCase();
const normalizePromptId = raw => {
  const value = String(raw || '').trim().toUpperCase();
  if (!/^P\d+$/.test(value)) throw new HotkeyError('INVALID_PROMPT_ID', 'Expected prompt id like P95.');
  return value;
};
const isEditableTarget = target => {
  const tag = String(target && target.tagName || '').toUpperCase();
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || !!(target && target.isContentEditable);
};

class ShortcutPolicy {
  constructor(reserved = ['`', 'f', '[', ']', '1', '4', '5']) {
    this.reserved = new Set(reserved.map(normalizeGesture));
  }
  validateBinding(binding, effectiveBindings, promptCatalog) {
    const gesture = normalizeGesture(binding.gesture);
    if (!gesture) throw new HotkeyError('INVALID_GESTURE', 'Gesture is empty.');
    if (this.reserved.has(gesture) || effectiveBindings.has(gesture)) {
      throw new HotkeyError('RESERVED_COLLISION', 'Gesture collides with an effective binding.');
    }
    if (binding.command !== 'COPY_PROMPT') throw new HotkeyError('UNKNOWN_COMMAND', binding.command);
    const promptId = normalizePromptId(binding.promptId);
    if (!promptCatalog.has(promptId)) throw new HotkeyError('UNKNOWN_PROMPT', promptId);
    return {gesture, command: binding.command, promptId};
  }
}

class ShortcutRegistry {
  constructor({policy, store, promptCatalog, trace}) {
    this.policy = policy;
    this.store = store;
    this.promptCatalog = promptCatalog;
    this.trace = trace;
    this.builtIns = new Map([
      ['`', {gesture: '`', command: 'HOTKEY_HELP_TOGGLE'}],
      ['1', {gesture: '1', command: 'VIEW_ALL'}],
      ['4', {gesture: '4', command: 'VIEW_FAVORITES'}],
      ['5', {gesture: '5', command: 'VIEW_DOCTRINE'}],
      ['f', {gesture: 'f', command: 'FILTER_TOGGLE'}],
      ['[', {gesture: '[', command: 'FILTER_HIDE'}],
      [']', {gesture: ']', command: 'FILTER_SHOW'}],
    ]);
    this.userBindings = new Map();
  }
  effectiveBindings() {
    return new Map([...this.builtIns, ...this.userBindings]);
  }
  configure(binding) {
    const candidate = this.policy.validateBinding(binding, this.effectiveBindings(), this.promptCatalog);
    const next = new Map(this.userBindings);
    next.set(candidate.gesture, candidate);
    try {
      this.store.save([...next.values()]);
    } catch (error) {
      this.trace.push({layer: 'registry', event: 'configure_failed', code: 'PERSISTENCE_FAILED'});
      throw new HotkeyError('PERSISTENCE_FAILED', String(error && error.message || error));
    }
    this.userBindings = next;
    this.trace.push({layer: 'registry', event: 'configured', gesture: candidate.gesture, promptId: candidate.promptId});
    return candidate;
  }
}

class FilterVisibility {
  constructor(trace) {
    this.visible = true;
    this.trace = trace;
  }
  setVisible(visible, command) {
    this.visible = !!visible;
    this.trace.push({layer: 'filter', event: 'visibility_changed', command, visible: this.visible});
    return {visible: this.visible};
  }
  hide() { return this.setVisible(false, 'FILTER_HIDE'); }
  show() { return this.setVisible(true, 'FILTER_SHOW'); }
  toggle() { return this.setVisible(!this.visible, 'FILTER_TOGGLE'); }
}

class HotkeyHelpVisibility {
  constructor(trace) {
    this.open = false;
    this.trace = trace;
  }
  toggle() {
    this.open = !this.open;
    this.trace.push({layer: 'hotkey_help', event: 'visibility_changed', open: this.open});
    return {open: this.open};
  }
}

class ViewNavigatorFake {
  constructor(trace) {
    this.views = [];
    this.trace = trace;
  }
  open(view) {
    this.views.push(view);
    this.trace.push({layer: 'view_navigator', event: 'view_copied', view});
    return {view};
  }
}

class ShortcutDispatcher {
  constructor({registry, filterVisibility, hotkeyHelpVisibility, promptAction, viewNavigator, trace}) {
    this.registry = registry;
    this.filterVisibility = filterVisibility;
    this.hotkeyHelpVisibility = hotkeyHelpVisibility;
    this.promptAction = promptAction;
    this.viewNavigator = viewNavigator;
    this.trace = trace;
    this.buffer = '';
  }
  resetSequence(reason) {
    if (this.buffer) this.trace.push({layer: 'dispatcher', event: 'sequence_reset', reason, buffer: this.buffer});
    this.buffer = '';
  }
  execute(binding) {
    let result;
    if (binding.command === 'HOTKEY_HELP_TOGGLE') result = this.hotkeyHelpVisibility.toggle();
    else if (binding.command === 'FILTER_HIDE') result = this.filterVisibility.hide();
    else if (binding.command === 'FILTER_SHOW') result = this.filterVisibility.show();
    else if (binding.command === 'FILTER_TOGGLE') result = this.filterVisibility.toggle();
    else if (binding.command === 'COPY_PROMPT') result = this.promptAction.copyPrompt(binding.promptId);
    else if (binding.command === 'VIEW_ALL') result = this.viewNavigator.open('all');
    else if (binding.command === 'VIEW_FAVORITES') result = this.viewNavigator.open('favorites');
    else if (binding.command === 'VIEW_DOCTRINE') result = this.viewNavigator.open('doctrine');
    else throw new HotkeyError('UNKNOWN_COMMAND', binding.command);
    this.trace.push({layer: 'dispatcher', event: 'dispatched', command: binding.command, promptId: binding.promptId || null});
    return {handled: true, result};
  }
  consumeBufferedKey(key, bindings) {
    if (!this.buffer || !/^[a-z0-9]$/.test(key)) return null;
    const candidate = this.buffer + key;
    if (bindings.has(candidate)) {
      const binding = bindings.get(candidate);
      this.buffer = '';
      return this.execute(binding);
    }
    const pending = [...bindings.keys()].some(gesture => gesture.length > 1 && gesture.startsWith(candidate));
    if (pending) {
      this.buffer = candidate;
      return {handled: true, pending: true, buffer: this.buffer};
    }
    this.resetSequence('no_match');
    return null;
  }
  handleKey(event = {}) {
    if (event.defaultPrevented || event.altKey || event.metaKey || event.ctrlKey) return {handled: false, reason: 'MODIFIED_OR_PREVENTED'};
    if (isEditableTarget(event.target)) return {handled: false, reason: 'EDITABLE_TARGET'};
    const key = normalizeGesture(event.key);
    if (key === 'escape') {
      this.resetSequence('escape');
      return {handled: false, reason: 'SEQUENCE_CANCELLED'};
    }
    const bindings = this.registry.effectiveBindings();
    const buffered = this.consumeBufferedKey(key, bindings);
    if (buffered) return buffered;
    if (bindings.has(key)) {
      this.resetSequence('direct_command');
      return this.execute(bindings.get(key));
    }
    if (/^[a-z0-9]$/.test(key)) {
      const pending = [...bindings.keys()].some(gesture => gesture.length > 1 && gesture.startsWith(key));
      if (pending) {
        this.buffer = key;
        return {handled: true, pending: true, buffer: this.buffer};
      }
    }
    return {handled: false, reason: 'NO_MATCH'};
  }
}

class MemoryStore {
  constructor(fail = false) { this.fail = fail; this.value = []; this.saveCalls = 0; }
  save(value) {
    this.saveCalls += 1;
    if (this.fail) throw new Error('storage unavailable');
    this.value = JSON.parse(JSON.stringify(value));
  }
}
class PromptActionFake {
  constructor(trace) { this.trace = trace; this.copied = []; }
  copyPrompt(promptId) {
    this.copied.push(promptId);
    this.trace.push({layer: 'navigator', event: 'prompt_copied', promptId});
    return {promptId};
  }
}

function buildProgram({promptIds = ['P95'], store = new MemoryStore()} = {}) {
  const trace = [];
  const policy = new ShortcutPolicy();
  const registry = new ShortcutRegistry({policy, store, promptCatalog: new Set(promptIds), trace});
  const filterVisibility = new FilterVisibility(trace);
  const hotkeyHelpVisibility = new HotkeyHelpVisibility(trace);
  const promptAction = new PromptActionFake(trace);
  const viewNavigator = new ViewNavigatorFake(trace);
  const dispatcher = new ShortcutDispatcher({registry, filterVisibility, hotkeyHelpVisibility, promptAction, viewNavigator, trace});
  return {trace, policy, registry, store, filterVisibility, hotkeyHelpVisibility, promptAction, viewNavigator, dispatcher};
}

function assert(value, message) { if (!value) throw new Error('ASSERTION_FAILED: ' + message); }
function expectCode(code, fn) {
  try { fn(); } catch (error) {
    assert(error instanceof HotkeyError, 'expected HotkeyError');
    assert(error.code === code, `expected ${code}, got ${error.code}`);
    return;
  }
  throw new Error('ASSERTION_FAILED: expected ' + code);
}

function runSelfTest() {
  const program = buildProgram({promptIds: ['P95', 'P14', 'P07']});

  program.dispatcher.handleKey({key: '`'});
  assert(program.hotkeyHelpVisibility.open === true, 'backtick opens Hotkeys');
  program.dispatcher.handleKey({key: '`'});
  assert(program.hotkeyHelpVisibility.open === false, 'backtick closes Hotkeys');
  assert(program.dispatcher.handleKey({key: '`', target: {tagName: 'INPUT'}}).reason === 'EDITABLE_TARGET', 'editable backtick suppression');
  assert(program.dispatcher.handleKey({key: '`', ctrlKey: true}).reason === 'MODIFIED_OR_PREVENTED', 'modified backtick suppression');

  program.dispatcher.handleKey({key: '['});
  assert(program.filterVisibility.visible === false, 'hide');
  program.dispatcher.handleKey({key: ']'});
  assert(program.filterVisibility.visible === true, 'show');
  program.dispatcher.handleKey({key: 'f'});
  assert(program.filterVisibility.visible === false, 'toggle');

  program.registry.configure({gesture: 'p95', command: 'COPY_PROMPT', promptId: 'p95'});
  assert(program.dispatcher.handleKey({key: 'p'}).pending, 'p prefix');
  assert(program.dispatcher.handleKey({key: '9'}).pending, 'p9 prefix');
  assert(program.dispatcher.handleKey({key: '5'}).handled, 'p95 dispatch must beat built-in 5');
  assert(program.promptAction.copied[0] === 'P95', 'P95 target');
  assert(program.viewNavigator.views.length === 0, 'built-in 5 must not steal buffered P95');

  program.registry.configure({gesture: 'p14', command: 'COPY_PROMPT', promptId: 'p14'});
  program.dispatcher.handleKey({key: 'p'});
  program.dispatcher.handleKey({key: '1'});
  assert(program.dispatcher.handleKey({key: '4'}).handled, 'p14 dispatch must beat built-ins 1 and 4');
  assert(program.promptAction.copied[1] === 'P14', 'P14 target');
  assert(program.viewNavigator.views.length === 0, 'built-in digits must not steal buffered P14');
  program.dispatcher.handleKey({key: '5'});
  assert(program.viewNavigator.views[0] === 'doctrine', 'built-in 5 remains active with no sequence buffer');

  const editable = program.dispatcher.handleKey({key: 'p', target: {tagName: 'INPUT'}});
  assert(editable.reason === 'EDITABLE_TARGET', 'editable suppression');
  expectCode('RESERVED_COLLISION', () => program.registry.configure({gesture: '`', command: 'COPY_PROMPT', promptId: 'P95'}));
  expectCode('RESERVED_COLLISION', () => program.registry.configure({gesture: 'f', command: 'COPY_PROMPT', promptId: 'P95'}));
  expectCode('UNKNOWN_PROMPT', () => program.registry.configure({gesture: 'p999', command: 'COPY_PROMPT', promptId: 'P999'}));

  const failing = buildProgram({promptIds: ['P95'], store: new MemoryStore(true)});
  expectCode('PERSISTENCE_FAILED', () => failing.registry.configure({gesture: 'p95', command: 'COPY_PROMPT', promptId: 'P95'}));
  assert(!failing.registry.userBindings.has('p95'), 'failed save must not publish');

  return {
    status: 'PASS',
    success_paths: ['HOTKEY_HELP_TOGGLE', 'FILTER_HIDE', 'FILTER_SHOW', 'FILTER_TOGGLE', 'COPY_PROMPT(P95)', 'COPY_PROMPT(P14)', 'VIEW_DOCTRINE'],
    failure_paths: ['EDITABLE_TARGET', 'MODIFIED_OR_PREVENTED', 'RESERVED_COLLISION', 'UNKNOWN_PROMPT', 'PERSISTENCE_FAILED'],
    trace: program.trace,
  };
}

if (require.main === module) process.stdout.write(JSON.stringify(runSelfTest()));
module.exports = {HotkeyError, ShortcutPolicy, ShortcutRegistry, ShortcutDispatcher, FilterVisibility, HotkeyHelpVisibility, ViewNavigatorFake, MemoryStore, PromptActionFake, buildProgram, runSelfTest};
