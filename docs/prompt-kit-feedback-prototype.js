'use strict';

const FEEDBACK_SCHEMA = 'prompt-feedback-event/v1';
const CURSOR_SCHEMA = 'prompt-feedback-cursor/v1';
const EVENT_TYPES = new Set(['prompt_vote', 'prompt_feedback']);
const VOTE_VALUES = new Set(['like', 'dislike']);
const SENSITIVE_KEYS = /(prompt[_-]?body|copy[_-]?content|clipboard|secret|token|password|credential)/i;

class FeedbackError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'FeedbackError';
    this.code = code;
    this.details = details;
  }
}

function stableJson(value) {
  if (Array.isArray(value)) return '[' + value.map(stableJson).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + stableJson(value[key])).join(',') + '}';
  }
  return JSON.stringify(value);
}

function requireText(value, field, maxLength = 200) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new FeedbackError('INVALID_EVENT', `${field} must be a non-empty string.`, {field});
  }
  const text = value.trim();
  if (text.length > maxLength) {
    throw new FeedbackError('INVALID_EVENT', `${field} exceeds ${maxLength} characters.`, {field, maxLength});
  }
  return text;
}

function normalizeTimestamp(value) {
  const timestamp = requireText(value, 'timestamp', 64);
  if (!Number.isFinite(Date.parse(timestamp))) {
    throw new FeedbackError('INVALID_EVENT', 'timestamp must be an ISO-compatible date/time.', {timestamp});
  }
  return new Date(timestamp).toISOString();
}

function sanitizeMetadata(metadata) {
  if (metadata === undefined || metadata === null) return undefined;
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
    throw new FeedbackError('INVALID_EVENT', 'metadata must be a flat object when supplied.');
  }
  const safe = {};
  for (const [rawKey, rawValue] of Object.entries(metadata)) {
    const key = requireText(rawKey, 'metadata key', 80);
    if (SENSITIVE_KEYS.test(key)) {
      throw new FeedbackError('SENSITIVE_FEEDBACK_PAYLOAD', `metadata key ${key} is not permitted.`, {key});
    }
    if (!['string', 'number', 'boolean'].includes(typeof rawValue)) {
      throw new FeedbackError('INVALID_EVENT', `metadata value for ${key} must be scalar.`, {key});
    }
    if (typeof rawValue === 'string' && rawValue.length > 200) {
      throw new FeedbackError('INVALID_EVENT', `metadata value for ${key} is too long.`, {key});
    }
    safe[key] = rawValue;
  }
  return Object.keys(safe).length ? safe : undefined;
}

class FeedbackEventStore {
  constructor({promptIds = []} = {}) {
    this.promptIds = new Set(promptIds);
    this.events = [];
    this.byEventId = new Map();
    this.latestVoteByPromptSource = new Map();
  }

  _validateCommon(input) {
    const eventId = requireText(input.event_id, 'event_id', 160);
    const promptId = requireText(input.prompt_id, 'prompt_id', 40);
    const eventType = requireText(input.event_type, 'event_type', 40);
    const source = requireText(input.source, 'source', 120);
    if (!this.promptIds.has(promptId)) {
      throw new FeedbackError('UNKNOWN_PROMPT', `Unknown prompt ${promptId}.`, {promptId});
    }
    if (!EVENT_TYPES.has(eventType)) {
      throw new FeedbackError('INVALID_EVENT_TYPE', `Unsupported event type ${eventType}.`, {eventType});
    }
    return {
      event_id: eventId,
      prompt_id: promptId,
      event_type: eventType,
      timestamp: normalizeTimestamp(input.timestamp),
      schema_version: FEEDBACK_SCHEMA,
      source,
    };
  }

  _append(event) {
    const existing = this.byEventId.get(event.event_id);
    if (existing) {
      if (stableJson(existing) !== stableJson(event)) {
        throw new FeedbackError('EVENT_ID_CONFLICT', `event_id ${event.event_id} already exists with different content.`, {eventId: event.event_id});
      }
      return existing;
    }
    const stored = Object.freeze({...event, sequence: this.events.length + 1});
    this.events.push(stored);
    this.byEventId.set(stored.event_id, stored);
    return stored;
  }

