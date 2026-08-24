'use strict';

const {
  PromptKitProgramError,
  PromptCatalog,
  SessionState,
  MemoryClipboard,
  FavoritePreferences,
  UsageLedger,
  CommandKernel,
} = require('./prompt-kit-program-prototype.js');

const {
  HotkeyError,
  ShortcutPolicy,
  ShortcutRegistry,
  ShortcutDispatcher,
  FilterVisibility,
  HotkeyHelpVisibility,
  ViewNavigatorFake,
  PromptNavigatorFake,
} = require('./prompt-kit-hotkey-prototype.js');

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
    defaultProfileId = 'default',
  } = {}) {
    this.trace = trace;
    if (typeof defaultProfileId !== 'string' || !defaultProfileId.trim()) {
      throw new PromptKitProgramError('INVALID_DEFAULT_PROFILE_ID', 'Profile preference storage requires the catalog default profile id.');
    }
    this.defaultProfileId = defaultProfileId;
    this.legacyFavorites = [...legacyFavorites].sort();
    this.profileFavorites = Object.fromEntries(
      Object.entries(profileFavorites || {}).map(([profileId, favorites]) => [profileId, [...favorites].sort()])
    );
    this.failProfileIds = new Set(failProfileIds);
    this.saveCalls = [];
  }
  storageSlot(profileId) {
    return profileId === this.defaultProfileId ? 'legacy-default-slot' : `named-profile:${profileId}`;
  }
  loadFavorites(profileId) {
    const favorites = profileId === this.defaultProfileId
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
    });
    if (this.failProfileIds.has(profileId)) {
      this.trace.push({layer: 'profile_preference_store', event: 'save_failed', profileId, storageSlot});
      throw new PromptKitProgramError(
        'PROFILE_PREFERENCE_PERSISTENCE_FAILED',
        `Favorite persistence failed for PromptProfile ${profileId}.`,
        {profileId}
      );
    }
    if (profileId === this.defaultProfileId) this.legacyFavorites = [...next];
    else this.profileFavorites[profileId] = [...next];
    this.trace.push({layer: 'profile_preference_store', event: 'save_succeeded', profileId, storageSlot});
  }
}

class BoundProfileFavoriteStore {
  constructor(rootStore, profileId) {
    this.rootStore = rootStore;
    this.profileId = profileId;
  }
  loadFavorites() {
    return this.rootStore.loadFavorites(this.profileId);
  }
  saveFavorites(candidate) {
    return this.rootStore.saveFavorites(this.profileId, candidate);
  }
}

class FavoritePreferenceContexts {
  constructor(trace, rootStore) {
    this.trace = trace;
    this.rootStore = rootStore;
    this.contexts = new Map();
  }
  forProfile(profileId) {
    if (!this.contexts.has(profileId)) {
      const boundStore = new BoundProfileFavoriteStore(this.rootStore, profileId);
      this.contexts.set(profileId, new FavoritePreferences(this.trace, boundStore));
      this.trace.push({layer: 'favorite_contexts', event: 'canonical_owner_bound', profileId});
    }
    return this.contexts.get(profileId);
  }
  snapshot(profileId) {
    return this.forProfile(profileId).snapshot();
  }
  has(profileId, promptId) {
    return this.forProfile(profileId).has(promptId);
  }
  toggle(profileId, promptId) {
    const owner = this.forProfile(profileId);
    const result = owner.toggle(promptId);
    return {profileId, ...result, favorites: owner.snapshot()};
  }
}

class MemoryProfileShortcutStore {
  constructor(trace, {profileBindings = {}, failProfileIds = []} = {}) {
    this.trace = trace;
    this.profileBindings = Object.fromEntries(
      Object.entries(profileBindings || {}).map(([profileId, bindings]) => [profileId, clone(bindings)])
    );
    this.failProfileIds = new Set(failProfileIds);
  }
  load(profileId) {
    const value = clone(this.profileBindings[profileId] || []);
    this.trace.push({layer: 'profile_shortcut_store', event: 'bindings_loaded', profileId, count: value.length});
    return value;
  }
  save(profileId, value) {
    const candidate = clone(value);
    this.trace.push({layer: 'profile_shortcut_store', event: 'save_attempted', profileId, count: candidate.length});
    if (this.failProfileIds.has(profileId)) {
      this.trace.push({layer: 'profile_shortcut_store', event: 'save_failed', profileId});
      throw new Error(`shortcut storage unavailable for ${profileId}`);
    }
    this.profileBindings[profileId] = candidate;
    this.trace.push({layer: 'profile_shortcut_store', event: 'save_succeeded', profileId, count: candidate.length});
  }
}

