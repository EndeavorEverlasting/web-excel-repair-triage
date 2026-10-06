# Prompt Invocation Composition Algebra

**Contract:** `harness/contracts/prompt-invocation-composition.v1.json`  
**Compiler:** `scripts/prompt_invocation_composition.py`  
**Status:** shared harness owner; no new P-number.

## Core language rule

**Invoke** does not mean **include every instruction**.

An invocation asks the compiler to evaluate a prompt against the current typed task. Only the applicable residual survives into the composed execution program.

For prompt (P_i) with declared facet set (F_i) and task facet set (T):

[
A_i = F_i \cap T
]

If another accepted owner or upstream artifact already supplies a shared facet, the downstream contribution is residualized:

[
R_i = A_i \setminus C_i
]

where (C_i) is the already-canonicalized overlap.

This is intentionally set algebra, not a claim that natural-language prompts form a Euclidean vector space.

## Relation algebra

| Relation | Rule |
| --- | --- |
| `DISJOINT` | Contributions commute; canonical numeric ID is the deterministic tie-break unless a task edge orders them. |
| `DUPLICATE` | Keep the canonical owner once; subtract duplicate overlap from the downstream residual. |
| `ORDERED_OVERLAP` | Resolve the shared decision once, then pass it downstream and invoke only the residual. |
| `CONSTRAINING_OVERLAP` | Keep the constraint; it may narrow but never grant authority. |
| `CONFLICT` | Fail closed. No model preference, similarity score, or "best guess" chooses an owner. |

An overlap with no explicit rule is itself `INCOHERENT_INVOCATION`.

## Authority is not additive

Prompt invocation is procedural composition, not permission composition.

For a contemplated action (a):

[
Authority_{eff}(a) =
TaskAuthority(a)
\land RepoPolicy(a)
\land SafetyPolicy(a)
\land VerifiedCapability(a)
\land SelectedOwnerScope(a)
]

Therefore:

[
P01 + P07 + P08 \neq SuperAuthority
]

The contract also defines a set-divergence guard:

[
A_{out}(v) \setminus (A_{in}(v) \cup A_{external}) = \varnothing
]

A prompt node may route, specialize, or narrow authority. It may not become an authority source.

## Deterministic P04 / P05 pushback

P04 and P05 intentionally overlap on `planning.runtime_partition`, but they do not compete for the same terminal job.

- **P04** owns new/revised factoring, ownership/collision decisions, and dispatch structure.
- **P05** packages accepted factoring into an ordered serialized launch pack.
- If P05 is invoked and the P04 artifact is `ABSENT`, `STALE`, or `CONTRADICTED`, the compiler returns `ROUTE_REQUIRED` with **P04 → P05**.
- If the P04 artifact is `ACCEPTED_CURRENT`, P05 consumes it and the shared intersection is not recomputed.
- Missing artifact state is `INSUFFICIENT_CONTEXT`; the agent does not flip a coin.

This makes pushback fact-driven rather than probabilistic.

## P97 prior art

P97 was invoked before this contract was authored.

| Reference | Mechanic | Local disposition |
| --- | --- | --- |
| Cedar | independent policies; forbid wins; no permit cancels a forbid | constraints are monotone; invocation cannot create permission |
| Rust coherence | overlapping trait implementations are incoherent | unresolved ownership overlap is a compile error |
| Python C3 | monotone deterministic linearization; inconsistent precedence is rejected | prompt precedence must linearize or fail |
| Nix module system | typed merges plus explicit override/order priorities | shared prompt facets require declared merge/owner/order rules |

Exact repositories, commits, and source paths are pinned in the machine contract.

## Divergence and curl: where the analogy is useful

The divergence/curl intuition is useful, but v1 does not pretend we already have a numeric vector field.

Two graph diagnostics are mathematically defensible now:

1. **Authority source/divergence guard** — detect any outbound authority not grounded in inbound/external authority. The allowed residual is the empty set.
2. **No-progress circulation guard** — reject a closed prompt-routing cycle when evidence, proof floor, artifact identity, and task state are unchanged.

A future typed state field could promote these into numerical divergence/circulation metrics. Until then, set difference and graph-cycle invariants are the exact model.

## Example

```json
{
  "schema_version": "prompt-invocation-request/v1",
  "invocations": ["P01", "P04", "P07", "P08", "P82"],
  "task_facets": [
    "harness.integrity",
    "planning.factor",
    "execution.repository_mutation",
    "proof.live_runtime",
    "iteration.empirical"
  ],
  "facts": {}
}
```

The compiler projects each invocation, adds only evidence-backed dependency edges, and emits one stable linearization. It does not concatenate five prompt bodies.

## CLI

```powershell
python scripts/prompt_invocation_composition.py validate-contract --summary
python scripts/prompt_invocation_composition.py compose --input <request.json>
```

The receipt includes:
- state;
- canonical linearization;
- projected vs residual vs inherited facets;
- deterministic pushback;
- precedence edges;
- `NO_AUTHORITY_EXPANSION`;
- a content hash for replay/comparison.

## Proof ceiling

Repository/static tests can prove the algebra and deterministic compiler. They do not prove that every downstream model or UI already invokes this compiler. Consumer wiring is a separate integration/runtime proof lane.
