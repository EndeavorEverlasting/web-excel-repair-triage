# Prompt Kit feedback event + hook polling seam

## Purpose

This document defines a bounded executable seam for explicit Prompt Kit feedback. Users may express a like, dislike, or optional written feedback about a stable prompt identity. Repository hooks or agents may poll those durable events incrementally and use them as maintenance evidence. Feedback is **evidence, not mutation authority**: a hook may identify a prompt for review, but votes alone may not rewrite a canonical prompt, bypass tests, or override repository governance.

This seam complements existing Prompt Kit usage/favorite behavior. It does not replace the semantic usage owner, Favorite preferences, P99's user-flow/telemetry role, or the command/profile prototypes. Production UI wiring is intentionally outside this prototype.

## Observable done checklist

The prototype is accepted only when executable evidence proves:

1. each event carries stable `event_id`, `prompt_id`, `event_type`, `value`, `timestamp`, `schema_version`, and `source` fields;
2. event history is append-only so hooks can reliably poll and audit it;
3. the latest vote from one source for one prompt supersedes that source's prior vote for aggregation without deleting history;
4. replaying the exact same event ID/payload is idempotent, while reusing an event ID with different content fails closed;
5. written feedback remains distinct from like/dislike votes;
6. Favorites, semantic usage, prompt votes, and written feedback remain distinguishable evidence classes;
7. unknown prompt identities and malformed events fail closed;
8. metadata cannot contain prompt bodies, clipboard contents, credentials, secrets, or equivalent sensitive payloads;
9. a versioned cursor lets a consumer request only unseen events;
10. polling is bounded and a cursor ahead of the log fails closed;
11. a hook persists its checkpoint only after every event in the returned page is successfully consumed;
12. retrying from the same checkpoint cannot double-count already-applied event IDs;
13. aggregation can answer which prompts have repeated negative votes and how much written feedback exists;
14. thresholded negative feedback produces `REVIEW_CANDIDATE`, never an automatic prompt rewrite;
15. repository/static proof is not represented as live browser or user-acceptance proof.

## Event contract

Schema: `prompt-feedback-event/v1`

Required fields:

| Field | Contract |
| --- | --- |
| `event_id` | Stable caller-generated idempotency identity. |
| `prompt_id` | Stable canonical Prompt Kit identity such as `P99`; titles/order are not identities. |
| `event_type` | `prompt_vote` or `prompt_feedback`. |
| `value` | `like` / `dislike` for votes; `comment` for written feedback. |
| `timestamp` | Normalized ISO-compatible timestamp. |
| `schema_version` | Exactly `prompt-feedback-event/v1`. |
| `source` | Opaque bounded source identity used for vote replacement/idempotency semantics. |

Optional fields:

- `comment` — written feedback only, bounded to 1000 characters in the prototype.
- `metadata` — small scalar context such as the UI surface; sensitive payload keys are rejected.
- `supersedes_event_id` — emitted on a later vote from the same `(prompt_id, source)` pair.
- `sequence` — monotonically increasing store-owned sequence used for cursor traversal.

The event log never stores prompt bodies merely to identify the prompt; `prompt_id` is sufficient.

## Explicit feedback semantics

### Likes and dislikes

Voting is a mutable user judgment represented by immutable events. The store retains every submitted vote, but the aggregate opinion for a `(prompt_id, source)` pair is the newest accepted vote. Therefore:

```text
LIKE evt-1 -> DISLIKE evt-2
```

is two auditable events but one current negative opinion. `evt-2.supersedes_event_id == evt-1`.

This avoids two bad alternatives:

- deleting history, which makes polling/audit fragile;
- counting both votes forever, which misrepresents a changed opinion.

### Written feedback

Written feedback is a separate event class. It can explain *why* a vote exists, but it does not need to accompany a vote and is not converted into a synthetic like/dislike.

### Favorites and semantic usage

These remain separate signals:

- **Favorite:** keep this prompt readily accessible.
- **Semantic usage:** the prompt/workflow was actually used/completed.
- **Like/dislike:** explicit quality/usefulness judgment.
- **Written feedback:** qualitative explanation or suggestion.

A maintenance consumer may correlate those classes when a future canonical owner supplies them, but it must not collapse them into one counter or infer that Favorite == Like.

## Polling and cursor contract

Cursor schema: `prompt-feedback-cursor/v1`.

The prototype cursor is an opaque-to-consumers string carrying the last accepted sequence:

```text
prompt-feedback-cursor/v1:42
```

The public behavior is:

