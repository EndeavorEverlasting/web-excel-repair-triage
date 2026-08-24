'use strict';

const {
  PromptKitProgramError,
  PromptCatalog,
  SessionState,
  MemoryClipboard,
  UsageLedger,
  CommandKernel,
} = require('./prompt-kit-program-prototype.js');

const VALID_MODALITIES = new Set(['pointer', 'keyboard']);

function assert(value, message) {
  if (!value) throw new Error('ASSERTION_FAILED: ' + message);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function validateInteractionContext(context) {
  if (!context || typeof context !== 'object') {
    throw new PromptKitProgramError('INVALID_INTERACTION_CONTEXT', 'InteractionContext is required.');
  }
  if (typeof context.source !== 'string' || !context.source.trim()) {
    throw new PromptKitProgramError('INVALID_INTERACTION_CONTEXT', 'InteractionContext requires a source.');
  }
  if (!VALID_MODALITIES.has(context.modality)) {
    throw new PromptKitProgramError(
      'INVALID_INTERACTION_MODALITY',
      `Unsupported interaction modality: ${String(context.modality)}`,
      {modality: context.modality}
    );
  }
  if (typeof context.profileId !== 'string' || !context.profileId.trim()) {
    throw new PromptKitProgramError('INVALID_INTERACTION_CONTEXT', 'InteractionContext requires a profileId.');
  }
  return Object.freeze({
    source: context.source,
    modality: context.modality,
    profileId: context.profileId,
  });
}

class ProfileCatalog {
  constructor(profiles) {
    const rows = Array.isArray(profiles) ? profiles : [];
    const ids = new Set();
    const normalized = [];
    for (const raw of rows) {
      if (!raw || typeof raw.id !== 'string' || !raw.id.trim() || typeof raw.name !== 'string' || !raw.name.trim()) {
        throw new PromptKitProgramError('INVALID_PROFILE_CATALOG', 'PromptProfile requires non-empty id and name.');
      }
      if (ids.has(raw.id)) {
        throw new PromptKitProgramError('INVALID_PROFILE_CATALOG', `Duplicate PromptProfile id: ${raw.id}`);
      }
      ids.add(raw.id);
      normalized.push(Object.freeze({id: raw.id, name: raw.name, isDefault: raw.isDefault === true}));
    }
    const defaults = normalized.filter(profile => profile.isDefault);
    if (normalized.length < 1 || defaults.length !== 1) {
      throw new PromptKitProgramError('INVALID_PROFILE_CATALOG', 'ProfileCatalog requires exactly one default profile.');
    }
    this.profiles = Object.freeze(normalized);
    this.byId = new Map(this.profiles.map(profile => [profile.id, profile]));
    this.defaultId = defaults[0].id;
  }
  require(profileId) {
    const profile = this.byId.get(profileId);
    if (!profile) {
      throw new PromptKitProgramError('UNKNOWN_PROFILE', `Unknown PromptProfile ${profileId}`, {profileId});
    }
    return profile;
  }
  defaultProfile() {
    return this.require(this.defaultId);
  }
  needsSwitcher() {
    return this.profiles.length > 1;
  }
  list() {
    return this.profiles.map(profile => ({...profile}));
  }
}

class ActiveProfile {
  constructor(trace, profileCatalog) {
    this.trace = trace;
    this.profileCatalog = profileCatalog;
    this.profileId = profileCatalog.defaultProfile().id;
  }
  current() {
    return this.profileId;
  }
  activate(profileId) {
    const target = this.profileCatalog.require(profileId);
    const previousProfileId = this.profileId;
    this.profileId = target.id;
    this.trace.push({
      layer: 'active_profile',
      event: 'profile_activated',
      previousProfileId,
      profileId: target.id,
    });
    return target;
  }
}

class InteractionContextFactory {
  constructor(trace, profileCatalog, activeProfile) {
    this.trace = trace;
    this.profileCatalog = profileCatalog;
    this.activeProfile = activeProfile;
  }
  create(source, modality) {
    const profileId = this.activeProfile.current();
    this.profileCatalog.require(profileId);
    const context = validateInteractionContext({source, modality, profileId});
    this.trace.push({
      layer: 'interaction_context',
      event: 'context_created',
      source: context.source,
      modality: context.modality,
      profileId: context.profileId,
    });
    return context;
  }
}

class MemoryProfilePreferenceStore {
  constructor(trace, {
    legacyFavorites = ['P07'],
    profileFavorites = {work: ['P95']},
    failProfileIds = [],
  } = {}) {
    this.trace = trace;
    this.legacyFavorites = [...legacyFavorites].sort();
    this.profileFavorites = Object.fromEntries(
      Object.entries(profileFavorites || {}).map(([profileId, favorites]) => [profileId, [...favorites].sort()])
    );
    this.failProfileIds = new Set(failProfileIds);
    this.saveCalls = [];
  }
  storageSlot(profileId) {
    return profileId === 'default' ? 'legacy-default-slot' : `named-profile:${profileId}`;
  }
  loadFavorites(profileId) {
    const favorites = profileId === 'default'
      ? this.legacyFavorites
      : (this.profileFavorites[profileId] || []);
    this.trace.push({
      layer: 'profile_preference_store',
      event: 'favorites_loaded',
      profileId,
      storageSlot: this.storageSlot(profileId),
    });
    return [...favorites];
  }
  saveFavorites(profileId, candidate) {
    const next = [...candidate].sort();
    const storageSlot = this.storageSlot(profileId);
    this.saveCalls.push({profileId, favorites: [...next], storageSlot});
    this.trace.push({
      layer: 'profile_preference_store',
      event: 'save_attempted',
      profileId,
      storageSlot,
      favorites: [...next],
    });
    if (this.failProfileIds.has(profileId)) {
      this.trace.push({
        layer: 'profile_preference_store',
        event: 'save_failed',
        profileId,
        storageSlot,
      });
      throw new PromptKitProgramError(
        'PROFILE_PREFERENCE_PERSISTENCE_FAILED',
        `Favorite persistence failed for PromptProfile ${profileId}.`,
        {profileId}
      );
    }
    if (profileId === 'default') {
      this.legacyFavorites = [...next];
    } else {
      this.profileFavorites[profileId] = [...next];
    }
    this.trace.push({
      layer: 'profile_preference_store',
      event: 'save_succeeded',
      profileId,
      storageSlot,
      favorites: [...next],
    });
  }
}

class ProfiledFavoritePreferences {
  constructor(trace, store) {
    this.trace = trace;
    this.store = store;
  }
  snapshot(profileId) {
    return this.store.loadFavorites(profileId).sort();
  }
  has(profileId, promptId) {
    return this.snapshot(profileId).includes(promptId);
  }
  toggle(profileId, promptId) {
    const current = new Set(this.store.loadFavorites(profileId));
    const candidate = new Set(current);
    if (candidate.has(promptId)) candidate.delete(promptId); else candidate.add(promptId);
    const next = [...candidate].sort();
    this.store.saveFavorites(profileId, next);
    const favorite = candidate.has(promptId);
    this.trace.push({
      layer: 'profiled_favorites',
      event: 'favorite_published',
      profileId,
      promptId,
      favorite,
    });
    return {profileId, promptId, favorite, favorites: next};
  }
}

class CopyPresentationPolicy {
  plan(context) {
    const interaction = validateInteractionContext(context);
    const keyboardShortcutRecovery = interaction.modality === 'keyboard'
      && interaction.source === 'favorite-shortcut';
    if (keyboardShortcutRecovery) {
      return Object.freeze({
        reveal: true,
        focusCopy: true,
        preserveOriginFocus: false,
        reason: 'KEYBOARD_SHORTCUT_RECOVERY',
      });
    }
    return Object.freeze({
      reveal: false,
      focusCopy: false,
      preserveOriginFocus: true,
      reason: 'VISIBLE_CONTROL_ALREADY_TARGETED',
    });
  }
}

class ModalityAwarePromptSurface {
  constructor(trace) {
    this.trace = trace;
    this.revealed = [];
    this.focusedCopy = [];
    this.preservedOrigins = [];
    this.favoriteProjection = new Map();
    this.profileProjection = [];
  }
  applyCopyPlan(promptId, context, plan) {
    if (plan.reveal) {
      this.revealed.push(promptId);
      this.trace.push({layer: 'surface', event: 'prompt_revealed', promptId, source: context.source});
    }
    if (plan.focusCopy) {
      this.focusedCopy.push(promptId);
      this.trace.push({layer: 'surface', event: 'copy_control_focused', promptId, source: context.source});
    } else if (plan.preserveOriginFocus) {
      this.preservedOrigins.push({promptId, source: context.source, modality: context.modality});
      this.trace.push({
        layer: 'surface',
        event: 'origin_focus_preserved',
        promptId,
        source: context.source,
        modality: context.modality,
      });
    }
  }
  projectFavorite(profileId, promptId, favorite) {
    this.favoriteProjection.set(`${profileId}:${promptId}`, favorite);
    this.trace.push({
      layer: 'surface',
      event: 'favorite_projected',
      profileId,
      promptId,
      favorite,
    });
  }
  projectProfile(profile) {
    this.profileProjection.push(profile.id);
    this.trace.push({
      layer: 'surface',
      event: 'active_profile_projected',
      profileId: profile.id,
    });
  }
}

class InteractionCommandGateway {
  constructor(trace, kernel, contexts) {
    this.trace = trace;
    this.kernel = kernel;
    this.contexts = contexts;
  }
  execute(command, source, modality) {
    const context = this.contexts.create(source, modality);
    this.trace.push({
      layer: 'interaction_gateway',
      event: 'command_submitted',
      commandType: command.type,
      source: context.source,
      modality: context.modality,
      profileId: context.profileId,
    });
    return this.kernel.execute({...command, source: context.source, context});
  }
}

class PromptControlEntrypoint {
  constructor(gateway) {
    this.gateway = gateway;
  }
  copy(promptId, modality) {
    return this.gateway.execute({type: 'COPY_REVEAL_PROMPT', promptId}, 'prompt-control', modality);
  }
  toggleFavorite(promptId, modality) {
    return this.gateway.execute({type: 'TOGGLE_FAVORITE', promptId}, 'prompt-control', modality);
  }
}

class FavoriteShortcutEntrypoint {
  constructor(gateway) {
    this.gateway = gateway;
  }
  copy(promptId) {
    return this.gateway.execute({type: 'COPY_REVEAL_PROMPT', promptId}, 'favorite-shortcut', 'keyboard');
  }
}

class ProfileSwitcherEntrypoint {
  constructor(gateway) {
    this.gateway = gateway;
  }
  activate(profileId, modality) {
    return this.gateway.execute({type: 'ACTIVATE_PROFILE', targetProfileId: profileId}, 'profile-switcher', modality);
  }
}

function buildProfileModalityProgram({
  profiles = [
    {id: 'default', name: 'Default', isDefault: true},
    {id: 'work', name: 'Work', isDefault: false},
  ],
  legacyFavorites = ['P07'],
  profileFavorites = {work: ['P95']},
  failProfileIds = [],
  clipboardFail = false,
  clipboardDefer = false,
  usageFail = false,
} = {}) {
  const trace = [];
  const promptCatalog = new PromptCatalog([
    {id: 'P07', name: 'Repo Sprint Executor', copyContent: 'EXECUTE THE REPO SPRINT.'},
    {id: 'P95', name: 'Example Prompt', copyContent: 'EXAMPLE PROMPT CONTENT.'},
  ]);
  const profileCatalog = new ProfileCatalog(profiles);
  const activeProfile = new ActiveProfile(trace, profileCatalog);
  const contexts = new InteractionContextFactory(trace, profileCatalog, activeProfile);
  const session = new SessionState(trace);
  const preferenceStore = new MemoryProfilePreferenceStore(trace, {
    legacyFavorites,
    profileFavorites,
    failProfileIds,
  });
  const favorites = new ProfiledFavoritePreferences(trace, preferenceStore);
  const clipboard = new MemoryClipboard(trace, {fail: clipboardFail, defer: clipboardDefer});
  const usageLedger = new UsageLedger(trace, {fail: usageFail});
  const presentationPolicy = new CopyPresentationPolicy();
  const surface = new ModalityAwarePromptSurface(trace);
  const kernel = new CommandKernel(trace);

  kernel.register('COPY_REVEAL_PROMPT', async command => {
    const context = validateInteractionContext(command.context);
    profileCatalog.require(context.profileId);
    const prompt = promptCatalog.require(command.promptId);
    const presentation = presentationPolicy.plan(context);
    if (presentation.reveal) session.revealPrompt(prompt.id);
    surface.applyCopyPlan(prompt.id, context, presentation);
    try {
      await clipboard.writeText(prompt.copyContent);
    } catch (error) {
      if (error instanceof PromptKitProgramError && error.code === 'CLIPBOARD_WRITE_FAILED') {
        error.details = {
          ...error.details,
          promptId: prompt.id,
          profileId: context.profileId,
          recovery: presentation.focusCopy ? 'COPY_CONTROL_FOCUSED' : 'VISIBLE_COPY_CONTROL',
        };
      }
      throw error;
    }
    const telemetry = usageLedger.recordCompletion({
      type: 'PROMPT_COPIED',
      promptId: prompt.id,
      profileId: context.profileId,
      source: context.source,
      modality: context.modality,
    });
    return {
      status: 'COPIED',
      promptId: prompt.id,
      profileId: context.profileId,
      modality: context.modality,
      terminalValue: 'PROMPT_TEXT_ON_CLIPBOARD',
      presentation,
      telemetry,
    };
  });

  kernel.register('TOGGLE_FAVORITE', command => {
    const context = validateInteractionContext(command.context);
    profileCatalog.require(context.profileId);
    const prompt = promptCatalog.require(command.promptId);
    const persisted = favorites.toggle(context.profileId, prompt.id);
    surface.projectFavorite(context.profileId, prompt.id, persisted.favorite);
    const telemetry = usageLedger.recordCompletion({
      type: 'FAVORITE_CHANGED',
      promptId: prompt.id,
      profileId: context.profileId,
      favorite: persisted.favorite,
      source: context.source,
      modality: context.modality,
    });
    return {
      status: 'FAVORITE_CHANGED',
      ...persisted,
      terminalValue: 'PROFILE_SCOPED_PREFERENCE_CHANGED',
      telemetry,
    };
  });

  kernel.register('ACTIVATE_PROFILE', command => {
    validateInteractionContext(command.context);
    const target = profileCatalog.require(command.targetProfileId);
    activeProfile.activate(target.id);
    surface.projectProfile(target);
    return {
      status: 'PROFILE_ACTIVE',
      profileId: target.id,
      terminalValue: 'ACTIVE_PROFILE_CHANGED',
    };
  });

  const gateway = new InteractionCommandGateway(trace, kernel, contexts);
  return {
    trace,
    promptCatalog,
    profileCatalog,
    activeProfile,
    contexts,
    session,
    preferenceStore,
    favorites,
    clipboard,
    usageLedger,
    presentationPolicy,
    surface,
    kernel,
    gateway,
    controls: new PromptControlEntrypoint(gateway),
    favoriteShortcut: new FavoriteShortcutEntrypoint(gateway),
    profileSwitcher: new ProfileSwitcherEntrypoint(gateway),
  };
}

async function expectCode(expected, fn) {
  try {
    await fn();
  } catch (error) {
    assert(error instanceof PromptKitProgramError, `expected PromptKitProgramError for ${expected}`);
    assert(error.code === expected, `expected ${expected}, observed ${error.code}`);
    return error;
  }
  throw new Error(`ASSERTION_FAILED: expected ${expected}`);
}

async function runSelfTest() {
  const singleProfile = buildProfileModalityProgram({
    profiles: [{id: 'default', name: 'Default', isDefault: true}],
    profileFavorites: {},
  });
  assert(singleProfile.profileCatalog.needsSwitcher() === false, 'single-profile user needs no profile switcher');

  const pointerCopy = await singleProfile.controls.copy('P07', 'pointer');
  assert(pointerCopy.status === 'COPIED', 'pointer control reaches terminal clipboard value');
  assert(pointerCopy.profileId === 'default', 'single-profile pointer command uses implicit default profile');
  assert(pointerCopy.presentation.preserveOriginFocus === true, 'pointer control does not receive keyboard-only focus movement');
  assert(singleProfile.surface.focusedCopy.length === 0, 'pointer control path does not force Copy focus');

  const keyboardControlCopy = await singleProfile.controls.copy('P95', 'keyboard');
  assert(keyboardControlCopy.status === 'COPIED', 'keyboard activation of visible control reaches same terminal command');
  assert(keyboardControlCopy.presentation.preserveOriginFocus === true, 'already-focused keyboard control does not receive redundant focus movement');
  assert(singleProfile.clipboard.writes.length === 2, 'pointer and keyboard visible controls share clipboard owner');

  const defaultFavorite = await singleProfile.controls.toggleFavorite('P95', 'pointer');
  assert(defaultFavorite.favorite === true, 'default profile Favorite mutation succeeds');
  assert(singleProfile.preferenceStore.legacyFavorites.includes('P95'), 'default profile writes through legacy compatibility slot');
  assert(!Object.prototype.hasOwnProperty.call(singleProfile.preferenceStore.profileFavorites, 'default'), 'default profile does not invent a named-profile storage slot');

  const multiProfile = buildProfileModalityProgram({clipboardDefer: true});
  assert(multiProfile.profileCatalog.needsSwitcher() === true, 'multi-profile user exposes profile-switch capability');

  const shortcutResult = await multiProfile.favoriteShortcut.copy('P07');
  assert(shortcutResult.status === 'COPIED', 'configured keyboard shortcut reaches terminal clipboard value');
  assert(shortcutResult.presentation.reveal === true, 'keyboard shortcut reveals target prompt');
  assert(shortcutResult.presentation.focusCopy === true, 'keyboard shortcut focuses Copy recovery target');
  assert(multiProfile.surface.revealed[0] === 'P07', 'shortcut surface reveal is projected');
  assert(multiProfile.surface.focusedCopy[0] === 'P07', 'shortcut Copy focus is projected');

  const sessionBeforeSwitch = multiProfile.session.snapshot();
  const pointerSwitch = await multiProfile.profileSwitcher.activate('work', 'pointer');
  assert(pointerSwitch.status === 'PROFILE_ACTIVE' && multiProfile.activeProfile.current() === 'work', 'pointer profile activation succeeds');
  assert(JSON.stringify(multiProfile.session.snapshot()) === JSON.stringify(sessionBeforeSwitch), 'profile activation does not reset transient browsing state');

  const workFavoriteBefore = multiProfile.favorites.snapshot('work');
  assert(workFavoriteBefore.length === 1 && workFavoriteBefore[0] === 'P95', 'work profile starts with isolated Favorite state');
  const workFavorite = await multiProfile.controls.toggleFavorite('P07', 'pointer');
  assert(workFavorite.favorite === true && workFavorite.profileId === 'work', 'Favorite mutation is scoped to active work profile');
  assert(multiProfile.favorites.snapshot('work').join(',') === 'P07,P95', 'work Favorite candidate is published');
  assert(multiProfile.favorites.snapshot('default').join(',') === 'P07', 'default Favorite state is unchanged by work mutation');

  const keyboardSwitch = await multiProfile.profileSwitcher.activate('default', 'keyboard');
  assert(keyboardSwitch.status === 'PROFILE_ACTIVE' && multiProfile.activeProfile.current() === 'default', 'keyboard profile activation reaches same semantic command');

  const invalidProfile = buildProfileModalityProgram();
  const invalidStart = invalidProfile.activeProfile.current();
  await expectCode('UNKNOWN_PROFILE', () => invalidProfile.profileSwitcher.activate('missing', 'keyboard'));
  assert(invalidProfile.activeProfile.current() === invalidStart, 'unknown profile cannot replace active profile');

  const invalidModality = buildProfileModalityProgram();
  await expectCode('INVALID_INTERACTION_MODALITY', () => invalidModality.controls.copy('P07', 'voice'));
  assert(!invalidModality.trace.some(event => event.layer === 'kernel' && event.event === 'command_started'), 'invalid modality is rejected before kernel side effects');

  const failedProfileStore = buildProfileModalityProgram({failProfileIds: ['work']});
  await failedProfileStore.profileSwitcher.activate('work', 'pointer');
  const failedDefaultBefore = failedProfileStore.favorites.snapshot('default');
  const failedWorkBefore = failedProfileStore.favorites.snapshot('work');
  await expectCode('PROFILE_PREFERENCE_PERSISTENCE_FAILED', () => failedProfileStore.controls.toggleFavorite('P07', 'keyboard'));
  assert(JSON.stringify(failedProfileStore.favorites.snapshot('work')) === JSON.stringify(failedWorkBefore), 'failed work persistence leaves work state unchanged');
  assert(JSON.stringify(failedProfileStore.favorites.snapshot('default')) === JSON.stringify(failedDefaultBefore), 'failed work persistence leaves default state unchanged');
  assert(!failedProfileStore.surface.favoriteProjection.has('work:P07'), 'failed profile persistence does not project false Favorite success');

  const inFlight = buildProfileModalityProgram({clipboardDefer: true});
  const pendingDefaultCopy = inFlight.favoriteShortcut.copy('P07');
  await inFlight.profileSwitcher.activate('work', 'pointer');
  const completedDefaultCopy = await pendingDefaultCopy;
  assert(inFlight.activeProfile.current() === 'work', 'profile switch can complete while prior command is in flight');
  assert(completedDefaultCopy.profileId === 'default', 'in-flight command retains initiating profile snapshot');
  const copiedEvents = inFlight.usageLedger.events.filter(event => event.type === 'PROMPT_COPIED');
  assert(copiedEvents.length === 1 && copiedEvents[0].profileId === 'default', 'semantic completion attribution uses initiating profile, not later active profile');

  return {
    status: 'PASS',
    selectedExtension: 'INTERACTION_CONTEXT_WITH_PROFILE_SCOPED_PREFERENCES',
    archetypeSupport: {
      mousePointerOnly: 'PASS',
      keyboardOnly: 'PASS',
      singleProfile: 'PASS',
      multiProfile: 'PASS',
    },
    journeys: {
      pointerVisibleControlCopy: 'PASS',
      keyboardVisibleControlCopy: 'PASS',
      keyboardShortcutRevealFocus: 'PASS',
      defaultProfileLegacyCompatibility: 'PASS',
      pointerProfileActivation: 'PASS',
      keyboardProfileActivation: 'PASS',
      profileFavoriteIsolation: 'PASS',
      unknownProfileFailure: 'PASS',
      invalidModalityBoundary: 'PASS',
      profilePersistenceFailureIsolation: 'PASS',
      inFlightProfileSnapshot: 'PASS',
    },
    statePolicy: {
      interactionModality: 'invocation-only; never global mutable mode',
      promptCatalog: 'shared across profiles',
      sessionState: 'shared transient state; profile switch does not reset it',
      durablePreferences: 'semantic owners remain Favorites/ShortcutRegistry; persistence namespace is profile-scoped',
      defaultProfile: 'delegates to legacy preference storage seam',
    },
    implementationBoundary: 'prototype only; broad docs/prompt-kit*.js wiring intentionally deferred',
    traces: {
      singleProfile: singleProfile.trace,
      multiProfile: multiProfile.trace,
      persistenceFailure: failedProfileStore.trace,
      inFlightSwitch: inFlight.trace,
    },
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
  VALID_MODALITIES,
  validateInteractionContext,
  ProfileCatalog,
  ActiveProfile,
  InteractionContextFactory,
  MemoryProfilePreferenceStore,
  ProfiledFavoritePreferences,
  CopyPresentationPolicy,
  ModalityAwarePromptSurface,
  InteractionCommandGateway,
  PromptControlEntrypoint,
  FavoriteShortcutEntrypoint,
  ProfileSwitcherEntrypoint,
  buildProfileModalityProgram,
  runSelfTest,
};