  submitVote(input) {
    const common = this._validateCommon({...input, event_type: 'prompt_vote'});
    const value = requireText(input.value, 'value', 20).toLowerCase();
    if (!VOTE_VALUES.has(value)) {
      throw new FeedbackError('INVALID_VOTE', 'Vote value must be like or dislike.', {value});
    }
    const voteKey = `${common.prompt_id}\u0000${common.source}`;
    const previous = this.latestVoteByPromptSource.get(voteKey);
    const candidate = {
      ...common,
      value,
      ...(previous ? {supersedes_event_id: previous.event_id} : {}),
      ...(sanitizeMetadata(input.metadata) ? {metadata: sanitizeMetadata(input.metadata)} : {}),
    };
    const stored = this._append(candidate);
    this.latestVoteByPromptSource.set(voteKey, stored);
    return stored;
  }

  submitFeedback(input) {
    const common = this._validateCommon({...input, event_type: 'prompt_feedback'});
    const comment = requireText(input.comment, 'comment', 1000);
    const metadata = sanitizeMetadata(input.metadata);
    return this._append({
      ...common,
      value: 'comment',
      comment,
      ...(metadata ? {metadata} : {}),
    });
  }

  static encodeCursor(sequence) {
    if (!Number.isInteger(sequence) || sequence < 0) {
      throw new FeedbackError('INVALID_CURSOR', 'Cursor sequence must be a non-negative integer.');
    }
    return `${CURSOR_SCHEMA}:${sequence}`;
  }

  static decodeCursor(cursor) {
    const text = requireText(cursor, 'cursor', 120);
    const prefix = `${CURSOR_SCHEMA}:`;
    if (!text.startsWith(prefix)) {
      throw new FeedbackError('INVALID_CURSOR', 'Cursor schema is not supported.', {cursor: text});
    }
    const sequence = Number(text.slice(prefix.length));
    if (!Number.isInteger(sequence) || sequence < 0) {
      throw new FeedbackError('INVALID_CURSOR', 'Cursor sequence is malformed.', {cursor: text});
    }
    return sequence;
  }

  pollSince(cursor = FeedbackEventStore.encodeCursor(0), {limit = 100} = {}) {
    const sequence = FeedbackEventStore.decodeCursor(cursor);
    if (sequence > this.events.length) {
      throw new FeedbackError('FUTURE_CURSOR', 'Cursor is ahead of the current event log.', {sequence, eventCount: this.events.length});
    }
    if (!Number.isInteger(limit) || limit < 1 || limit > 500) {
      throw new FeedbackError('INVALID_POLL_LIMIT', 'Poll limit must be an integer from 1 through 500.', {limit});
    }
    const events = this.events.slice(sequence, sequence + limit);
    const nextSequence = events.length ? events[events.length - 1].sequence : sequence;
    return Object.freeze({
      schema_version: CURSOR_SCHEMA,
      cursor,
      next_cursor: FeedbackEventStore.encodeCursor(nextSequence),
      has_more: nextSequence < this.events.length,
      events: Object.freeze([...events]),
    });
  }
}

class FeedbackAggregator {
  constructor() {
    this.processedEventIds = new Set();
    this.latestVoteByPromptSource = new Map();
    this.commentsByPrompt = new Map();
  }

  apply(event) {
    if (this.processedEventIds.has(event.event_id)) return false;
    if (event.schema_version !== FEEDBACK_SCHEMA) {
      throw new FeedbackError('UNSUPPORTED_EVENT_SCHEMA', `Unsupported feedback schema ${event.schema_version}.`);
    }
    if (event.event_type === 'prompt_vote') {
      this.latestVoteByPromptSource.set(`${event.prompt_id}\u0000${event.source}`, event);
    } else if (event.event_type === 'prompt_feedback') {
      const comments = this.commentsByPrompt.get(event.prompt_id) || [];
      comments.push(event);
      this.commentsByPrompt.set(event.prompt_id, comments);
    } else {
      throw new FeedbackError('INVALID_EVENT_TYPE', `Unsupported event type ${event.event_type}.`);
    }
    this.processedEventIds.add(event.event_id);
    return true;
  }