```text
pollSince(cursor, limit)
  -> events after cursor, in append order
  -> next_cursor for the final returned sequence
  -> has_more
```

Properties:

- empty/new consumers start at cursor `...:0`;
- the read does not mutate the log;
- page size is bounded;
- an unchanged log returns zero events and the same cursor;
- future/malformed cursors fail closed rather than silently skipping data.

The numeric representation is a prototype detail; production may replace it with another opaque durable token while preserving the versioned semantics.

## Hook checkpoint transaction

A consumer owns a durable checkpoint independently from the event log:

```text
LOAD CHECKPOINT
  -> POLL EVENTS SINCE CHECKPOINT
  -> APPLY EACH EVENT IDEMPOTENTLY
  -> SAVE next_cursor only after the page succeeds
```

If processing fails, the checkpoint stays on the previous cursor. The next run re-reads that page. Since the aggregator deduplicates by `event_id`, already-applied events from a partially processed page do not double-count.

This is at-least-once delivery at the consumer boundary with idempotent application, not an unsafe claim of exactly-once distributed delivery.

## Maintenance evidence boundary

`FeedbackAggregator.maintenanceCandidates()` may return rows such as:

```text
prompt_id=P99
likes=0
dislikes=2
feedback_count=1
disposition=REVIEW_CANDIDATE
```

That row means “inspect/refine this prompt.” It does **not** authorize:

- changing registry prompt content;
- assigning a new prompt ID;
- bypassing `prompt_registry_ops.py` or generated-site parity;
- weakening tests/validators;
- treating a popularity threshold as repository governance.

A prompt-maintenance sprint still needs repository evidence, accepted scope, focused regressions, generated parity, and ordinary integration proof.

## Prototype journey

Executable owner: `docs/prompt-kit-feedback-prototype.js`.

Representative sequence:

```text
USER LIKE P99
  -> append prompt_vote(evt-001)
USER CHANGES TO DISLIKE P99
  -> append prompt_vote(evt-002, supersedes evt-001)
ANOTHER SOURCE DISLIKES P99
  -> append prompt_vote(evt-003)
USER WRITES FEEDBACK
  -> append prompt_feedback(evt-004)
HOOK cursor=0
  -> poll page 1
  -> apply events idempotently
  -> persist checkpoint
HOOK resumes
  -> poll only unseen events
  -> aggregate P99 as 0 likes / 2 dislikes / 1 written feedback
  -> emit REVIEW_CANDIDATE
  -> no prompt mutation API exists
```

Failure journeys prove conflicting event IDs, unknown prompts, sensitive metadata, future cursors, and failed hook processing all fail closed.

## Relationship to current Prompt Kit owners

- **P99** remains the reusable user-flow and preference-telemetry semantic owner. This prototype supplies a concrete explicit-feedback event/polling seam that a later P99/product integration can consume.
- **Favorite/usage runtime** remains independent; this prototype does not edit existing favorite/gameplay branches.
- **Command/profile program design** remains independent; feedback `source` is opaque and does not assume a particular profile implementation.
- **Prompt registry mutation** remains under existing canonical helper/governance contracts; the feedback consumer has no write authority there.

This boundary deliberately avoids racing the currently open Prompt Kit profile/modality and older preference-gameplay PRs.

## Validation

Focused repository proof:

```text
node --check docs/prompt-kit-feedback-prototype.js
node docs/prompt-kit-feedback-prototype.js
python -m unittest tests.test_prompt_kit_feedback_prototype -v
git diff --check
```

The dedicated workflow runs those checks on the exact PR head and on `main` pushes affecting this seam.

## Second-pass critique targets

After the first green execution, inspect specifically for:

1. whether a changed vote is incorrectly counted twice;
2. whether event replay can double-count;
3. whether a failed consumer advances its checkpoint;
4. whether a cursor can silently skip unseen events;
5. whether feedback payloads accidentally capture prompt/clipboard/secret content;
6. whether the aggregator exposes any automatic prompt-mutation authority;
7. whether the seam collides with existing profile, Favorite, usage, or prompt-registry owners.

A green happy path without these checks is not fixed-point proof.

## Proof ceiling

This sprint can prove the event schema, append/replacement semantics, idempotency, polling/cursor behavior, checkpoint failure atomicity, privacy guards, aggregation, and no-auto-rewrite boundary in Node/Python/GitHub Actions.

It cannot prove user-visible like/dislike controls, browser persistence/migration, cross-device synchronization, authenticated multi-user identity, real hook scheduling, subjective usefulness, or production prompt-maintenance decisions. Those remain later product/runtime/integration gates rather than being inferred from this prototype.