class BoundProfileShortcutStore {
  constructor(rootStore, profileId) {
    this.rootStore = rootStore;
    this.profileId = profileId;
  }
  load() {
    return this.rootStore.load(this.profileId);
  }
  save(value) {
    return this.rootStore.save(this.profileId, value);
  }
}

class ShortcutRegistryContexts {
  constructor({trace, rootStore, promptCatalog}) {
    this.trace = trace;
    this.rootStore = rootStore;
    this.promptCatalog = promptCatalog;
    this.contexts = new Map();
  }
  forProfile(profileId) {
    if (!this.contexts.has(profileId)) {
      const boundStore = new BoundProfileShortcutStore(this.rootStore, profileId);
      const registry = new ShortcutRegistry({
        policy: new ShortcutPolicy(),
        store: boundStore,
        promptCatalog: this.promptCatalog,
        trace: this.trace,
        initialBindings: boundStore.load(),
      });
      this.contexts.set(profileId, registry);
      this.trace.push({layer: 'shortcut_contexts', event: 'canonical_owner_bound', profileId});
    }
    return this.contexts.get(profileId);
  }
}

class ActiveShortcutRegistry {
  constructor(activeProfile, contexts) {
    this.activeProfile = activeProfile;
    this.contexts = contexts;
  }
  current() {
    return this.contexts.forProfile(this.activeProfile.current());
  }
  effectiveBindings() {
    return this.current().effectiveBindings();
  }
  configure(binding) {
    return this.current().configure(binding);
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
    this.activeFavoriteProfileId = null;
    this.activeFavoriteProjection = new Set();
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
      this.trace.push({layer: 'surface', event: 'origin_focus_preserved', promptId, source: context.source, modality: context.modality});
    }
  }
  projectFavoriteSet(profileId, favorites) {
    this.activeFavoriteProfileId = profileId;
    this.activeFavoriteProjection = new Set(favorites);
    this.trace.push({layer: 'surface', event: 'favorite_set_projected', profileId, count: this.activeFavoriteProjection.size});
  }
  projectFavorite(profileId, promptId, favorite) {
    this.favoriteProjection.set(`${profileId}:${promptId}`, favorite);
    if (this.activeFavoriteProfileId === profileId) {
      if (favorite) this.activeFavoriteProjection.add(promptId);
      else this.activeFavoriteProjection.delete(promptId);
    }
    this.trace.push({layer: 'surface', event: 'favorite_projected', profileId, promptId, favorite});
  }
  projectProfile(profile) {
    this.profileProjection.push(profile.id);
    this.trace.push({layer: 'surface', event: 'active_profile_projected', profileId: profile.id});
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
  constructor(gateway) { this.gateway = gateway; }
  copy(promptId, modality) {
    return this.gateway.execute({type: 'COPY_REVEAL_PROMPT', promptId}, 'prompt-control', modality);
  }
  toggleFavorite(promptId, modality) {
    return this.gateway.execute({type: 'TOGGLE_FAVORITE', promptId}, 'prompt-control', modality);
  }
}

class FavoriteShortcutEntrypoint {
  constructor(gateway) { this.gateway = gateway; }
  copy(promptId) {
    return this.gateway.execute({type: 'COPY_REVEAL_PROMPT', promptId}, 'favorite-shortcut', 'keyboard');
  }
}

