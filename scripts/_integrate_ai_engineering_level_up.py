from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Patch anchor not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


prompts = [
    {
        "id": "P67",
        "seq": "67",
        "name": "Repository Eval Framework Builder",
        "type": "VALIDATE",
        "class": "AI ENGINEERING / EVALS",
        "sprintRole": "Build a repository-wide eval system that catches regressions before model or agent behavior ships",
        "progress": "YES",
        "useWhen": "An AI- or agent-enabled repository has tests but lacks a deliberate eval framework for task quality, tool use, failure modes, regressions, or model-dependent behavior.",
        "inspectFirst": "Repository rules, product tasks, agent/model entry points, existing tests and fixtures, prompt/skill registries, production incidents, support failures, runtime traces, validators, CI, and current proof gaps.",
        "expectedOutput": "A versioned eval plan plus implemented deterministic and model-aware cases, fixtures, scoring oracles, regression gates, machine-readable results, CI wiring, and an honest proof ceiling.",
        "nextStep": "Run the smallest representative eval suite against the current implementation, repair the highest-severity failure it exposes, and preserve the result as a reproducible gate.",
        "proofGate": "The eval suite covers representative success and failure cases, deterministic checks run before expensive judge/model checks, regressions fail closed, skipped evidence is explicit, and test count is never substituted for task-quality proof.",
        "color": "Teal",
        "copySheet": "P67_COPY_SAFE",
        "category": "standard",
        "copyContent": """BUILD A REPOSITORY-WIDE AI EVAL FRAMEWORK. DO NOT STOP AT A RUBRIC OR TEST PLAN.\nRepo: xyz_repo_or_path\nAI/agent surface: xyz_ai_surface\nKnown failures or quality risks: xyz_eval_risks\n\nMISSION\nTurn the repository's real user tasks and failure history into an executable eval system that catches regressions before shipment. Reuse existing tests and harnesses, but do not confuse ordinary unit coverage with AI-behavior evaluation.\n\n1. MAP THE BEHAVIOR TO EVALUATE\n- Identify the user task, agent/model decision points, tools, context dependencies, outputs, and irreversible actions.\n- Recover real failures from tests, issues, incidents, traces, support notes, and prior regressions.\n- Define explicit success, acceptable degradation, and failure criteria.\n\n2. BUILD AN EVAL PYRAMID\n- deterministic unit/contract checks first;\n- synthetic integration cases second;\n- model/judge evaluation only where deterministic oracles cannot express quality;\n- human or operator review only where judgment remains genuinely irreducible.\nDo not spend model tokens to verify facts code can verify exactly.\n\n3. CREATE REPRESENTATIVE CASES\nInclude normal cases, edge cases, malformed tool/API responses, missing context, conflicting instructions, timeout/fallback conditions, and regressions drawn from actual failures. Use sanitized fixtures.\n\n4. MAKE SCORING REPRODUCIBLE\n- version fixtures and rubrics;\n- separate correctness from style;\n- record false-positive/false-negative risks;\n- preserve baseline and candidate results;\n- make failures attributable to a case and criterion.\n\n5. ENFORCE THE GATE\nWire the focused eval into the owning validator or CI lane. A regression must fail closed unless the repository explicitly records an approved threshold change with evidence. Never weaken a case merely to make a candidate pass.\n\n6. DELIVER\nImplement the eval files, fixtures, validator/report, tests, and CI wiring that fit the repository's existing patterns. Run them, commit them, push/update the PR, and report the exact proof level reached.\n\nFINAL RESPONSE\n- evaluated surface\n- cases and failure classes\n- deterministic vs model/judge layers\n- files/artifacts\n- baseline/candidate result\n- validation\n- commit/PR\n- remaining blind spots\n- exact next command""",
        "keywords": ["evals", "evaluation framework", "ai evals", "agent evals", "regression eval", "judge model", "quality gate", "golden cases", "evaluation harness", "repo eval framework"],
    },
    {
        "id": "P68",
        "seq": "68",
        "name": "Context Engineering System Refactorer",
        "type": "BUILD + FACTOR",
        "class": "AI ENGINEERING / CONTEXT",
        "sprintRole": "Treat prompts, tools, retrieval, memory, history, and token budgets as one engineered information system",
        "progress": "YES",
        "useWhen": "An AI system is slow, expensive, distracted, inconsistent, or repeatedly misinterprets work because context is bloated, duplicated, stale, poorly routed, or loaded indiscriminately.",
        "inspectFirst": "System prompts, prompt registry, skills, tool schemas, retrieval/chunking, memory, conversation history, context loaders, token/latency telemetry, cache behavior, agent routing, and known misinterpretations.",
        "expectedOutput": "A context map and budget, measured baseline, deterministic routing/pruning changes, tests for context selection and precedence, reduced unnecessary context load, and preserved task quality.",
        "nextStep": "Run the representative context-selection test and measured before/after token or byte budget, then repair the largest remaining unnecessary context source without degrading task correctness.",
        "proofGate": "Every loaded context source has a purpose and owner; deterministic routing replaces default prompt bloat where practical; precedence is explicit; measured context reduction preserves required behavior; and no hidden context dependency is claimed away without tests.",
        "color": "Purple",
        "copySheet": "P68_COPY_SAFE",
        "category": "standard",
        "copyContent": """ENGINEER THE FULL CONTEXT SYSTEM AROUND THE MODEL. DO NOT TREAT THIS AS PROMPT-WORDING POLISH.\nRepo: xyz_repo_or_path\nAgent/model entry point: xyz_ai_surface\nPrimary context pain: xyz_context_problem\n\nMISSION\nMap and refactor the information system feeding the model: system instructions, task prompt, tool definitions, retrieved chunks, memory, conversation history, repository maps, skills, and runtime state. Reduce distraction and token/latency cost without removing information required for correctness.\n\n1. INVENTORY CONTEXT SOURCES\nFor every source record owner, trigger, size, freshness, precedence, consumers, and whether it is always loaded or demand-loaded.\n\n2. MEASURE THE BASELINE\nCapture prompt/context bytes or tokens, retrieval counts, tool-schema load, latency/cost when available, and representative task success. Separate measured facts from estimates.\n\n3. PRUNE AND ROUTE\n- disable or defer tools irrelevant to the active lane;\n- load skills only when their trigger matches;\n- replace repeated prose with schemas, maps, registries, validators, or deterministic lookups;\n- bound history and retrieval;\n- remove duplicated authority;\n- preserve explicit precedence and safety instructions.\n\n4. DESIGN FOR FINITE CONTEXT\nUse compact repository maps, targeted retrieval, stable identifiers, summaries with provenance, caching where safe, and clear invalidation rules. Do not rely on the model to remember facts the system can retrieve deterministically.\n\n5. TEST CONTEXT SELECTION\nAdd cases proving required context is present, irrelevant context is excluded, stale context loses to current repository evidence, conflicting authorities resolve correctly, and reduced context does not degrade the representative task.\n\n6. DELIVER MEASURED IMPROVEMENT\nImplement the smallest reusable context-routing changes, validators, and telemetry. Report baseline/candidate deltas and any quality tradeoff. Never optimize token count alone.\n\nFINAL RESPONSE\n- context map\n- baseline and candidate load\n- sources removed/deferred\n- routing/precedence changes\n- quality regression checks\n- files/commit/PR\n- remaining context debt\n- exact next command""",
        "keywords": ["context engineering", "context window", "context pruning", "token pruning", "system prompt bloat", "tool schema bloat", "retrieval", "memory", "context routing", "token budget"],
    },
    {
        "id": "P69",
        "seq": "69",
        "name": "Production Agent Reliability Hardener",
        "type": "HARNESS + BUILD",
        "class": "AI ENGINEERING / AGENT RELIABILITY",
        "sprintRole": "Harden an agent like a distributed system: retries, idempotency, degradation, bounded state, and failure-path proof",
        "progress": "YES",
        "useWhen": "An agent works in demos or happy paths but must survive malformed APIs, timeouts, duplicate actions, provider/tool failures, partial state, concurrency, or high-stakes execution.",
        "inspectFirst": "Agent loop/state machine, tool adapters, retries/timeouts, queues, idempotency keys, persistence, error taxonomy, rollback/compensation, traces, production incidents, safety boundaries, and failure-path tests.",
        "expectedOutput": "Implemented reliability controls, explicit failure taxonomy, idempotent or compensating mutations, bounded retries/timeouts, fallback/degradation paths, observability, fault-injection tests, and operator recovery guidance.",
        "nextStep": "Execute the highest-risk synthetic failure scenario against the hardened path and repair any duplicate, stuck, silent, or unsafe transition it exposes.",
        "proofGate": "Retries are bounded, mutations are idempotent or compensating, malformed responses fail safely, partial state is recoverable, fallbacks reduce capability without inflating proof, and synthetic failure injection passes before live-risk claims.",
        "color": "Green",
        "copySheet": "P69_COPY_SAFE",
        "category": "standard",
        "copyContent": """HARDEN THIS AGENT FOR PRODUCTION FAILURE MODES. TREAT IT LIKE A DISTRIBUTED SYSTEM WITH A NON-DETERMINISTIC COMPONENT.\nRepo: xyz_repo_or_path\nAgent/runtime: xyz_agent_runtime\nHighest-risk action: xyz_agent_risk\n\nMISSION\nMake the agent survive bad tools, malformed API responses, timeouts, duplicate requests, partial failures, restarts, and degraded providers without silently corrupting state or claiming success.\n\n1. DRAW THE STATE AND FAILURE MODEL\nIdentify states, transitions, side effects, external dependencies, retryable/non-retryable failures, irreversible mutations, and recovery points.\n\n2. BOUND EVERY EXTERNAL CALL\nDefine timeout, retry policy, backoff, cancellation, validation, and error classification. Never retry an unsafe mutation blindly.\n\n3. MAKE SIDE EFFECTS SAFE\nUse idempotency keys, deduplication, compare-and-set, transactional boundaries, or explicit compensation where appropriate. Persist enough state to resume or disposition interrupted work.\n\n4. DEGRADE GRACEFULLY\nWhen a model, tool, API, or optional subsystem fails, preserve the highest safe capability that remains. Lower capability must lower the proof claim.\n\n5. OBSERVE THE LOOP\nRecord structured transitions, tool-call outcomes, retry counts, latency, terminal failure reason, and artifact identifiers without leaking secrets or private payloads.\n\n6. FAULT-INJECT BEFORE TRUST\nTest malformed JSON, empty responses, rate limits, timeouts, duplicate callbacks, stale state, provider outage, tool denial, and interrupted finalization. Assert no duplicate destructive action and an actionable recovery path.\n\n7. DELIVER\nImplement the reliability controls and regression tests using existing harness patterns. Run focused failure tests before broader validation; commit and push the hardened path.\n\nFINAL RESPONSE\n- state/failure model\n- reliability controls\n- fault cases executed\n- artifacts/logging\n- validation\n- commit/PR\n- live-proof ceiling\n- exact next command""",
        "keywords": ["production agents", "agent reliability", "retries", "idempotency", "graceful degradation", "timeouts", "malformed api", "fault injection", "agent state machine", "distributed systems"],
    },
    {
        "id": "P70",
        "seq": "70",
        "name": "LLM Ops Production Readiness Builder",
        "type": "OPERATE",
        "class": "AI ENGINEERING / LLM OPS",
        "sprintRole": "Build deployment, monitoring, latency, cost, caching, fallback, and provider-resilience controls around an AI product",
        "progress": "YES",
        "useWhen": "A model-backed feature is approaching deployment or already runs for users and needs measurable reliability, latency, cost, caching, provider fallback, release, and rollback discipline.",
        "inspectFirst": "Deployment manifests, provider/model configuration, release flow, telemetry, traces, eval results, latency/error metrics, token/cost data, caches, rate limits, fallback routing, secrets boundaries, incident runbooks, and rollback path.",
        "expectedOutput": "Implemented LLM Ops controls with service objectives, telemetry, cost/latency budgets, cache policy, provider/model fallback rules, release gates, rollback/runbook artifacts, and validation that does not require unauthorized production mutation.",
        "nextStep": "Run the pre-deployment readiness gate against the exact candidate configuration and repair the first failed SLO, fallback, observability, or rollback requirement before release.",
        "proofGate": "The candidate has measurable health and cost signals, explicit latency/error budgets, safe cache rules, tested fallback behavior, secrets remain external, release/rollback gates are executable, and no deployment is claimed without actual authority and observation.",
        "color": "Orange",
        "copySheet": "P70_COPY_SAFE",
        "category": "standard",
        "copyContent": """BUILD THE LLM OPS LAYER THAT TURNS THIS AI FEATURE INTO AN OPERABLE PRODUCT.\nRepo: xyz_repo_or_path\nModel/provider/runtime: xyz_provider_runtime\nDeployment target: xyz_deployment_target\n\nMISSION\nImplement the operational controls needed to deploy and run the model-backed feature predictably: monitoring, latency, cost, caching, fallbacks, release gates, rollback, and provider failure handling. Do not deploy or touch secrets unless the task explicitly authorizes it.\n\n1. DEFINE SERVICE OBJECTIVES\nSet measurable targets or budgets for success/error rate, latency, timeouts, token/cost consumption, queue depth where relevant, and quality/eval regression. Use repository evidence rather than invented precision.\n\n2. INSTRUMENT WHAT MATTERS\nCapture model/provider, request class, latency, retries, token usage, cache hit/miss, fallback use, terminal error class, and eval/release identity. Sanitize prompts and outputs according to privacy policy.\n\n3. CONTROL COST AND LATENCY\nUse bounded context, caching with explicit invalidation/privacy rules, model routing by task need, batching where safe, and request budgets. Never trade away correctness or safety silently.\n\n4. DESIGN PROVIDER/MODEL FAILURE HANDLING\nSpecify timeouts, rate-limit behavior, fallback models/providers, circuit-breaking or cooldown, and the capability/proof reduction of each fallback. Test the path without requiring a real outage when synthetic proof is sufficient.\n\n5. RELEASE AND ROLLBACK\nTie deployment readiness to evals plus operational gates. Record exact model/config versions, canary or bounded rollout when available, rollback command/path, and incident ownership.\n\n6. VALIDATE BEFORE DEPLOYMENT\nRun configuration/static/synthetic readiness first. If production credentials or runtime authority are absent, stop at the exact gate and provide the operator action rather than claiming deployment.\n\nFINAL RESPONSE\n- SLO/budgets\n- telemetry and privacy\n- cost/latency controls\n- fallback behavior\n- release/rollback artifacts\n- validation\n- commit/PR/deployment state\n- proof ceiling\n- exact next command""",
        "keywords": ["llm ops", "llmops", "model operations", "ai operations", "latency", "token cost", "caching", "provider fallback", "model fallback", "monitoring"],
    },
    {
        "id": "P71",
        "seq": "71",
        "name": "AI Toolchain Adaptability Review + Upgrade",
        "type": "MAINTENANCE + BUILD",
        "class": "AI ENGINEERING / ADAPTABILITY",
        "sprintRole": "Keep fast-changing model and agent dependencies replaceable through contracts, adapters, compatibility proof, and bounded periodic review",
        "progress": "YES",
        "useWhen": "A repository depends on rapidly changing models, SDKs, agent frameworks, tool protocols, or provider features and needs to evolve without one-off rewrites or novelty-driven churn.",
        "inspectFirst": "Pinned dependencies, provider/model assumptions, adapters, schemas, compatibility tests, deprecation notices already recorded in-repo, open upgrade PRs, fallback paths, migration docs, and recent breakages.",
        "expectedOutput": "A bounded drift inventory, stable interface boundaries, one evidence-backed upgrade or compatibility repair when warranted, regression tests across old/new assumptions, migration/rollback notes, and a scheduled review trigger encoded in repository process where appropriate.",
        "nextStep": "Run the compatibility matrix for the highest-risk changing dependency and either land the smallest proven adapter/upgrade or record the exact evidence-backed reason to defer it.",
        "proofGate": "The repo distinguishes stable contracts from replaceable tools, upgrades are evidence-driven rather than trend-driven, compatibility tests cover the critical path, rollback or coexistence is defined, and adaptation does not silently expand production authority.",
        "color": "Gold",
        "copySheet": "P71_COPY_SAFE",
        "category": "standard",
        "copyContent": """MAKE THIS AI REPOSITORY ADAPTABLE WITHOUT CHASING EVERY NEW TOOL.\nRepo: xyz_repo_or_path\nChanging dependency or assumption: xyz_ai_dependency\nReview horizon: xyz_review_window\n\nMISSION\nReduce the cost of model, provider, SDK, framework, and tool-protocol change by strengthening stable contracts and replacing direct coupling with tested adapters. Execute one evidence-backed compatibility improvement when the repository proves it is useful.\n\n1. INVENTORY VOLATILE ASSUMPTIONS\nFind hard-coded model names, provider-specific payloads, SDK internals, tool schemas, prompt-format assumptions, unsupported APIs, and framework-specific state. Rank by critical-path risk and change frequency observed in repository evidence.\n\n2. IDENTIFY STABLE CONTRACTS\nDefine the task inputs/outputs, tool semantics, artifact schemas, error taxonomy, proof levels, and safety boundaries that should survive implementation changes. Do not abstract merely for style.\n\n3. BUILD OR REPAIR ADAPTERS\nWhere coupling is already causing churn, isolate it behind the smallest interface or registry that preserves behavior. Keep deterministic transformations in code and provider-specific configuration out of prompt prose.\n\n4. PROVE COMPATIBILITY\nRun the same representative evals against the current and candidate implementation where possible. Cover serialization, tool calls, errors, fallback, and artifact parity. Record unsupported differences explicitly.\n\n5. UPGRADE ONLY WITH EVIDENCE\nAdopt a new dependency when it closes a verified gap, removes risk, improves measurable performance/cost, or is required by deprecation/security. Do not upgrade only because the ecosystem moved.\n\n6. PLAN ROLLBACK AND REVIEW\nPreserve pinning, rollback/coexistence path, migration notes, and a lightweight recurring review trigger when change risk justifies it.\n\nFINAL RESPONSE\n- volatile assumptions\n- stable contracts\n- adapter/upgrade implemented\n- compatibility evidence\n- rollback/migration path\n- commit/PR\n- deferred changes and reason\n- exact next command""",
        "keywords": ["adaptability", "ai toolchain", "model upgrade", "provider upgrade", "agent framework", "sdk drift", "compatibility", "adapter", "deprecation", "toolchain review"],
    },
]

