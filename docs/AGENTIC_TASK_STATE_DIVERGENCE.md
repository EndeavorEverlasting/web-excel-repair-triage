# Agentic Task-State Divergence

This sprint treats prompt usage, task iteration, and corrective operator work as different signals.

## Grounding episode

The scoring unit is a **grounding episode**, not a prompt identity and not an entire mission. An episode starts when a task/sprint anchor is established or when a successful REGROUND/REBOOTSTRAP creates a clean task model. It closes when the anchored task reaches terminal evidence, when post-recovery durable evidence establishes a clean successor episode, or when the operator explicitly starts a distinct sprint/task anchor.

Ordinary prompt reuse across episodes is neutral. Legitimate repeated work that advances durable evidence is neutral. Correction burden never carries across episode IDs.

## Correction events

A correction event is one observed corrective operator action bound to one grounding episode. It is not a prompt invocation. It is not a normal task iteration. It has no occurrence-count multiplier: repeated corrections are represented by separate uniquely identified events.

For episode `e`, let:

`C_e = { a | a.grounding_episode_id = e AND a.corrective = true }`

Then:

`B_e = sum(weight[a.kind] for a in C_e)`

`Y_e = response_relevance_e / (1 + B_e)`

`D_e = 1 - Y_e`

Where `B_e` is correction burden, `Y_e` is interaction yield, and `D_e` is divergence pressure. Prompt usage count and legitimate sprint/task iteration count do not appear in `B_e`.

This is a bounded heuristic, not a probability model. P99 owns outcome/friction semantics, P115 owns re-ground coordination, P07/P32 own repair, and P105 owns authorized promotion.

## Recovery

The bounded recovery sequence is: freeze unproven mutation; refresh durable truth; rebuild the task model and complete work graph; diff prior assumptions against evidence; re-anchor one-to-one to the current request; execute the smallest dependency-ready action; and close the episode after successful post-recovery evidence advance or escalate the intervention if the same divergence recurs.