class ProfileSwitcherEntrypoint {
  constructor(gateway) { this.gateway = gateway; }
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
  profileShortcutBindings = {},
  failShortcutProfileIds = [],
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
    defaultProfileId: profileCatalog.defaultProfile().id,
  });
  const favorites = new FavoritePreferenceContexts(trace, preferenceStore);
  const clipboard = new MemoryClipboard(trace, {fail: clipboardFail, defer: clipboardDefer});
  const usageLedger = new UsageLedger(trace, {fail: usageFail});
  const presentationPolicy = new CopyPresentationPolicy();
  const surface = new ModalityAwarePromptSurface(trace);
  surface.projectFavoriteSet(activeProfile.current(), favorites.snapshot(activeProfile.current()));

  const shortcutStore = new MemoryProfileShortcutStore(trace, {
    profileBindings: profileShortcutBindings,
    failProfileIds: failShortcutProfileIds,
  });
  const shortcutContexts = new ShortcutRegistryContexts({
    trace,
    rootStore: shortcutStore,
    promptCatalog: new Set(['P07', 'P95']),
  });
  const activeShortcuts = new ActiveShortcutRegistry(activeProfile, shortcutContexts);
  const shortcutPromptNavigator = new PromptNavigatorFake(trace);
  const shortcutDispatcher = new ShortcutDispatcher({
    registry: activeShortcuts,
    filterVisibility: new FilterVisibility(trace),
    hotkeyHelpVisibility: new HotkeyHelpVisibility(trace),
    promptNavigator: shortcutPromptNavigator,
    viewNavigator: new ViewNavigatorFake(trace),
    trace,
  });

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
    surface.projectFavoriteSet(target.id, favorites.snapshot(target.id));
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
    shortcutStore,
    shortcutContexts,
    activeShortcuts,
    shortcutDispatcher,
    shortcutPromptNavigator,
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

function expectHotkeyCode(expected, fn) {
  try {
    fn();
  } catch (error) {
    assert(error instanceof HotkeyError, `expected HotkeyError for ${expected}`);
    assert(error.code === expected, `expected ${expected}, observed ${error.code}`);
    return error;
  }
  throw new Error(`ASSERTION_FAILED: expected ${expected}`);
}

