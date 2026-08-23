# Operator Delivery and Live-Certification Contract

Binding when work concerns technician acquisition, cross-device delivery, local execution, or live certification.

## Acquisition

- Prefer the lowest-friction supported surface. Browser-only Prompt Kit use should use the public URL; do not require a clone.
- A repository-backed Windows flow must provide a mouse-accessible CMD entry point. If the repository is absent, clone the canonical repository. If present, verify canonical origin/default branch, fetch, and fast-forward only.
- Refuse to reset, overwrite, discard, or silently bypass dirty/divergent/local-only work. Never embed credentials or user-specific absolute paths.
- Acquisition is not completion: verify required files and run the owning validator/launcher before claiming readiness.
- When choices are necessary, use the registered GUI/operator surface instead of forcing technicians to reconstruct command fragments.
- Do not recursively hunt disks for a convenient checkout. Use the canonical destination/registry or an explicit operator-selected path.

## Live certification

Live evidence is separate from CI, replay, fixtures, emulators, and source/build proof.

**Local topology** is appropriate when proof depends on a workstation, attached device, protected network, private input, browser/desktop behavior, or a runtime unavailable remotely. Use a repository-owned launcher/script/validator; identify commit, target, phase, artifacts, and proof ceiling; dry-run first for mutating operations; propagate nonzero exit codes; keep only non-sensitive evidence in approved outputs.

**Remote-branch topology** is appropriate when deterministic implementation/artifacts can be produced safely without protected runtime access. Use one isolated branch, commit/push the implementation and safe evidence, and hand off an exact fetch/pin/validate command that preserves dirty primary work. Remote-branch green proof is not target-runtime or production proof.

When both are viable, choose the topology that produces the strongest safe evidence with the least operator reconstruction.

## Freshness gate for live certification

- Before selecting the certification subject, refresh remote/provider truth (`git fetch --all --prune --tags` or provider equivalent), resolve the actual default branch, and inspect current/open/recent overlapping PRs and branches plus the latest relevant commits. An unfetched checkout, remembered SHA, old feature base, or prior handoff is not a certification floor.
- Establish the current evidence floor: owning runtime-certification contract, launcher/generator/profile/schema, focused validators, current CI/build conclusions, registered artifact manifests/reports, prior live-cert receipts, and known blockers. Prior evidence remains useful history but only proves the exact head/artifact/inputs it observed.
- Pin the exact subject after refresh: commit SHA, required base/dependency floor, target, phase, artifact path and manifest/hash when applicable, runtime route/provider, and proof ceiling. The runtime report must record those identities.
- If the remote base/head, dependency, launcher/generator/profile/schema, target artifact, or evidence owner moves after preflight, mark affected proof stale and refresh/reconcile/rebuild/revalidate before claiming certification. A runtime pass cannot bless stale repository state, and old runtime evidence cannot certify a newer head.
- Preserve dirty/divergent/local-only work while refreshing; never force-reset merely to obtain a certification floor.

## Actionable runtime / live-cert closeout

- Every runtime or live-cert stop must state: completed/proven behavior; remaining gaps; risks; blockers; proof ceiling; integration state; and the first executable next action or ordered dependency-aware next steps.
- Each gap/risk/blocker must identify the affected target or artifact, current evidence, consequence, and the exact action or operator gate that advances it. A passing command, process start, or green CI result does not erase unobserved runtime risk.
- The next action must identify owner, dependency, exact command or operator action, expected evidence/artifact, and completion gate. Continue agent-capable work immediately; reserve handoff for a protected runtime, physical action, inaccessible credential/system, or another genuine operator-only gate.
- `none; no safe actionable work remains` is valid only when the requested proof ceiling is actually satisfied, integration/cleanup is complete or explicitly out of scope, and no known safe unproven action remains.

## Evidence and artifact safety

Evidence strength is ordered by what was actually observed. Distinguish source/build proof, process start, command acknowledgment, observed behavior, local runtime proof, target proof, and production proof. Never silently promote a weaker class.

Runtime evidence belongs in registered `Outputs/` or proof/report paths. HARs, credentials, private workbooks, protected inputs, or sensitive raw logs must not be committed merely to prove execution.

## Owned implementation references

Use the relevant registered workflow, capability, trigger, launcher, skill, and validator. Prompt Kit acquisition details belong to `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`; generic harness details do not belong here.