  summary(promptId) {
    const votes = [...this.latestVoteByPromptSource.values()].filter(event => event.prompt_id === promptId);
    const comments = this.commentsByPrompt.get(promptId) || [];
    return Object.freeze({
      prompt_id: promptId,
      likes: votes.filter(event => event.value === 'like').length,
      dislikes: votes.filter(event => event.value === 'dislike').length,
      feedback_count: comments.length,
      latest_vote_events: Object.freeze(votes.map(event => event.event_id).sort()),
      feedback_events: Object.freeze(comments.map(event => event.event_id)),
    });
  }

  maintenanceCandidates({minimumDislikes = 2} = {}) {
    if (!Number.isInteger(minimumDislikes) || minimumDislikes < 1) {
      throw new FeedbackError('INVALID_THRESHOLD', 'minimumDislikes must be a positive integer.');
    }
    const promptIds = new Set([
      ...[...this.latestVoteByPromptSource.values()].map(event => event.prompt_id),
      ...this.commentsByPrompt.keys(),
    ]);
    return [...promptIds]
      .map(promptId => this.summary(promptId))
      .filter(row => row.dislikes >= minimumDislikes)
      .map(row => Object.freeze({...row, disposition: 'REVIEW_CANDIDATE'}));
  }
}

class MemoryCheckpointStore {
  constructor(initialCursor = FeedbackEventStore.encodeCursor(0)) {
    this.cursor = initialCursor;
    this.saveCalls = 0;
  }
  load() { return this.cursor; }
  save(cursor) {
    FeedbackEventStore.decodeCursor(cursor);
    this.cursor = cursor;
    this.saveCalls += 1;
  }
}

class FeedbackHookConsumer {
  constructor({eventStore, aggregator, checkpointStore}) {
    this.eventStore = eventStore;
    this.aggregator = aggregator;
    this.checkpointStore = checkpointStore;
  }
  pollOnce({limit = 100} = {}) {
    const cursor = this.checkpointStore.load();
    const page = this.eventStore.pollSince(cursor, {limit});
    for (const event of page.events) this.aggregator.apply(event);
    this.checkpointStore.save(page.next_cursor);
    return page;
  }
}

function assert(value, message) {
  if (!value) throw new Error(`ASSERTION_FAILED: ${message}`);
}

function expectCode(code, fn) {
  try { fn(); } catch (error) {
    assert(error instanceof FeedbackError, `expected FeedbackError ${code}`);
    assert(error.code === code, `expected ${code}, observed ${error.code}`);
    return error;
  }
  throw new Error(`ASSERTION_FAILED: expected ${code}`);
}