async function runSelfTest() {
  const singleProfile = buildProfileModalityProgram({
    profiles: [{id: 'solo', name: 'Default', isDefault: true}],
    profileFavorites: {},
  });
  assert(singleProfile.profileCatalog.needsSwitcher() === false, 'single-profile user needs no profile switcher');

  const pointerCopy = await singleProfile.controls.copy('P07', 'pointer');
  assert(pointerCopy.status === 'COPIED', 'pointer control reaches terminal clipboard value');
  assert(pointerCopy.profileId === 'solo', 'single-profile pointer command uses catalog-defined default identity');
  assert(pointerCopy.presentation.preserveOriginFocus === true, 'pointer control does not receive keyboard-only focus movement');
  assert(singleProfile.surface.focusedCopy.length === 0, 'pointer control path does not force Copy focus');

  const keyboardControlCopy = await singleProfile.controls.copy('P95', 'keyboard');
  assert(keyboardControlCopy.status === 'COPIED', 'keyboard activation of visible control reaches same terminal command');
  assert(keyboardControlCopy.presentation.preserveOriginFocus === true, 'already-focused keyboard control avoids redundant focus movement');
  assert(singleProfile.clipboard.writes.length === 2, 'pointer and keyboard visible controls share clipboard owner');

  const defaultFavorite = await singleProfile.controls.toggleFavorite('P95', 'pointer');
  assert(defaultFavorite.favorite === true, 'default profile Favorite mutation succeeds through canonical owner');
  assert(singleProfile.preferenceStore.legacyFavorites.includes('P95'), 'default profile writes through legacy compatibility slot');
  assert(singleProfile.preferenceStore.storageSlot('solo') === 'legacy-default-slot', 'catalog-defined default profile uses legacy compatibility slot');
  assert(!Object.prototype.hasOwnProperty.call(singleProfile.preferenceStore.profileFavorites, 'solo'), 'default profile does not invent named storage slot');

  const multiProfile = buildProfileModalityProgram({clipboardDefer: true});
  assert(multiProfile.profileCatalog.needsSwitcher() === true, 'multi-profile user exposes profile-switch capability');

  const shortcutCopy = await multiProfile.favoriteShortcut.copy('P07');
  assert(shortcutCopy.status === 'COPIED', 'configured keyboard shortcut journey reaches terminal clipboard value');
  assert(shortcutCopy.presentation.reveal === true, 'keyboard shortcut reveals target prompt');
  assert(shortcutCopy.presentation.focusCopy === true, 'keyboard shortcut focuses Copy recovery target');
  assert(multiProfile.surface.revealed[0] === 'P07', 'shortcut surface reveal is projected');
  assert(multiProfile.surface.focusedCopy[0] === 'P07', 'shortcut Copy focus is projected');

  const sessionBeforeSwitch = multiProfile.session.snapshot();
  const pointerSwitch = await multiProfile.profileSwitcher.activate('work', 'pointer');
  assert(pointerSwitch.status === 'PROFILE_ACTIVE' && multiProfile.activeProfile.current() === 'work', 'pointer profile activation succeeds');
  assert(JSON.stringify(multiProfile.session.snapshot()) === JSON.stringify(sessionBeforeSwitch), 'profile activation does not reset transient browsing state');
  assert([...multiProfile.surface.activeFavoriteProjection].sort().join(',') === 'P95', 'profile activation replaces stale Favorite projection with active profile set');

  const workFavoriteBefore = multiProfile.favorites.snapshot('work');
  assert(workFavoriteBefore.join(',') === 'P95', 'work profile starts with isolated Favorite state');
  const workFavorite = await multiProfile.controls.toggleFavorite('P07', 'pointer');
  assert(workFavorite.favorite === true && workFavorite.profileId === 'work', 'Favorite mutation is scoped to active work profile');
  assert(multiProfile.favorites.snapshot('work').join(',') === 'P07,P95', 'work Favorite candidate is published');
  assert(multiProfile.favorites.snapshot('default').join(',') === 'P07', 'default Favorite state is unchanged by work mutation');
  assert([...multiProfile.surface.activeFavoriteProjection].sort().join(',') === 'P07,P95', 'active work projection follows canonical Favorite owner after mutation');

  const keyboardSwitch = await multiProfile.profileSwitcher.activate('default', 'keyboard');
  assert(keyboardSwitch.status === 'PROFILE_ACTIVE' && multiProfile.activeProfile.current() === 'default', 'keyboard profile activation reaches same semantic command');
  assert([...multiProfile.surface.activeFavoriteProjection].sort().join(',') === 'P07', 'switching back removes stale work Favorite projection');

  const shortcutProfiles = buildProfileModalityProgram();
  shortcutProfiles.activeShortcuts.configure({gesture: 'p95', command: 'COPY_REVEAL_PROMPT', promptId: 'P95'});
  assert(shortcutProfiles.shortcutStore.load('default')[0].gesture === 'p95', 'default shortcut persists through canonical ShortcutRegistry');
  assert(shortcutProfiles.shortcutDispatcher.handleKey({key: 'p'}).pending, 'profile shortcut sequence starts');
  assert(shortcutProfiles.shortcutDispatcher.handleKey({key: '9'}).pending, 'profile shortcut sequence continues');
  assert(shortcutProfiles.shortcutDispatcher.handleKey({key: '5'}).handled, 'profile shortcut dispatches');
  assert(shortcutProfiles.shortcutPromptNavigator.copied[0] === 'P95', 'existing ShortcutDispatcher reaches configured prompt action');

  await shortcutProfiles.profileSwitcher.activate('work', 'pointer');
  assert(!shortcutProfiles.activeShortcuts.effectiveBindings().has('p95'), 'default shortcut is absent from work profile');
  shortcutProfiles.activeShortcuts.configure({gesture: 'p07', command: 'COPY_REVEAL_PROMPT', promptId: 'P07'});
  assert(shortcutProfiles.shortcutStore.load('work')[0].gesture === 'p07', 'work profile stores its own shortcut binding');

  await shortcutProfiles.profileSwitcher.activate('default', 'keyboard');
  assert(shortcutProfiles.activeShortcuts.effectiveBindings().has('p95'), 'default shortcut returns after profile switch');
  assert(!shortcutProfiles.activeShortcuts.effectiveBindings().has('p07'), 'work shortcut does not leak into default profile');

  const rehydratedShortcutContexts = new ShortcutRegistryContexts({
    trace: shortcutProfiles.trace,
    rootStore: shortcutProfiles.shortcutStore,
    promptCatalog: new Set(['P07', 'P95']),
  });
  assert(rehydratedShortcutContexts.forProfile('default').effectiveBindings().has('p95'), 'persisted default shortcut rehydrates through canonical ShortcutRegistry');
  assert(rehydratedShortcutContexts.forProfile('work').effectiveBindings().has('p07'), 'persisted work shortcut rehydrates through canonical ShortcutRegistry');

  const failedShortcuts = buildProfileModalityProgram({failShortcutProfileIds: ['work']});
  await failedShortcuts.profileSwitcher.activate('work', 'pointer');
  expectHotkeyCode('PERSISTENCE_FAILED', () => failedShortcuts.activeShortcuts.configure({gesture: 'p95', command: 'COPY_REVEAL_PROMPT', promptId: 'P95'}));
  assert(!failedShortcuts.activeShortcuts.effectiveBindings().has('p95'), 'failed work shortcut save does not publish binding');
  await failedShortcuts.profileSwitcher.activate('default', 'keyboard');
  assert(!failedShortcuts.activeShortcuts.effectiveBindings().has('p95'), 'failed work shortcut save cannot mutate default profile');

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
  assert(JSON.stringify(failedProfileStore.favorites.snapshot('work')) === JSON.stringify(failedWorkBefore), 'failed work Favorite persistence leaves work owner unchanged');
  assert(JSON.stringify(failedProfileStore.favorites.snapshot('default')) === JSON.stringify(failedDefaultBefore), 'failed work Favorite persistence leaves default owner unchanged');
  assert(!failedProfileStore.surface.favoriteProjection.has('work:P07'), 'failed Favorite persistence does not project false success');

  const inFlight = buildProfileModalityProgram({clipboardDefer: true});
  const pendingDefaultCopy = inFlight.favoriteShortcut.copy('P07');
  await inFlight.profileSwitcher.activate('work', 'pointer');
  const completedDefaultCopy = await pendingDefaultCopy;
  assert(inFlight.activeProfile.current() === 'work', 'profile switch can complete while prior command is in flight');
  assert(completedDefaultCopy.profileId === 'default', 'in-flight command retains initiating profile snapshot');
  const copiedEvents = inFlight.usageLedger.events.filter(event => event.type === 'PROMPT_COPIED');
  assert(copiedEvents.length === 1 && copiedEvents[0].profileId === 'default', 'semantic completion attribution uses initiating profile');

  const privacyPayload = JSON.stringify({
    singleProfile: singleProfile.trace,
    multiProfile: multiProfile.trace,
    shortcutProfiles: shortcutProfiles.trace,
    persistenceFailure: failedProfileStore.trace,
    inFlightSwitch: inFlight.trace,
  });
  assert(!privacyPayload.includes('Repo Sprint Executor'), 'trace excludes profile/prompt display text');
  assert(!privacyPayload.includes('EXECUTE THE REPO SPRINT.'), 'trace excludes prompt bodies');

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
      canonicalFavoriteOwnerReuse: 'PASS',
      profileFavoriteIsolation: 'PASS',
      profileFavoriteProjectionRefresh: 'PASS',
      profileShortcutIsolation: 'PASS',
      profileShortcutRehydration: 'PASS',
      profileShortcutPersistenceFailure: 'PASS',
      unknownProfileFailure: 'PASS',
      invalidModalityBoundary: 'PASS',
      profilePersistenceFailureIsolation: 'PASS',
      inFlightProfileSnapshot: 'PASS',
      privacyBoundedTrace: 'PASS',
    },
    statePolicy: {
      interactionModality: 'invocation-only; never global mutable mode',
      promptCatalog: 'shared across profiles',
      sessionState: 'shared transient state; profile switch does not reset it',
      favorites: 'canonical FavoritePreferences bound to a profile-scoped store',
      shortcuts: 'canonical ShortcutRegistry bound to a profile-scoped store and hydrated through its policy',
      defaultProfile: 'catalog-defined default delegates to legacy preference storage seam',
      tracePrivacy: 'opaque profile id plus semantic metadata; no display names or prompt bodies',
    },
    implementationBoundary: 'prototype only; broad docs/prompt-kit*.js production wiring intentionally deferred',
    traces: {
      singleProfile: singleProfile.trace,
      multiProfile: multiProfile.trace,
      shortcutProfiles: shortcutProfiles.trace,
      shortcutPersistenceFailure: failedShortcuts.trace,
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
  BoundProfileFavoriteStore,
  FavoritePreferenceContexts,
  MemoryProfileShortcutStore,
  BoundProfileShortcutStore,
  ShortcutRegistryContexts,
  ActiveShortcutRegistry,
  CopyPresentationPolicy,
  ModalityAwarePromptSurface,
  InteractionCommandGateway,
  PromptControlEntrypoint,
  FavoriteShortcutEntrypoint,
  ProfileSwitcherEntrypoint,
  buildProfileModalityProgram,
  runSelfTest,
};
