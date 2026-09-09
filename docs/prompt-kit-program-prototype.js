'use strict';

class PromptKitProgramError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'PromptKitProgramError';
    this.code = code;
    this.details = details;
  }
}

function assert(value, message) {
  if (!value) throw new Error('ASSERTION_FAILED: ' + message);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function validateCommandResult(result, commandType) {
  if (!result || typeof result !== 'object' || typeof result.status !== 'string' || !result.status.trim()) {
    throw new PromptKitProgramError(
      'INVALID_COMMAND_RESULT',
      `Command ${commandType} returned an invalid CommandResult.`,
      {commandType}
    );
  }
  return result;
}

class PromptCatalog {
  constructor(prompts) {
    this.byId = new Map((prompts || []).map(prompt => [prompt.id, Object.freeze({...prompt})]));
  }
  require(promptId) {
    const prompt = this.byId.get(promptId);
    if (!prompt) throw new PromptKitProgramError('UNKNOWN_PROMPT', `Unknown prompt ${promptId}`, {promptId});
    return prompt;
  }
}

class SessionState {
  constructor(trace) {
    this.trace = trace;
    this.value = {
      view: 'all', searchText: '', category: 'all', section: null, type: null, color: null,
      activePromptId: null, copyTargetPromptId: null, detailPromptId: null,
    };
  }
  revealPrompt(promptId) {
    this.value = {
      ...this.value,
      view: 'all', searchText: '', category: 'all', section: null, type: null, color: null,
      activePromptId: promptId, copyTargetPromptId: promptId,
    };
    this.trace.push({layer: 'session', event: 'prompt_reveal_state', promptId});
    return this.snapshot();
  }
  openDetail(promptId) {
    this.value = {...this.value, activePromptId: promptId, detailPromptId: promptId};
    this.trace.push({layer: 'session', event: 'detail_state_opened', promptId});
    return this.snapshot();
  }
  snapshot() { return clone(this.value); }
}

class MemoryClipboard {
  constructor(trace, {fail = false, defer = false} = {}) {
    this.trace = trace;
    this.fail = fail;
    this.defer = defer;
    this.writes = [];
  }
  async writeText(text) {
    this.trace.push({layer: 'clipboard', event: 'write_attempted'});
    if (this.defer) await Promise.resolve();
    if (this.fail) {
      this.trace.push({layer: 'clipboard', event: 'write_failed'});
      throw new PromptKitProgramError('CLIPBOARD_WRITE_FAILED', 'Clipboard write failed.');
    }
    this.writes.push(text);
    this.trace.push({layer: 'clipboard', event: 'write_succeeded'});
    return {written: true};
  }
}

class MemoryPreferenceStore {
  constructor(trace, {favorites = [], fail = false} = {}) {
    this.trace = trace;
    this.fail = fail;
    this.favorites = [...favorites];
    this.saveCalls = 0;
  }
  loadFavorites() { return [...this.favorites]; }
  saveFavorites(candidate) {
    this.saveCalls += 1;
    this.trace.push({layer: 'preference_store', event: 'save_attempted', favorites: [...candidate]});
    if (this.fail) {
      this.trace.push({layer: 'preference_store', event: 'save_failed'});
      throw new PromptKitProgramError('PREFERENCE_PERSISTENCE_FAILED', 'Favorite persistence failed.');
    }
    this.favorites = [...candidate];
    this.trace.push({layer: 'preference_store', event: 'save_succeeded', favorites: [...candidate]});
  }
}

class FavoritePreferences {
  constructor(trace, store) {
    this.trace = trace;
    this.store = store;
    this.favorites = new Set(store.loadFavorites());
  }
  has(promptId) { return this.favorites.has(promptId); }
  toggle(promptId) {
    const candidate = new Set(this.favorites);
    if (candidate.has(promptId)) candidate.delete(promptId); else candidate.add(promptId);
    this.store.saveFavorites([...candidate].sort());
    this.favorites = candidate;
    const favorite = candidate.has(promptId);
    this.trace.push({layer: 'preferences', event: 'favorite_published', promptId, favorite});
    return {promptId, favorite};
  }
  snapshot() { return [...this.favorites].sort(); }
}

class UsageLedger {
  constructor(trace, {fail = false} = {}) {
    this.trace = trace;
    this.fail = fail;
    this.events = [];
  }
  recordCompletion(event) {
    if (this.fail) {
      this.trace.push({layer: 'usage_ledger', event: 'record_degraded', type: event.type});
      return {recorded: false, degraded: true};
    }
    this.events.push(clone(event));
    this.trace.push({layer: 'usage_ledger', event: 'completion_recorded', type: event.type, promptId: event.promptId || null});
    return {recorded: true, degraded: false};
  }
  reset() {
    this.events = [];
    this.trace.push({layer: 'usage_ledger', event: 'reset'});
  }
}

class PromptSurfaceFake {
  constructor(trace) {
    this.trace = trace;
    this.revealed = [];
    this.focusedCopy = [];
    this.details = [];
    this.favoriteProjection = new Map();
  }
  revealPrompt(promptId) {
    this.revealed.push(promptId);
    this.trace.push({layer: 'surface', event: 'prompt_revealed', promptId});
  }
  focusCopy(promptId) {
    this.focusedCopy.push(promptId);
    this.trace.push({layer: 'surface', event: 'copy_control_focused', promptId});
  }
  openDetail(promptId) {
    this.details.push(promptId);
    this.trace.push({layer: 'surface', event: 'detail_opened', promptId});
  }
  projectFavorite(promptId, favorite) {
    this.favoriteProjection.set(promptId, favorite);
    this.trace.push({layer: 'surface', event: 'favorite_projected', promptId, favorite});
  }
}

class CommandKernel {
  constructor(trace) {
    this.trace = trace;
    this.handlers = new Map();
  }
  register(commandType, handler) {
    if (!commandType || typeof handler !== 'function') {
      throw new PromptKitProgramError('INVALID_COMMAND_REGISTRATION', 'Command registration requires an id and handler.');
    }
    if (this.handlers.has(commandType)) {
      throw new PromptKitProgramError('COMMAND_ALREADY_REGISTERED', commandType);
    }
    this.handlers.set(commandType, handler);
    this.trace.push({layer: 'kernel', event: 'command_registered', commandType});
  }
  async execute(command) {
    if (!command || typeof command.type !== 'string') {
      throw new PromptKitProgramError('INVALID_COMMAND', 'Command requires a string type.');
    }
    const handler = this.handlers.get(command.type);
    if (!handler) throw new PromptKitProgramError('UNKNOWN_COMMAND', command.type);
    this.trace.push({layer: 'kernel', event: 'command_started', commandType: command.type, source: command.source || 'unknown'});
    try {
      const result = validateCommandResult(await handler(command), command.type);
      this.trace.push({layer: 'kernel', event: 'command_completed', commandType: command.type, status: result.status});
      return result;
    } catch (error) {
      const normalized = error instanceof PromptKitProgramError
        ? error
        : new PromptKitProgramError('COMMAND_FAILED', String(error && error.message || error));
      this.trace.push({layer: 'kernel', event: 'command_failed', commandType: command.type, code: normalized.code});
      throw normalized;
    }
  }
}

class HotkeyEntrypoint {
  constructor(kernel) { this.kernel = kernel; }
  copyFavorite(promptId) { return this.kernel.execute({type: 'COPY_REVEAL_PROMPT', promptId, source: 'hotkey'}); }
}

class PromptCardEntrypoint {
  constructor(kernel) { this.kernel = kernel; }
  copy(promptId) { return this.kernel.execute({type: 'COPY_REVEAL_PROMPT', promptId, source: 'card'}); }
  toggleFavorite(promptId) { return this.kernel.execute({type: 'TOGGLE_FAVORITE', promptId, source: 'card'}); }
}

class FinderEntrypoint {
  constructor(kernel) { this.kernel = kernel; }
  inspect(promptId) { return this.kernel.execute({type: 'OPEN_PROMPT_DETAIL', promptId, source: 'finder'}); }
}

function buildCommandKernelProgram({clipboardFail = false, clipboardDefer = false, preferenceFail = false, usageFail = false} = {}) {
  const trace = [];
  const catalog = new PromptCatalog([
    {id: 'P07', name: 'Repo Sprint Executor', copyContent: 'EXECUTE THE REPO SPRINT.'},
    {id: 'P95', name: 'Example Prompt', copyContent: 'EXAMPLE PROMPT CONTENT.'},
  ]);
  const session = new SessionState(trace);
  const clipboard = new MemoryClipboard(trace, {fail: clipboardFail, defer: clipboardDefer});
  const preferenceStore = new MemoryPreferenceStore(trace, {favorites: ['P07'], fail: preferenceFail});
  const preferences = new FavoritePreferences(trace, preferenceStore);
  const usageLedger = new UsageLedger(trace, {fail: usageFail});
  const surface = new PromptSurfaceFake(trace);
  const kernel = new CommandKernel(trace);

  kernel.register('COPY_REVEAL_PROMPT', async command => {
    const prompt = catalog.require(command.promptId);
    session.revealPrompt(prompt.id);
    surface.revealPrompt(prompt.id);
    surface.focusCopy(prompt.id);
    try {
      await clipboard.writeText(prompt.copyContent);
    } catch (error) {
      if (error instanceof PromptKitProgramError && error.code === 'CLIPBOARD_WRITE_FAILED') {
        error.details = {...error.details, promptId: prompt.id, recovery: 'COPY_CONTROL_FOCUSED'};
      }
      throw error;
    }
    const telemetry = usageLedger.recordCompletion({type: 'PROMPT_COPIED', promptId: prompt.id, source: command.source || 'unknown'});
    return {status: 'COPIED', promptId: prompt.id, terminalValue: 'PROMPT_TEXT_ON_CLIPBOARD', reveal: 'COPY_CONTROL_FOCUSED', telemetry};
  });

  kernel.register('OPEN_PROMPT_DETAIL', command => {
    const prompt = catalog.require(command.promptId);
    session.openDetail(prompt.id);
    surface.openDetail(prompt.id);
    return {status: 'DETAIL_OPEN', promptId: prompt.id, terminalValue: 'PROMPT_INSPECTION_READY'};
  });

  kernel.register('TOGGLE_FAVORITE', command => {
    const prompt = catalog.require(command.promptId);
    const persisted = preferences.toggle(prompt.id);
    surface.projectFavorite(prompt.id, persisted.favorite);
    usageLedger.recordCompletion({type: 'FAVORITE_CHANGED', promptId: prompt.id, favorite: persisted.favorite, source: command.source || 'unknown'});
    return {status: 'FAVORITE_CHANGED', ...persisted, terminalValue: 'DURABLE_PREFERENCE_CHANGED'};
  });

  return {
    trace, catalog, session, clipboard, preferenceStore, preferences, usageLedger, surface, kernel,
    hotkeys: new HotkeyEntrypoint(kernel), cards: new PromptCardEntrypoint(kernel), finder: new FinderEntrypoint(kernel),
  };
}

function reducerPlan(state, action, catalog, favorites) {
  if (!action || typeof action.type !== 'string') throw new PromptKitProgramError('INVALID_ACTION', 'Action requires a type.');
  if (action.type === 'COPY_REVEAL_PROMPT') {
    const prompt = catalog.require(action.promptId);
    return {
      nextState: {...state, view: 'all', searchText: '', category: 'all', section: null, type: null, color: null, activePromptId: prompt.id, copyTargetPromptId: prompt.id},
      nextFavorites: [...favorites],
      effects: [
        {phase: 'precommit', critical: true, type: 'CLIPBOARD_WRITE', prompt},
        {phase: 'postcommit', critical: false, type: 'SURFACE_REVEAL', promptId: prompt.id},
        {phase: 'postcommit', critical: false, type: 'SURFACE_FOCUS_COPY', promptId: prompt.id},
        {phase: 'postcommit', critical: false, type: 'USAGE_RECORD', payload: {type: 'PROMPT_COPIED', promptId: prompt.id, source: action.source || 'unknown'}},
      ],
    };
  }
  if (action.type === 'TOGGLE_FAVORITE') {
    const prompt = catalog.require(action.promptId);
    const candidate = new Set(favorites);
    if (candidate.has(prompt.id)) candidate.delete(prompt.id); else candidate.add(prompt.id);
    const nextFavorites = [...candidate].sort();
    return {
      nextState: {...state, activePromptId: prompt.id},
      nextFavorites,
      effects: [
        {phase: 'precommit', critical: true, type: 'PREFERENCE_SAVE', favorites: nextFavorites},
        {phase: 'postcommit', critical: false, type: 'SURFACE_FAVORITE', promptId: prompt.id, favorite: candidate.has(prompt.id)},
        {phase: 'postcommit', critical: false, type: 'USAGE_RECORD', payload: {type: 'FAVORITE_CHANGED', promptId: prompt.id, favorite: candidate.has(prompt.id), source: action.source || 'unknown'}},
      ],
    };
  }
  throw new PromptKitProgramError('UNKNOWN_ACTION', action.type);
}

class ReducerEffectProgram {
  constructor({clipboardFail = false, preferenceFail = false, usageFail = false} = {}) {
    this.trace = [];
    this.catalog = new PromptCatalog([
      {id: 'P07', name: 'Repo Sprint Executor', copyContent: 'EXECUTE THE REPO SPRINT.'},
      {id: 'P95', name: 'Example Prompt', copyContent: 'EXAMPLE PROMPT CONTENT.'},
    ]);
    this.state = new SessionState(this.trace).snapshot();
    this.clipboard = new MemoryClipboard(this.trace, {fail: clipboardFail, defer: true});
    this.preferenceStore = new MemoryPreferenceStore(this.trace, {favorites: ['P07'], fail: preferenceFail});
    this.favorites = this.preferenceStore.loadFavorites();
    this.usageLedger = new UsageLedger(this.trace, {fail: usageFail});
    this.surface = new PromptSurfaceFake(this.trace);
  }
  async runEffect(effect) {
    if (effect.type === 'CLIPBOARD_WRITE') return this.clipboard.writeText(effect.prompt.copyContent);
    if (effect.type === 'PREFERENCE_SAVE') return this.preferenceStore.saveFavorites(effect.favorites);
    if (effect.type === 'SURFACE_REVEAL') return this.surface.revealPrompt(effect.promptId);
    if (effect.type === 'SURFACE_FOCUS_COPY') return this.surface.focusCopy(effect.promptId);
    if (effect.type === 'SURFACE_FAVORITE') return this.surface.projectFavorite(effect.promptId, effect.favorite);
    if (effect.type === 'USAGE_RECORD') return this.usageLedger.recordCompletion(effect.payload);
    throw new PromptKitProgramError('UNKNOWN_EFFECT', effect.type);
  }
  async dispatch(action) {
    this.trace.push({layer: 'reducer_program', event: 'dispatch_started', actionType: action.type});
    const plan = reducerPlan(this.state, action, this.catalog, this.favorites);
    for (const effect of plan.effects.filter(item => item.phase === 'precommit')) {
      try { await this.runEffect(effect); }
      catch (error) {
        this.trace.push({layer: 'reducer_program', event: 'precommit_failed', effect: effect.type});
        throw error;
      }
    }
    this.state = clone(plan.nextState);
    this.favorites = [...plan.nextFavorites];
    this.trace.push({layer: 'reducer_program', event: 'state_committed', actionType: action.type});
    for (const effect of plan.effects.filter(item => item.phase === 'postcommit')) {
      try { await this.runEffect(effect); }
      catch (error) {
        if (effect.critical) throw error;
        this.trace.push({layer: 'reducer_program', event: 'postcommit_degraded', effect: effect.type});
      }
    }
    return {status: 'COMPLETED', state: clone(this.state), favorites: [...this.favorites], effectCount: plan.effects.length};
  }
}

async function expectCode(expected, fn) {
  try { await fn(); }
  catch (error) {
    assert(error instanceof PromptKitProgramError, `expected PromptKitProgramError for ${expected}`);
    assert(error.code === expected, `expected ${expected}, observed ${error.code}`);
    return error;
  }
  throw new Error(`ASSERTION_FAILED: expected ${expected}`);
}

function expectSyncCode(expected, fn) {
  try { fn(); }
  catch (error) {
    assert(error instanceof PromptKitProgramError, `expected PromptKitProgramError for ${expected}`);
    assert(error.code === expected, `expected ${expected}, observed ${error.code}`);
    return error;
  }
  throw new Error(`ASSERTION_FAILED: expected ${expected}`);
}

async function runSelfTest() {
  const kernelProgram = buildCommandKernelProgram({clipboardDefer: true});

  const pendingCopy = kernelProgram.hotkeys.copyFavorite('P07');
  assert(kernelProgram.usageLedger.events.length === 0, 'completion telemetry is absent while async clipboard write is pending');
  const hotkeyResult = await pendingCopy;
  assert(hotkeyResult.status === 'COPIED', 'hotkey copy reaches terminal clipboard value');
  assert(kernelProgram.clipboard.writes[0] === 'EXECUTE THE REPO SPRINT.', 'canonical prompt text is copied');
  assert(kernelProgram.surface.revealed[0] === 'P07', 'copy journey reveals prompt');
  assert(kernelProgram.surface.focusedCopy[0] === 'P07', 'copy journey focuses copy control');
  assert(kernelProgram.usageLedger.events.length === 1, 'copy completion records exactly one semantic event after awaited clipboard success');

  const cardResult = await kernelProgram.cards.copy('P95');
  assert(cardResult.status === 'COPIED', 'card copy uses same command kernel');
  assert(kernelProgram.usageLedger.events.filter(event => event.type === 'PROMPT_COPIED').length === 2, 'entrypoints do not create duplicate usage owners');

  const detailResult = await kernelProgram.finder.inspect('P95');
  assert(detailResult.status === 'DETAIL_OPEN', 'finder inspection has an explicit inspection terminal value');
  assert(kernelProgram.usageLedger.events.filter(event => event.type === 'PROMPT_COPIED').length === 2, 'inspection is not counted as copy completion');

  const favoriteResult = await kernelProgram.cards.toggleFavorite('P95');
  assert(favoriteResult.favorite === true, 'favorite is published after durable save');
  assert(kernelProgram.preferenceStore.favorites.includes('P95'), 'favorite store received durable candidate');

  const clipboardFailure = buildCommandKernelProgram({clipboardFail: true, clipboardDefer: true});
  const clipboardError = await expectCode('CLIPBOARD_WRITE_FAILED', () => clipboardFailure.hotkeys.copyFavorite('P07'));
  assert(clipboardError.details.recovery === 'COPY_CONTROL_FOCUSED', 'clipboard failure preserves an actionable recovery target');
  assert(clipboardFailure.usageLedger.events.length === 0, 'rejected async clipboard write does not create completion telemetry');
  assert(clipboardFailure.surface.focusedCopy[0] === 'P07', 'failed copy leaves copy control ready for retry');

  const persistenceFailure = buildCommandKernelProgram({preferenceFail: true});
  await expectCode('PREFERENCE_PERSISTENCE_FAILED', () => persistenceFailure.cards.toggleFavorite('P95'));
  assert(!persistenceFailure.preferences.has('P95'), 'failed durable favorite write does not publish new preference state');
  assert(!persistenceFailure.surface.favoriteProjection.has('P95'), 'failed durable favorite write does not project false UI success');

  const telemetryDegraded = buildCommandKernelProgram({usageFail: true});
  const degradedCopy = await telemetryDegraded.hotkeys.copyFavorite('P07');
  assert(degradedCopy.status === 'COPIED' && degradedCopy.telemetry.degraded === true, 'telemetry degradation cannot negate successful clipboard value');

  await expectCode('UNKNOWN_PROMPT', () => kernelProgram.hotkeys.copyFavorite('P999'));
  await expectCode('UNKNOWN_COMMAND', () => kernelProgram.kernel.execute({type: 'NOT_A_COMMAND'}));
  expectSyncCode('COMMAND_ALREADY_REGISTERED', () => kernelProgram.kernel.register('COPY_REVEAL_PROMPT', () => ({})));

  const invalidResultKernel = new CommandKernel([]);
  invalidResultKernel.register('BAD_RESULT', async () => undefined);
  await expectCode('INVALID_COMMAND_RESULT', () => invalidResultKernel.execute({type: 'BAD_RESULT'}));

  const reducerProgram = new ReducerEffectProgram();
  const reducerCopy = await reducerProgram.dispatch({type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'hotkey'});
  assert(reducerCopy.state.copyTargetPromptId === 'P07', 'reducer candidate reaches equivalent copy target state');
  assert(reducerProgram.clipboard.writes.length === 1, 'reducer candidate reaches awaited clipboard side effect');
  assert(reducerCopy.effectCount === 4, 'reducer candidate requires explicit effect choreography');

  const reducerPersistenceFailure = new ReducerEffectProgram({preferenceFail: true});
  await expectCode('PREFERENCE_PERSISTENCE_FAILED', () => reducerPersistenceFailure.dispatch({type: 'TOGGLE_FAVORITE', promptId: 'P95', source: 'card'}));
  assert(!reducerPersistenceFailure.favorites.includes('P95'), 'reducer transaction does not commit state after failed persistence');

  return {
    status: 'PASS',
    selectedDesign: 'COMMAND_KERNEL_WITH_OWNED_STATE_AND_PORTS',
    journeys: {
      asyncCopySuccess: 'PASS', asyncCopyRejection: 'PASS', favoriteSuccess: 'PASS',
      favoritePersistenceFailure: 'PASS', inspectionDoesNotCountAsCopy: 'PASS',
      telemetryDegradation: 'PASS', extensionCollision: 'PASS', invalidCommandResult: 'PASS',
      reducerComparison: 'PASS',
    },
    comparison: {
      commandKernel: {
        publicExecutionSeam: 'await execute(command) -> CommandResult',
        terminalActionOwnership: 'command handler',
        stateOwnership: 'separate session/preferences owners',
        effectOrdering: 'local to the command that needs it',
      },
      reducerEffect: {
        publicExecutionSeam: 'await dispatch(action)',
        terminalActionOwnership: 'reducer plan + effect runner',
        stateOwnership: 'central pending state plus external stores',
        effectOrdering: 'precommit/postcommit effect protocol required',
      },
      decision: 'Prompt Kit is command-heavy and side-effect-order-sensitive; keep an async command kernel and deep state owners rather than introducing a global reducer/effect runtime.',
    },
    kernelTrace: kernelProgram.trace,
    reducerTrace: reducerProgram.trace,
  };
}

if (require.main === module) {
  runSelfTest()
    .then(result => process.stdout.write(JSON.stringify(result, null, 2) + '\n'))
    .catch(error => {
      process.stderr.write(`${error && error.stack || error}\n`);
      process.exitCode = 1;
    });
}

module.exports = {
  PromptKitProgramError, validateCommandResult, PromptCatalog, SessionState, MemoryClipboard,
  MemoryPreferenceStore, FavoritePreferences, UsageLedger, PromptSurfaceFake, CommandKernel,
  HotkeyEntrypoint, PromptCardEntrypoint, FinderEntrypoint, buildCommandKernelProgram,
  reducerPlan, ReducerEffectProgram, runSelfTest,
};