registry = {
    "schema_version": "prompt-registry-extension/v1",
    "registry_id": "ai-engineering-level-up-prompts",
    "prompts": prompts,
}
write_json(ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json", registry)

# Register the extension in the canonical combined builder.
builder_registry = ROOT / "scripts/build_prompt_kit_registry.py"
replace_once(
    builder_registry,
    '    REPO_ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json",\n',
    '    REPO_ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json",\n'
    '    REPO_ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json",\n',
)

# Search aliases and visible production-AI doctrine.
builder = ROOT / "build_prompt_kit.py"
replace_once(
    builder,
    '    "context to artifact": "P56", "create artifact": "P56",\n}',
    '    "context to artifact": "P56", "create artifact": "P56",\n'
    '    "ai engineering": "P67 P68 P69 P70 P71", "ai engineering level up": "P67 P68 P69 P70 P71",\n'
    '    "evals": "P67", "evaluation framework": "P67", "agent evals": "P67",\n'
    '    "context engineering": "P68", "context pruning": "P68", "token pruning": "P68",\n'
    '    "production agents": "P69", "agent reliability": "P69", "idempotency": "P69",\n'
    '    "llm ops": "P70", "llmops": "P70", "provider fallback": "P70",\n'
    '    "adaptability": "P71", "ai toolchain": "P71", "model upgrade": "P71",\n'
    '}',
)

doctrine_block = '''        "ai_engineering": {
            "title": "Production AI Engineering Doctrine",
            "subtitle": "Five repository disciplines for moving from an AI demo to an operable system",
            "sections": [
                {"heading": "The Five Disciplines", "content":
                 "1. **Evals** - define executable quality gates before regressions reach users.\\n"
                 "2. **Context engineering** - design the complete information system around the model, not only the first prompt.\\n"
                 "3. **Production agents** - engineer retries, idempotency, degradation, recovery, and failure paths like a distributed system.\\n"
                 "4. **LLM Ops** - operate deployment, monitoring, latency, cost, caching, fallbacks, and rollback as product infrastructure.\\n"
                 "5. **Adaptability** - isolate fast-changing models and tools behind stable contracts and compatibility proof."},
                {"heading": "Evals Before Confidence", "content":
                 "A model or agent feature is not production-ready because its happy path works. Repositories should encode representative success cases, real regressions, malformed-input cases, and failure conditions as repeatable evals. Deterministic oracles run before model judges. Human judgment is reserved for criteria code cannot express. A skipped eval is not a pass."},
                {"heading": "Context Is a System", "content":
                 "Context includes system instructions, task prompts, tool schemas, retrieved chunks, memory, history, repository maps, skills, and runtime state. Every loaded source should have an owner, trigger, precedence, freshness rule, and measurable cost. Prefer demand-loading and deterministic routing over always-on prompt bloat. Optimize context only when required task quality remains intact."},
                {"heading": "Agents Need Reliability Engineering", "content":
                 "Production agents must tolerate malformed tool responses, timeouts, duplicate requests, restarts, partial failures, and degraded providers. External calls need bounded timeouts and retries. Side effects need idempotency or compensation. State transitions and terminal failures need observable evidence. Fault injection should precede high-risk runtime trust."},
                {"heading": "LLM Ops Is Product Infrastructure", "content":
                 "Model-backed products need measurable health, latency/error budgets, token and cost visibility, privacy-aware caching, provider/model fallback policy, release identity, rollback, and incident ownership. Evals and operational gates meet at deployment readiness. Configuration proof does not become production proof until the real target is authorized and observed."},
                {"heading": "Adapt Without Chasing Novelty", "content":
                 "Models, SDKs, agent frameworks, and tool protocols change quickly. Keep volatile implementations replaceable by stabilizing task contracts, schemas, tool semantics, proof vocabulary, and safety boundaries. Upgrade when evidence shows a verified gap, deprecation, security need, or measurable benefit. Preserve compatibility tests and rollback instead of performing one-off rewrites."},
                {"heading": "Repository Maturity Loop", "content":
                 "Use P67 to establish evals, P68 to engineer context, P69 to harden agent reliability, P70 to build operational readiness, and P71 to keep the stack replaceable. These prompts are complementary, not a mandatory waterfall: start at the repository's largest verified gap, preserve dependency order, and re-run evals after every material context, runtime, or dependency change."},
            ],
        },
'''
replace_once(
    builder,
    '            ],\n        },\n    }\n\n\nCSS_TEXT = r"""',
    '            ],\n        },\n' + doctrine_block + '    }\n\n\nCSS_TEXT = r"""',
)

# Guided web tutorial route: add one option without increasing questionnaire length.
guided = ROOT / "docs/prompt-kit-guided-recommendations.js"
replace_once(
    guided,
    "  {id:'build',label:'Implement a bounded change',queries:['implement','build','sprint']},\n",
    "  {id:'build',label:'Implement a bounded change',queries:['implement','build','sprint']},\n"
    "  {id:'ai-level-up',label:'Level up an AI/agent repository for production',queries:['ai engineering level up','evals','context engineering','production agents','llm ops','adaptability']},\n",
)

# Guided prompt-finder fallback knows the five new routes too.
tutorial_registry_path = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
tutorial_registry = json.loads(tutorial_registry_path.read_text(encoding="utf-8"))
p65 = next(item for item in tutorial_registry["prompts"] if item["id"] == "P65")
route_anchor = "- P66 Repository Work Ledger Steward: establish, adopt, contribute to, or repair a repository-owned human/agent work ledger without creating competing authority."
route_text = route_anchor + "\n" + "\n".join([
    "- P67 Repository Eval Framework Builder: create repository-wide AI/agent evals and regression gates.",
    "- P68 Context Engineering System Refactorer: reduce context bloat and engineer prompts/tools/retrieval/memory as one system.",
    "- P69 Production Agent Reliability Hardener: add retries, idempotency, degradation, recovery, and fault-injection proof.",
    "- P70 LLM Ops Production Readiness Builder: build monitoring, latency/cost, caching, fallback, release, and rollback controls.",
    "- P71 AI Toolchain Adaptability Review + Upgrade: isolate volatile models/frameworks behind stable contracts and compatibility tests.",
])
if route_anchor not in p65["copyContent"]:
    raise SystemExit("P65 routing-map anchor not found")
p65["copyContent"] = p65["copyContent"].replace(route_anchor, route_text, 1)
for keyword in ["ai engineering", "ai repository level up", "evals", "context engineering", "production agents", "llm ops", "adaptability"]:
    if keyword not in p65["keywords"]:
        p65["keywords"].append(keyword)
write_json(tutorial_registry_path, tutorial_registry)

# Promote the five tracks near repeated-friction recovery so they are discoverable without renumbering.
order_path = ROOT / "registry/prompts/prompt-display-order.v1.json"
order = json.loads(order_path.read_text(encoding="utf-8"))
ids = [pid for pid in order["promoted_prompt_ids"] if pid not in {"P67", "P68", "P69", "P70", "P71"}]
anchor_index = ids.index("P13") + 1 if "P13" in ids else min(5, len(ids))
for offset, pid in enumerate(["P67", "P68", "P69", "P70", "P71"]):
    ids.insert(anchor_index + offset, pid)
order["promoted_prompt_ids"] = ids
order["rationale"] = "Promote guided entry, repository intake, work-ledger continuity, repeated-friction recovery, the five production-AI engineering tracks, common execution, diagnosis, validation, closeout, planning, and tutorial discovery without renumbering stable prompt identities. All unlisted prompts retain numeric sequence order."
write_json(order_path, order)

# Reference panel: variables, prompt-sequence cards, and one grouped class legend.
reference_path = ROOT / "docs/reference.json"
reference = json.loads(reference_path.read_text(encoding="utf-8"))
existing_vars = {item.get("variable") for item in reference.get("variables", [])}
for variable, meaning, example in [
    ("xyz_ai_surface", "model, agent, workflow, or AI-enabled product surface under evaluation", "support-agent tool loop / retrieval answerer"),
    ("xyz_eval_risks", "known quality failures, regressions, or task classes the eval system must cover", "wrong tool choice; malformed response; stale retrieval"),
    ("xyz_context_problem", "context-system symptom to measure and repair", "tool-schema bloat / stale retrieval / oversized history"),
    ("xyz_agent_runtime", "agent loop, service, worker, or orchestrator being hardened", "triage agent worker / background tool executor"),
    ("xyz_provider_runtime", "model/provider/runtime combination subject to LLM Ops controls", "primary model + fallback provider"),
    ("xyz_ai_dependency", "volatile model, SDK, framework, provider, or protocol under review", "agent SDK / model API / tool protocol"),
    ("xyz_review_window", "bounded evidence window for adaptability review", "last 90 days / current release cycle"),
]:
    if variable not in existing_vars:
        reference.setdefault("variables", []).append({"variable": variable, "meaning": meaning, "example": example})

sequence_by_id = {item.get("promptId"): item for item in reference.get("promptSequence", [])}
sequence_entries = [
    {"seq":"67","promptId":"P67","moment":"Repository Eval Framework Builder","useItFor":"AI/agent behavior needs repository-wide quality and regression gates.","doNotUseWhen":"Only one deterministic unit test is missing and no AI-behavior eval layer is needed.","produces":"Versioned cases, oracles, reports, and executable eval gates.","gate":"Representative regressions fail closed and deterministic checks precede expensive judge/model evaluation.","then":"Use P68/P69 or the owning product repair based on what the eval exposes.","mutatesRepo":"YES","authority":"Eval fixtures, validators, reports, and CI inside owned scope","proofCeiling":"Repository eval/static/synthetic proof; no live-user quality claim unless observed.","copySafeSheet":"P67_COPY_SAFE"},
    {"seq":"68","promptId":"P68","moment":"Context Engineering System Refactorer","useItFor":"Context bloat, stale retrieval, duplicated authority, or indiscriminate tool/history loading harms quality, cost, or latency.","doNotUseWhen":"The issue is ordinary application memory unrelated to model context.","produces":"Measured context map/budget, routing/pruning changes, and context-selection regression tests.","gate":"Required information remains available while unnecessary context is measurably reduced or better routed.","then":"Re-run representative evals with P67.","mutatesRepo":"YES","authority":"Context loaders, prompt/tool registries, routing, retrieval configuration, and validators inside scope","proofCeiling":"Measured context-selection and repository test proof; provider billing/latency claims require actual telemetry.","copySafeSheet":"P68_COPY_SAFE"},
    {"seq":"69","promptId":"P69","moment":"Production Agent Reliability Hardener","useItFor":"An agent must survive timeouts, malformed tools/APIs, duplicates, partial failure, restarts, or degraded providers.","doNotUseWhen":"There is no agent loop or external side-effect boundary.","produces":"Reliability controls, failure taxonomy, recovery state, observability, and fault-injection tests.","gate":"Retries are bounded, side effects are safe, failure paths are recoverable, and synthetic faults pass.","then":"Use P70 when the hardened path is approaching deployment.","mutatesRepo":"YES","authority":"Agent runtime/harness reliability surfaces inside explicit scope","proofCeiling":"Synthetic failure-path proof until protected/live runtime is actually exercised.","copySafeSheet":"P69_COPY_SAFE"},
    {"seq":"70","promptId":"P70","moment":"LLM Ops Production Readiness Builder","useItFor":"A model-backed feature needs deployability, monitoring, latency/cost, caching, fallback, release, and rollback controls.","doNotUseWhen":"The feature is still only a local prototype with no operational path to harden.","produces":"Operational readiness controls, SLO/budgets, telemetry, fallback policy, release gates, and rollback/runbook artifacts.","gate":"Readiness is measurable and deployment remains gated by actual authority and runtime proof.","then":"Use P19/P08 for authorized deployment or live behavior proof.","mutatesRepo":"YES","authority":"Repository-owned deployment/observability/configuration/runbook surfaces; no implicit production authority","proofCeiling":"Config/static/synthetic operational readiness until real deployment is authorized and observed.","copySafeSheet":"P70_COPY_SAFE"},
    {"seq":"71","promptId":"P71","moment":"AI Toolchain Adaptability Review + Upgrade","useItFor":"Fast-moving models, SDKs, providers, frameworks, or tool protocols are causing coupling or upgrade risk.","doNotUseWhen":"No evidence-backed compatibility or lifecycle problem exists.","produces":"Volatility inventory, stable contracts/adapters, one bounded upgrade or compatibility repair, matrix proof, and rollback/migration notes.","gate":"Adaptation is evidence-driven, compatibility-tested, and reversible rather than novelty-driven.","then":"Re-run P67 evals and P70 readiness if runtime dependencies changed.","mutatesRepo":"YES","authority":"Bounded compatibility/adaptor/dependency surfaces inside scope","proofCeiling":"Compatibility and repository proof; production/provider behavior requires actual runtime evidence.","copySafeSheet":"P71_COPY_SAFE"},
]
for entry in sequence_entries:
    if entry["promptId"] in sequence_by_id:
        sequence_by_id[entry["promptId"]].update(entry)
    else:
        reference.setdefault("promptSequence", []).append(entry)
reference["promptSequence"] = sorted(reference.get("promptSequence", []), key=lambda item: int(str(item.get("seq", "9999"))))
reference["classLegend"] = [item for item in reference.get("classLegend", []) if item.get("promptIds") != "P67-P71"]
reference.setdefault("classLegend", []).append({
    "promptType": "AI ENGINEERING LEVEL-UP",
    "promptClass": "EVALS / CONTEXT / AGENT RELIABILITY / LLM OPS / ADAPTABILITY",
    "promptIds": "P67-P71",
    "whenToUse": "Move an AI/agent repository from demo-level confidence toward production engineering maturity",
    "progressUse": "YES",
    "proofGate": "Each discipline produces executable repository evidence and preserves its proof ceiling",
    "fillRole": "Production AI maturity",
    "fillHex": "#A7F3D0",
    "color": "Mint",
    "meaning": "Five complementary tracks: evaluate behavior, engineer context, harden agents, operate model infrastructure, and keep volatile dependencies replaceable.",
})
write_json(reference_path, reference)

# Five-module tutorial pack plus machine-readable map.
tutorial_root = ROOT / "docs/tutorials/ai-engineering-level-up"
tutorial_root.mkdir(parents=True, exist_ok=True)
manifest = {
    "schema_version": "ai-engineering-level-up-tutorial/v1",
    "tutorial_id": "ai-engineering-repository-level-up",
    "title": "Production AI Engineering: Five Repository Level-Up Tracks",
    "modules": [
        {"order":1,"prompt_id":"P67","slug":"evals","path":"docs/tutorials/ai-engineering-level-up/01-evals.md","completion_gate":"A representative eval suite fails on a known bad case and passes on the current intended behavior."},
        {"order":2,"prompt_id":"P68","slug":"context-engineering","path":"docs/tutorials/ai-engineering-level-up/02-context-engineering.md","completion_gate":"Context selection is mapped, measured, and regression-tested; unnecessary always-loaded context is reduced without quality loss."},
        {"order":3,"prompt_id":"P69","slug":"production-agents","path":"docs/tutorials/ai-engineering-level-up/03-production-agents.md","completion_gate":"At least one high-risk synthetic failure path proves bounded retries, safe side effects, and actionable recovery."},
        {"order":4,"prompt_id":"P70","slug":"llm-ops","path":"docs/tutorials/ai-engineering-level-up/04-llm-ops.md","completion_gate":"The exact candidate configuration has measurable readiness gates, fallback behavior, and rollback without claiming unauthorized deployment."},
        {"order":5,"prompt_id":"P71","slug":"adaptability","path":"docs/tutorials/ai-engineering-level-up/05-adaptability.md","completion_gate":"The highest-risk volatile dependency is behind a tested stable contract or has an evidence-backed deferral with rollback/migration notes."},
    ],
    "recommended_loop": ["P67", "P68", "P69", "P70", "P71", "P67"],
    "proof_rule": "Do not treat completion of one module as production proof for another module. Re-run evals after material context, runtime, provider, or dependency changes.",
}
write_json(tutorial_root / "tutorial-manifest.v1.json", manifest)

(tutorial_root / "README.md").write_text("""# Production AI Engineering: Five Repository Level-Up Tracks

This tutorial pack turns five useful AI-engineering ideas into repository work that can be inspected, tested, committed, and reviewed. The goal is not a title or compensation claim; it is to make AI-enabled repositories more reliable and easier to operate.

## Choose the largest verified gap

| Track | Prompt | Start here when | Durable result |
|---|---|---|---|
| Evals | P67 | quality is anecdotal or regressions escape | executable cases, oracles, reports, CI gates |
| Context engineering | P68 | prompts/tools/retrieval/history are bloated or stale | measured context map, routing/pruning, context tests |
| Production agents | P69 | the happy path works but failures are fragile | idempotency, bounded retries, recovery, fault tests |
| LLM Ops | P70 | the feature must be deployable and operable | SLOs, telemetry, cost/latency controls, fallback, rollback |
| Adaptability | P71 | models/SDKs/frameworks change faster than the repo can absorb | stable contracts, adapters, compatibility proof |

The tracks are complementary, not a rigid waterfall. A new repo may start with P67. A deployed repo with provider incidents may need P70 first. A sprawling agent harness may get the largest immediate gain from P68.

## Maturity loop

1. **Evaluate** the real task and known failure modes.
2. **Engineer context** so the model receives the right information, not all information.
3. **Harden agent execution** against distributed-system failure modes.
4. **Operate the model layer** with measurable reliability, latency, cost, fallback, and rollback.
5. **Adapt deliberately** as providers, models, frameworks, and tool protocols change.
6. **Re-run evals** after material changes.

## Repository rule

Every track should end in tracked artifacts and an executable gate. Prose alone is not completion when the behavior is machine-checkable. Static and synthetic proof must remain distinct from live or production proof.
""", encoding="utf-8")

modules = {
"01-evals.md": """# 1. Evals — turn quality into an executable contract

**Prompt:** P67 Repository Eval Framework Builder

## Goal
Build a small eval suite around the repository's real user tasks before adding more agent complexity.

## Walkthrough
1. Pick one high-value task and write down what a correct result means.
2. Collect one normal case, one edge case, one known regression, and one malformed/failure case.
3. Use deterministic assertions first: schema, exact fields, files, commands, tool choice, or invariants.
4. Add model/judge scoring only for criteria such as usefulness or semantic completeness that deterministic code cannot represent well.
5. Emit a machine-readable result and wire the focused suite into CI.
6. Deliberately run a known-bad fixture and prove the gate fails.

## What to avoid
- counting unit tests as proof of model quality;
- spending LLM tokens on exact checks code can perform;
- changing the rubric and the candidate in the same unreviewed step;
- hiding skipped judge/human evidence as a pass.

## Completion gate
A representative eval suite fails on a known bad case and passes on the intended behavior, with the proof ceiling stated explicitly.
""",
"02-context-engineering.md": """# 2. Context engineering — design the information system around the model

**Prompt:** P68 Context Engineering System Refactorer

## Goal
Make every piece of model context intentional: prompts, tool definitions, retrieved chunks, memory, history, repo maps, skills, and runtime state.

## Walkthrough
1. Inventory every context source and record owner, trigger, size, freshness, and precedence.
2. Measure the baseline context bytes/tokens and representative task success.
3. Identify always-loaded material that is lane-specific, duplicated, stale, or deterministic.
4. Demand-load skills and tools, bound history/retrieval, and move deterministic facts into registries/maps/validators.
5. Add tests proving required context remains present and stale/irrelevant context is excluded.
6. Compare before/after context load and task quality.

## What to avoid
- pruning security or precedence rules because they consume tokens;
- optimizing token count while silently reducing correctness;
- letting multiple files claim the same authority;
- assuming a larger context window removes the need for routing.

## Completion gate
Context selection is measured and regression-tested, and unnecessary always-loaded context is reduced or better routed without representative quality loss.
""",
"03-production-agents.md": """# 3. Production agents — harden the non-happy path

**Prompt:** P69 Production Agent Reliability Hardener

## Goal
Treat the agent loop as a distributed system whose components include non-deterministic models and unreliable external tools.

## Walkthrough
1. Draw states, side effects, external calls, and recovery points.
2. Classify failures as retryable, terminal, compensating, or operator-required.
3. Add bounded timeouts/backoff and never blindly retry destructive mutations.
4. Make side effects idempotent or provide explicit compensation.
5. Persist enough state to resume or disposition interrupted work.
6. Instrument transitions, tool outcomes, retries, latency, and terminal reason.
7. Fault-inject malformed responses, timeouts, duplicates, stale state, and provider/tool failures.

## What to avoid
- retry loops with no budget;
- treating process exit as successful task completion;
- duplicate external mutations after restart;
- fallback paths that keep a high proof claim after capability is reduced.

## Completion gate
A high-risk synthetic failure path proves bounded retries, safe side effects, recoverable state, and an actionable terminal failure record.
""",
"04-llm-ops.md": """# 4. LLM Ops — make model behavior operable

**Prompt:** P70 LLM Ops Production Readiness Builder

## Goal
Build the operational layer around model-backed behavior: deployment readiness, monitoring, latency, cost, caching, provider fallback, release identity, and rollback.

## Walkthrough
1. Define measurable latency/error/cost/quality budgets from available evidence.
2. Instrument provider/model identity, latency, retries, tokens, cache behavior, fallback, and terminal errors.
3. Bound context and choose cache rules with explicit privacy/invalidation behavior.
4. Test rate limits, provider failure, fallback routing, and reduced-capability behavior.
5. Tie the release gate to evals plus operational readiness.
6. Record exact model/config identity and rollback/runbook actions.
7. Stop at the production-access gate unless credentials and deployment authority are explicitly present.

## What to avoid
- logging raw sensitive prompts by default;
- provider fallback that changes capability without changing proof claims;
- optimizing latency/cost without a quality regression gate;
- reporting configuration readiness as a successful deployment.

## Completion gate
The exact candidate configuration has measurable readiness checks, tested fallback behavior, and a rollback path; production remains a separate observed gate.
""",
"05-adaptability.md": """# 5. Adaptability — isolate churn behind stable contracts

**Prompt:** P71 AI Toolchain Adaptability Review + Upgrade

## Goal
Keep fast-changing models, providers, SDKs, agent frameworks, and tool protocols replaceable without recurring repository-wide rewrites.

## Walkthrough
1. Inventory volatile assumptions and rank them by critical-path impact and observed churn.
2. Identify stable contracts: task inputs/outputs, artifact schemas, tool semantics, errors, proof levels, and safety boundaries.
3. Add a small adapter or registry only where direct coupling is already costly.
4. Run the same representative evals against current and candidate implementations.
5. Upgrade when evidence shows a real gap, deprecation/security need, or measurable benefit.
6. Preserve pinning, rollback/coexistence, and migration notes.

## What to avoid
- framework abstraction with no proven churn problem;
- unbounded "keep dependencies current" work;
- adopting a new model/tool because it is fashionable rather than useful;
- deleting the known-good path before compatibility proof exists.

## Completion gate
The highest-risk volatile dependency is behind a tested stable contract, or the repo records an evidence-backed deferral with an explicit rollback/migration path.
""",
}
for name, content in modules.items():
    (tutorial_root / name).write_text(content, encoding="utf-8")

# Focused regression test for registry/tutorial/reference/doctrine/site integration.
test_path = ROOT / "tests/test_ai_engineering_level_up.py"
test_path.write_text('''from __future__ import annotations\n\nimport json\nimport sys\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nSCRIPTS = ROOT / "scripts"\nif str(SCRIPTS) not in sys.path:\n    sys.path.insert(0, str(SCRIPTS))\n\nimport build_prompt_kit_registry\nimport build_prompt_kit\n\n\nclass AIEngineeringLevelUpTests(unittest.TestCase):\n    IDS = ("P67", "P68", "P69", "P70", "P71")\n\n    def test_effective_registry_contains_five_distinct_tracks(self) -> None:\n        prompts = build_prompt_kit_registry.load_prompt_registry()\n        by_id = {item["id"]: item for item in prompts}\n        self.assertEqual(len(by_id), len(prompts))\n        for prompt_id in self.IDS:\n            self.assertIn(prompt_id, by_id)\n            self.assertEqual(by_id[prompt_id]["progress"], "YES")\n        self.assertEqual(by_id["P67"]["class"], "AI ENGINEERING / EVALS")\n        self.assertEqual(by_id["P68"]["class"], "AI ENGINEERING / CONTEXT")\n        self.assertEqual(by_id["P69"]["class"], "AI ENGINEERING / AGENT RELIABILITY")\n        self.assertEqual(by_id["P70"]["class"], "AI ENGINEERING / LLM OPS")\n        self.assertEqual(by_id["P71"]["class"], "AI ENGINEERING / ADAPTABILITY")\n\n    def test_each_prompt_requires_executable_repository_proof(self) -> None:\n        by_id = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}\n        required = {\n            "P67": ("deterministic", "regression", "model/judge"),\n            "P68": ("context", "measure", "quality"),\n            "P69": ("idempot", "timeout", "fault"),\n            "P70": ("latency", "cost", "fallback", "rollback"),\n            "P71": ("stable contracts", "compatibility", "rollback"),\n        }\n        for prompt_id, phrases in required.items():\n            text = by_id[prompt_id]["copyContent"].lower()\n            for phrase in phrases:\n                self.assertIn(phrase.lower(), text)\n            self.assertIn("exact next command", text)\n\n    def test_prompt_finder_and_search_route_the_five_tracks(self) -> None:\n        p65 = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P65"]\n        for prompt_id in self.IDS:\n            self.assertIn(prompt_id, p65["copyContent"])\n        for keyword in ("ai engineering", "evals", "context engineering", "production agents", "llm ops", "adaptability"):\n            self.assertIn(keyword, p65["keywords"])\n        order = json.loads(build_prompt_kit_registry.DISPLAY_ORDER_POLICY.read_text(encoding="utf-8"))\n        positions = [order["promoted_prompt_ids"].index(prompt_id) for prompt_id in self.IDS]\n        self.assertEqual(positions, list(range(positions[0], positions[0] + 5)))\n\n    def test_reference_panel_maps_prompts_and_variables(self) -> None:\n        ref = json.loads((ROOT / "docs/reference.json").read_text(encoding="utf-8"))\n        seq = {item["promptId"]: item for item in ref["promptSequence"]}\n        for prompt_id in self.IDS:\n            self.assertIn(prompt_id, seq)\n            self.assertEqual(seq[prompt_id]["mutatesRepo"], "YES")\n        legend = [item for item in ref["classLegend"] if item.get("promptIds") == "P67-P71"]\n        self.assertEqual(len(legend), 1)\n        variables = {item["variable"] for item in ref["variables"]}\n        for variable in ("xyz_ai_surface", "xyz_eval_risks", "xyz_context_problem", "xyz_agent_runtime", "xyz_provider_runtime", "xyz_ai_dependency", "xyz_review_window"):\n            self.assertIn(variable, variables)\n\n    def test_doctrine_contains_all_five_production_disciplines(self) -> None:\n        doctrine = build_prompt_kit.build_doctrine()\n        self.assertIn("ai_engineering", doctrine)\n        block = doctrine["ai_engineering"]\n        self.assertEqual(block["title"], "Production AI Engineering Doctrine")\n        text = "\\n".join(section["heading"] + "\\n" + section["content"] for section in block["sections"]).lower()\n        for phrase in ("evals", "context engineering", "production agents", "llm ops", "adaptability", "p67", "p71"):\n            self.assertIn(phrase, text)\n\n    def test_tutorial_manifest_is_complete_and_prompt_mapped(self) -> None:\n        root = ROOT / "docs/tutorials/ai-engineering-level-up"\n        manifest = json.loads((root / "tutorial-manifest.v1.json").read_text(encoding="utf-8"))\n        self.assertEqual(manifest["schema_version"], "ai-engineering-level-up-tutorial/v1")\n        self.assertEqual([item["prompt_id"] for item in manifest["modules"]], list(self.IDS))\n        for module in manifest["modules"]:\n            path = ROOT / module["path"]\n            self.assertTrue(path.is_file(), path)\n            content = path.read_text(encoding="utf-8")\n            self.assertIn(module["prompt_id"], content)\n            self.assertIn("Completion gate", content)\n        readme = (root / "README.md").read_text(encoding="utf-8")\n        for prompt_id in self.IDS:\n            self.assertIn(prompt_id, readme)\n\n    def test_checked_in_site_contains_tracks_and_doctrine(self) -> None:\n        site = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")\n        for prompt_id in self.IDS:\n            self.assertIn(f'"id": "{prompt_id}"', site)\n        for phrase in (\n            "Repository Eval Framework Builder",\n            "Context Engineering System Refactorer",\n            "Production Agent Reliability Hardener",\n            "LLM Ops Production Readiness Builder",\n            "AI Toolchain Adaptability Review + Upgrade",\n            "Production AI Engineering Doctrine",\n        ):\n            self.assertIn(phrase, site)\n        self.assertEqual(site, build_prompt_kit_registry.render())\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")