function runSelfTest() {
  const events = new FeedbackEventStore({promptIds: ['P07', 'P99']});
  events.submitVote({event_id: 'evt-001', prompt_id: 'P99', value: 'like', timestamp: '2026-08-25T12:00:00-04:00', source: 'local-profile:alpha'});
  const replacement = events.submitVote({event_id: 'evt-002', prompt_id: 'P99', value: 'dislike', timestamp: '2026-08-25T12:01:00-04:00', source: 'local-profile:alpha'});
  events.submitVote({event_id: 'evt-003', prompt_id: 'P99', value: 'dislike', timestamp: '2026-08-25T12:02:00-04:00', source: 'local-profile:beta'});
  events.submitFeedback({event_id: 'evt-004', prompt_id: 'P99', comment: 'The closeout is useful, but this route is too long.', timestamp: '2026-08-25T12:03:00-04:00', source: 'local-profile:alpha', metadata: {surface: 'prompt-detail'}});
  assert(replacement.supersedes_event_id === 'evt-001', 'new vote explicitly supersedes the prior vote from the same source');
  assert(events.events.length === 4, 'event history stays append-only');

  const idempotent = events.submitVote({event_id: 'evt-003', prompt_id: 'P99', value: 'dislike', timestamp: '2026-08-25T12:02:00-04:00', source: 'local-profile:beta'});
  assert(idempotent.event_id === 'evt-003' && events.events.length === 4, 'same event replay is idempotent');
  expectCode('EVENT_ID_CONFLICT', () => events.submitVote({event_id: 'evt-003', prompt_id: 'P99', value: 'like', timestamp: '2026-08-25T12:02:00-04:00', source: 'local-profile:beta'}));
  expectCode('SENSITIVE_FEEDBACK_PAYLOAD', () => events.submitFeedback({event_id: 'evt-sensitive', prompt_id: 'P99', comment: 'bad metadata', timestamp: '2026-08-25T12:04:00-04:00', source: 'local-profile:alpha', metadata: {clipboard: 'contents'}}));
  expectCode('UNKNOWN_PROMPT', () => events.submitVote({event_id: 'evt-unknown', prompt_id: 'P404', value: 'like', timestamp: '2026-08-25T12:04:00-04:00', source: 'local-profile:alpha'}));

  const aggregator = new FeedbackAggregator();
  const checkpoint = new MemoryCheckpointStore();
  const hook = new FeedbackHookConsumer({eventStore: events, aggregator, checkpointStore: checkpoint});
  const first = hook.pollOnce({limit: 2});
  assert(first.events.length === 2 && first.has_more === true, 'poll returns a bounded first page');
  const second = hook.pollOnce({limit: 100});
  assert(second.events.length === 2 && second.has_more === false, 'second poll resumes exactly after checkpoint');
  const empty = hook.pollOnce();
  assert(empty.events.length === 0, 'unchanged checkpoint poll is empty');

  const summary = aggregator.summary('P99');
  assert(summary.likes === 0 && summary.dislikes === 2, 'latest vote replaces the earlier vote in aggregation');
  assert(summary.feedback_count === 1, 'written feedback remains a separate evidence class');
  const candidates = aggregator.maintenanceCandidates({minimumDislikes: 2});
  assert(candidates.length === 1 && candidates[0].disposition === 'REVIEW_CANDIDATE', 'negative votes surface a maintenance candidate only');
  assert(typeof aggregator.rewritePrompt === 'undefined', 'feedback aggregation has no prompt mutation authority');

  const beforeFailure = checkpoint.load();
  events.submitFeedback({event_id: 'evt-005', prompt_id: 'P07', comment: 'Keep this one.', timestamp: '2026-08-25T12:05:00-04:00', source: 'local-profile:gamma'});
  const failingAggregator = {
    apply() { throw new FeedbackError('CONSUMER_FAILED', 'Injected hook processing failure.'); },
  };
  const failingHook = new FeedbackHookConsumer({eventStore: events, aggregator: failingAggregator, checkpointStore: checkpoint});
  expectCode('CONSUMER_FAILED', () => failingHook.pollOnce());
  assert(checkpoint.load() === beforeFailure, 'checkpoint does not advance when consumer processing fails');

  expectCode('FUTURE_CURSOR', () => events.pollSince(FeedbackEventStore.encodeCursor(999)));

  return {
    status: 'PASS',
    schema: FEEDBACK_SCHEMA,
    cursorSchema: CURSOR_SCHEMA,
    journeys: {
      appendOnlyVoteHistory: 'PASS',
      replacementVoteAggregation: 'PASS',
      idempotentEventReplay: 'PASS',
      eventIdConflictFailsClosed: 'PASS',
      cursorPagination: 'PASS',
      hookCheckpointResume: 'PASS',
      checkpointFailureAtomicity: 'PASS',
      writtenFeedbackSeparateFromVotes: 'PASS',
      privacyBoundedMetadata: 'PASS',
      maintenanceEvidenceWithoutRewriteAuthority: 'PASS',
    },
    evidenceClasses: ['favorite', 'semantic_usage', 'prompt_vote', 'prompt_feedback'],
    eventCount: events.events.length,
    p99Summary: summary,
    maintenanceCandidates: candidates,
  };
}

if (require.main === module) {
  try {
    process.stdout.write(JSON.stringify(runSelfTest(), null, 2) + '\n');
  } catch (error) {
    process.stderr.write(`${error && error.stack || error}\n`);
    process.exitCode = 1;
  }
}

module.exports = {
  FEEDBACK_SCHEMA,
  CURSOR_SCHEMA,
  FeedbackError,
  FeedbackEventStore,
  FeedbackAggregator,
  MemoryCheckpointStore,
  FeedbackHookConsumer,
  runSelfTest,
};
