#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "spec-architecture-prompts"


def run(*args: str) -> str:
    cmd = [sys.executable, *args]
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    return completed.stdout


PASS1_LEDGER = [
    {
        "insight": "Create UX from product intent: information architecture, end-to-end journeys, interaction hierarchy, responsive/accessibility states, and a real representative implementation rather than screen-only mockups.",
        "current_owner": "P95 Program Design & Call-Stack Prototype Architect + P82 Prototype-Measure-Refine Delivery Loop are adjacent but do not own UX architecture.",
        "action": "ADD",
        "proof": "Dedicated UX architecture prompt with routing boundaries to P95/P82/P99.",
    },
    {
        "insight": "Emulate a strong reference UX from screenshots, a live product, or a known interface while distinguishing observed evidence from inferred hidden behavior and adapting it to the target app.",
        "current_owner": "No exact Prompt Kit owner; P82 can compare prototypes but does not own reference decomposition/fidelity.",
        "action": "ADD",
        "proof": "Reference-emulation prompt with fidelity matrix, unknowns ledger, responsive/state proof, and intentional-deviation ledger.",
    },
    {
        "insight": "Repeatedly polish a working interface until it feels sleek, sophisticated, coherent, and finished across hierarchy, spacing, typography, density, feedback, motion, microcopy, and edge states.",
        "current_owner": "P99 owns flow friction/state/telemetry; P82 owns broad experimentation. Neither owns craft-focused polish as the terminal job.",
        "action": "ADD",
        "proof": "Polish prompt with deliberate multi-pass refinement and explicit non-redesign boundary.",
    },
    {
        "insight": "Keep UX quality coherent across multiple apps through shared semantic tokens, components, interaction patterns, accessibility conventions, and centralized shortcut/command ownership without forcing every app to look identical.",
        "current_owner": "No generic cross-app product design-system prompt; workbook visual-design artifacts are domain-specific.",
        "action": "ADD",
        "proof": "Cross-app design-system prompt with theme/exception seams and migration proof.",
    },
    {
        "insight": "Prove UX is not broken across responsive layouts, keyboard/focus, touch, state transitions, reduced motion, and real browser/device geometry; static string/DOM checks cannot claim live layout acceptance.",
        "current_owner": "P94 protects change regressions and P08 owns generic runtime proof, but neither owns whole-interface UX acceptance across viewport/input matrices.",
        "action": "ADD",
        "proof": "UX acceptance prompt reusing repository browser/layout harnesses and routing broader behavior regressions to P94.",
    },
    {
        "insight": "Temporary interaction modes must not destroy unrelated state: e.g. search may hide irrelevant filters, and clearing search restores prior filter context.",
        "current_owner": "P99 User-Flow Friction & Preference Telemetry Refiner",
        "action": "ALREADY COVERED",
        "proof": "P99 already requires preserving orthogonal state and includes active-search/filter transition controls.",
    },
    {
        "insight": "Keyboard shortcuts, filter controls, Favorites, and state transitions should use centralized interaction ownership rather than ad-hoc bindings that collide or break behavior.",
        "current_owner": "P99 for user-flow semantics; existing product hotkey design/harness for Prompt Kit-specific bindings.",
        "action": "ALREADY COVERED",
        "proof": "New design-system prompt generalizes only the cross-app ownership principle; Prompt Kit's specific 1-5 bindings remain product-owned.",
    },
    {
        "insight": "Onboarding/discoverability, non-overlapping action controls, explicit success feedback, reduced motion, responsive/mobile controls, and touch-safe interaction are recurring polish/acceptance concerns.",
        "current_owner": "Current Prompt Kit product contracts prove these patterns locally but there is no reusable generic UX owner.",
        "action": "ADD",
        "proof": "The architecture/polish/acceptance prompts reuse these as bounded acceptance patterns rather than copying Prompt Kit implementation details.",
    },
    {
        "insight": "Generic iterative prototyping already exists and should not be cloned merely because UX benefits from iteration.",
        "current_owner": "P82 Prototype-Measure-Refine Delivery Loop",
        "action": "ALREADY COVERED",
        "proof": "New UX prompts route broad uncertainty to P82 instead of recreating its general prototype loop.",
    },
]


def draft(
    *,
    name: str,
    type_: str,
    class_: str,
    sprint_role: str,
    use_when: str,
    inspect_first: str,
    expected_output: str,
    next_step: str,
    proof_gate: str,
    copy_content: str,
    keywords: list[str],
) -> dict[str, object]:
    return {
        "name": name,
        "type": type_,
        "class": class_,
        "sprintRole": sprint_role,
        "useWhen": use_when,
        "inspectFirst": inspect_first,
        "expectedOutput": expected_output,
        "nextStep": next_step,
        "proofGate": proof_gate,
        "copyContent": copy_content.strip(),
        "keywords": keywords,
        "profile": "spec-architecture",
        "color": "Cyan",
        "category": "standard",
        "progress": "YES",
    }


DRAFTS = [
    draft(
        name="UX Product Designer & Interaction Architect",
        type_="DESIGN + BUILD",
        class_="PRODUCT / UX ARCHITECTURE",
        sprint_role="Turn product intent into a coherent user-experience architecture, then implement and prove the smallest representative journey before broad visual polish",
        use_when="A new app, feature, or substantial redesign needs deliberate information architecture, user journeys, interaction/state design, responsive behavior, accessibility, and component hierarchy before implementation sprawls or pixel polish begins.",
        inspect_first="Product goals and user roles; current UI/routes/components when any exist; data and actions available to users; primary and secondary journeys; current design tokens/system; responsive/mobile and keyboard constraints; accessibility requirements; analytics/support evidence; loading, empty, error, permission, offline, and destructive states; existing program-design and regression contracts.",
        expected_output="A user-job and journey map, information architecture, interaction/state model, component/action hierarchy, responsive/accessibility acceptance matrix, and a thin functional implementation of the highest-value journey with executable proof and explicit handoff to later flow refinement or polish.",
        next_step="Implement the smallest end-to-end journey that reaches terminal user value, exercise its normal and edge states across representative input/viewport modes, critique the result against the UX architecture, and repair structural defects before expanding surface area.",
        proof_gate="The primary journey reaches terminal user value without dead ends or ambiguous ownership; hierarchy and actions are understandable; normal/loading/empty/error/success/disabled/permission states are defined; keyboard/touch/responsive behavior is intentional; accessibility is not deferred to final polish; and the representative implementation passes applicable automated plus live interaction proof.",
        copy_content=r'''DESIGN AND IMPLEMENT THE UX ARCHITECTURE FOR THIS PRODUCT. DO NOT START WITH DECORATIVE PIXEL POLISH OR A SCREENSHOT-ONLY MOCKUP.

Repo/product: xyz_repo_or_product
UX surface or feature: xyz_ux_surface
Primary user outcome: xyz_user_outcome_or_resolve_from_context

MISSION
Turn the real user job into a coherent product experience: information architecture, end-to-end journeys, action hierarchy, state transitions, responsive behavior, accessibility, and reusable component seams. Build enough real UI to prove the architecture instead of leaving only boxes-and-arrows artifacts.

1. RECOVER THE USER JOB AND TERMINAL VALUE
- Identify the user, starting state, actual task, terminal useful result, frequency, risk, permissions, and failure/recovery needs.
- Trace the shortest credible primary journey from entrypoint to terminal value. Name secondary journeys only when they materially constrain the primary one.
- Inspect current product/repository truth before inventing a parallel navigation model or component system.

2. DESIGN INFORMATION ARCHITECTURE BEFORE CHROME
Define what is primary, secondary, contextual, progressive-disclosure, persistent, or hidden-by-default. Keep the first viewport focused on the user's material rather than permanent control chrome. Group actions by semantic purpose, not by whichever file or backend owns them.

3. MODEL INTERACTION STATE EXPLICITLY
For consequential surfaces define:
- initial/default;
- focused/hovered/pressed/selected;
- loading/progress;
- empty/no-results;
- success/confirmation;
- error/retry/recovery;
- disabled/permission-denied;
- destructive/undo or confirmation where relevant.
Preserve orthogonal state. A temporary mode such as search, filtering, editing, or a modal should suspend only what becomes irrelevant, not erase unrelated user intent.

4. BUILD THE COMPONENT AND ACTION HIERARCHY
Prefer deep, reusable components with clear state ownership and simple calling seams. Reuse existing design-system primitives where they fit. Define primary action, secondary actions, navigation, feedback, and keyboard/touch semantics so agents do not invent competing controls or shortcuts in every screen.

5. DESIGN RESPONSIVE + ACCESSIBLE BEHAVIOR AS CORE BEHAVIOR
Specify how navigation, content density, actions, tables/cards, dialogs, and progressive disclosure adapt across supported widths and input modes. Preserve logical reading/focus order, visible focus, keyboard completion, touch reachability, reduced-motion behavior, labels, contrast, and semantic structure. Do not treat mobile as a shrunken desktop screenshot.

6. IMPLEMENT ONE REAL VERTICAL UX SLICE
Build the smallest representative journey against actual product state/data boundaries. Avoid a fake prototype that cannot exercise loading, failure, selection, completion, or persistence. Reuse current architecture unless evidence proves a structural change is required.

7. CRITIQUE STRUCTURE BEFORE POLISH
Exercise the journey and ask: Can the user tell where they are, what matters, what action advances the job, what happened after acting, and how to recover? Repair structural confusion, stale controls, unnecessary intermediate screens, lost state, or inaccessible interactions before spending cycles on decorative polish.

8. VALIDATE
Run focused component/interaction tests plus the strongest practical live browser/runtime proof for the claims being made. Check representative viewport/input modes and the defined state matrix. Preserve already accepted behavior around the changed surface.

ROUTING BOUNDARY
- Use P95 Program Design & Call-Stack Prototype Architect when runtime modules, call-stack seams, or state ownership beneath the UX are the unresolved problem.
- Use P82 Prototype-Measure-Refine Delivery Loop when broad experimentation/alternative comparison is the primary unknown.
- Use P99 User-Flow Friction & Preference Telemetry Refiner when the product already works and the core defect is redundant steps, lost orthogonal state, or preference/usage telemetry.
- Use UX Polish & Sophistication Refiner after the UX structure works and the remaining job is craft/finish.
- Use UX Integrity & Cross-Viewport Acceptance Guard when the main job is proving the interface does not break across supported states/viewports/input modes.

DELIVER
Report the terminal user value, journey/IA, state matrix, component/action ownership, representative implementation, responsive/accessibility decisions, validation/live proof, commit/PR/merge state, and any exact unresolved user-only product decision.''',
        keywords=[
            "ux design",
            "user experience design",
            "interaction design",
            "information architecture",
            "ui architecture",
            "product design",
            "user journey",
            "responsive ux",
            "accessible interface",
            "state design",
            "component hierarchy",
            "new interface",
        ],
    ),
    draft(
        name="Reference UX Emulator & Adaptation Builder",
        type_="EMULATE + BUILD",
        class_="PRODUCT / UX REFERENCE EMULATION",
        sprint_role="Decompose a reference interface into observable design and interaction rules, adapt those rules to the target product, and prove functional responsive fidelity rather than producing a screenshot-only imitation",
        use_when="A screenshot, live site/app, mockup, competitor, prior version, or other concrete interface should be emulated or used as a strong UX reference for a target product while preserving the target's real semantics and constraints.",
        inspect_first="All available reference images/video/live routes; target product goals, data, actions, routes, existing components and design tokens; viewport/input states visible in the reference; brand/content/asset boundaries; known differences in permissions, platform, density, accessibility, and responsive behavior; existing regression and browser-proof harnesses.",
        expected_output="An observed-vs-inferred reference decomposition, fidelity matrix, extracted/adapted design tokens and interaction patterns, implemented target UX, intentional-deviation ledger, and before/after or side-by-side proof across representative states and viewports.",
        next_step="Decompose the highest-value reference journey into observed layout/interaction/state rules, implement that journey in the target product with real behavior, compare reference and candidate at matched viewports/states, and repair the largest fidelity or usability gap.",
        proof_gate="Observed reference facts are separated from inference; the target reproduces the intended hierarchy, density, actions, feedback, state behavior, and responsive logic where evidence supports them; intentional deviations are explained; no screenshot-only fake substitutes for functionality; and representative live comparison plus regressions pass without importing unauthorized assets/content.",
        copy_content=r'''EMULATE THIS REFERENCE UX IN THE TARGET PRODUCT. DECOMPOSE THE EXPERIENCE; DO NOT JUST COPY VISIBLE PIXELS.

Target repo/product: xyz_target_product
Reference: xyz_reference_url_images_or_existing_app
Target journey/surface: xyz_target_journey_or_resolve_from_context

MISSION
Use the reference as evidence for layout, visual hierarchy, interaction design, density, feedback, motion, state behavior, and responsive structure. Reproduce the useful experience in the target product while adapting it to the target's real data, actions, constraints, accessibility, and identity.

1. PIN THE REFERENCE EVIDENCE
Collect the actual screenshots, video, live routes, viewport sizes, states, and interactions available. Record what was directly observed versus what is inferred. One static screenshot does not prove hover behavior, keyboard order, responsive collapse, loading/error states, persistence, or hidden navigation.

2. BUILD A FIDELITY MATRIX
For each material surface record:
- macro layout and content order;
- spacing/density rhythm;
- typography hierarchy;
- color/contrast and semantic emphasis;
- component shapes, borders, radius, elevation, dividers;
- action placement and affordance;
- navigation and progressive disclosure;
- hover/focus/pressed/selected/disabled states;
- loading/empty/error/success feedback;
- motion/transition behavior when observed;
- responsive and mobile transformations;
- keyboard/touch behavior when observable.
Mark each item OBSERVED, INFERRED, TARGET-SPECIFIC, or INTENTIONAL DEVIATION.

3. EXTRACT RULES, NOT JUST COORDINATES
Translate recurring reference patterns into target design tokens, layout rules, component variants, and interaction contracts. Do not hard-code a pile of one-off pixel values when a stable spacing/type/component rule explains the reference better.

4. ADAPT TO THE TARGET PRODUCT
Preserve the target's actual user jobs, terminology, data shape, permissions, destructive-action safety, accessibility requirements, and platform conventions. Do not import proprietary branding, logos, copy, imagery, or other assets unless they are provided/authorized for the target. Similar interaction structure does not require pretending the target is the reference brand.

5. IMPLEMENT REAL BEHAVIOR
Wire controls to actual target state/actions. Reproduce relevant selection, search/filter, navigation, dialogs, feedback, loading/failure, and completion behavior. Do not deliver a visually similar shell whose controls are dead or whose state model collapses under real use.

6. COMPARE MATCHED STATES
Render/reference-match at the same viewport and state where possible. Compare macro geometry and hierarchy first, then typography/density/components, then motion/micro-details. Also test target-only states the reference does not expose so emulation does not create brittle missing-state behavior.

7. ITERATE TO BOUNDED FIDELITY
Use evidence-based passes: OBSERVE -> IMPLEMENT -> COMPARE -> CRITIQUE -> REFINE. Fix the highest-salience structural/interaction mismatch before tiny cosmetic deltas. Stop when the agreed fidelity/usability bar is met, remaining differences are intentional or unprovable, regressions pass, and no practical in-scope mismatch remains.

8. PROVE RESPONSIVE + INPUT BEHAVIOR
Use automated geometry/state checks where practical and real browser/runtime proof for visual/layout/focus/touch claims. Static HTML/source inspection is not proof that controls do not overlap, focus is usable, or touch behavior works.

ROUTING BOUNDARY
Use UX Product Designer & Interaction Architect when no strong reference exists and the experience must be derived primarily from product intent. Use UX Polish & Sophistication Refiner when the target structure already exists and only craft/finish remains. Use P82 for broader experimental alternatives rather than fidelity to a chosen reference. Use P94 for generic regression impact beyond the UX-specific acceptance surface.

DELIVER
Report reference evidence, observed/inferred matrix, adapted tokens/patterns, intentional deviations, implemented files, matched-state comparison, responsive/input proof, regression results, and commit/PR/merge state.''',
        keywords=[
            "emulate ux",
            "reference ux",
            "copy interface",
            "match screenshot",
            "ui emulation",
            "reference design",
            "fidelity matrix",
            "clone ux",
            "recreate interface",
            "adapt ui",
            "match app design",
            "reference implementation ux",
        ],
    ),
    draft(
        name="UX Polish & Sophistication Refiner",
        type_="REFINE + POLISH",
        class_="PRODUCT / UX POLISH",
        sprint_role="Iteratively refine a working interface until its visual hierarchy, density, component consistency, feedback, motion, microcopy, responsive behavior, and edge states feel deliberate and finished without destabilizing the product architecture",
        use_when="An interface is functionally usable but still feels rough, visually noisy, cramped, inconsistent, amateur, under-finished, awkward on some viewport/input modes, or repeatedly invites small UX tweaks after the core journey already works.",
        inspect_first="Current live interface and primary journey; design tokens/components; screenshots at representative viewports; hover/focus/pressed/disabled/loading/empty/error/success states; typography/spacing/density; action hierarchy; motion and reduced-motion behavior; responsive/mobile layout; keyboard/touch behavior; current flow/state and regression owners.",
        expected_output="A prioritized polish ledger, repeated before/after refinement passes, tightened visual and interaction consistency, completed edge-state treatment, responsive/accessibility polish, and regression/live proof showing the interface is sleeker without changing product semantics unnecessarily.",
        next_step="Walk the primary journey at representative viewport/input modes, fix the highest-salience polish defect, re-render/retest the affected states, then perform a deliberate second sweep for hierarchy, consistency, feedback, and edge-state roughness until a bounded polish fixed point.",
        proof_gate="The primary surfaces have coherent hierarchy and spacing; components and tokens are consistent; controls do not overlap or compete; feedback and edge states are intentional; keyboard/touch/reduced-motion behavior remains usable; no unrelated state is lost; live visual/layout claims are observed rather than inferred; and flow/program architecture is not gratuitously rewritten in the name of polish.",
        copy_content=r'''POLISH THIS WORKING UX UNTIL IT FEELS SLEEK, SOPHISTICATED, COHERENT, AND FINISHED. DO NOT TURN A POLISH PASS INTO AN UNBOUNDED PRODUCT REDESIGN.

Repo/product: xyz_repo_or_product
Surface/journey: xyz_ux_surface
Known roughness, if any: xyz_polish_problem

MISSION
Refine the craft of an already-working experience: hierarchy, spacing, typography, density, component consistency, affordance, feedback, motion, microcopy, responsive behavior, and edge states. Keep the product's real job and accepted semantics stable unless evidence exposes a structural defect that belongs to another owner.

1. CAPTURE THE CURRENT EXPERIENCE
Exercise the primary journey and capture representative desktop/narrow/mobile states plus important dialogs, menus, tables/cards, forms, navigation, and feedback. Record observable roughness before editing so polish is evidence-driven rather than random taste churn.

2. BUILD A POLISH LEDGER
Classify issues by:
- VISUAL HIERARCHY — emphasis, reading order, contrast, grouping;
- SPACING + DENSITY — rhythm, whitespace, crowding, line length;
- TYPOGRAPHY — scale, weight, hierarchy, truncation/wrapping;
- COMPONENT CONSISTENCY — tokens, radius, borders, elevation, icon sizing;
- ACTION AFFORDANCE — primary/secondary/destructive clarity;
- FEEDBACK — hover/focus/pressed/selected, success, confirmation, progress;
- EDGE STATES — loading, empty, no-results, error, retry, disabled, permissions;
- MOTION — purposeful transitions, no gratuitous animation, reduced-motion path;
- RESPONSIVE/INPUT — reflow, touch reachability, keyboard/focus, overflow;
- MICROCOPY — concise labels, status, errors, confirmations.
Prioritize by user salience and repeated surface area, not by easiest CSS tweak.

3. FIX SYSTEMIC ROUGHNESS FIRST
Prefer token/component/layout-rule repairs that improve several screens over scattered one-off overrides. Reuse the product's existing design system. If the same inconsistency appears across apps or many unrelated surfaces, route the shared rule to Cross-App UX Design System & Pattern Factorer rather than copying fixes everywhere.

4. PRESERVE FUNCTION AND ORTHOGONAL STATE
Polish must not silently change what actions do, erase search/filter/edit state, alter destructive semantics, duplicate event dispatch, or replace a familiar workflow merely because another layout looks prettier. When flow itself is inefficient, route to P99 rather than hiding flow debt with styling.

5. MAKE FEEDBACK FEEL COMPLETE
Every important action should have a clear before/during/after state. Avoid controls that visually activate without completing the user's goal, success messages that compete with primary content, stale selected states, and overlapping action rails. Reuse existing success/error feedback patterns instead of inventing a different toast language per screen.

6. POLISH RESPONSIVELY
Inspect more than one width and input mode. Ensure reflow preserves hierarchy and actions, text does not collide or truncate meaningfully, controls remain reachable, dialogs/menus stay in-bounds, and mobile does not simply compress desktop chrome. Preserve logical focus and reduced-motion behavior.

7. RUN DELIBERATE REFINEMENT PASSES
Use: OBSERVE -> PRIORITIZE -> REFINE -> RENDER/EXERCISE -> CRITIQUE -> KEEP/REPAIR.
After the first green pass, perform a deliberate second sweep across the full primary journey and edge states. Continue only while a practical in-scope defect is still visible or measurable; do not manufacture endless cosmetic churn after the bounded polish fixed point.

8. PROVE IT IS FINISHED, NOT JUST DIFFERENT
Run focused regressions plus the strongest practical live browser/runtime comparison. Check for overlap, clipping, hidden actions, broken focus, stale state, responsive regressions, motion/accessibility regressions, and accidental behavior changes. Screenshots can support visual comparison but do not replace interaction proof.

ROUTING BOUNDARY
Use UX Product Designer & Interaction Architect when information architecture/journey/state structure is not yet sound. Use P99 when redundant steps or lost state are the primary problem. Use P82 when meaningful alternative concepts still need experimental comparison. Use UX Integrity & Cross-Viewport Acceptance Guard when the main remaining task is durable acceptance/regression proof rather than further polish.

DELIVER
Report the polish ledger, systemic rules changed, before/after evidence, edge states completed, responsive/input checks, regressions/live proof, files, commit/PR/merge state, and any remaining issue that belongs to a different owner.''',
        keywords=[
            "ux polish",
            "ui polish",
            "polish interface",
            "sleek interface",
            "sophisticated ux",
            "visual polish",
            "interaction polish",
            "design refinement",
            "microinteractions",
            "microcopy",
            "ui cleanup",
            "finish ux",
        ],
    ),
    draft(
        name="Cross-App UX Design System & Pattern Factorer",
        type_="SYSTEM + FACTOR",
        class_="PRODUCT / DESIGN SYSTEM",
        sprint_role="Create or tighten a reusable cross-app UX language of semantic tokens, components, interaction patterns, accessibility conventions, and controlled exceptions so multiple products stay coherent without becoming identical",
        use_when="Several apps or major surfaces repeatedly reinvent spacing, typography, colors, components, responsive behavior, feedback, keyboard shortcuts, or interaction conventions and the operator wants a durable sleek cross-app system instead of repeated one-off polishing.",
        inspect_first="Existing app-specific tokens/styles/components; shared libraries/packages; screenshots and live surfaces across apps; typography/color/spacing/radius/elevation/motion conventions; component variants/states; navigation and feedback patterns; accessibility/input conventions; shortcut/command registries; theming/brand differences; build/versioning/migration constraints.",
        expected_output="A versioned semantic-token and pattern architecture, reusable component/state contracts, interaction/accessibility conventions, theme/brand extension seams, centralized command/shortcut ownership where applicable, migrated representative components in more than one relevant surface, and regression/visual proof that reuse improves consistency without flattening legitimate product differences.",
        next_step="Inventory repeated cross-app patterns, select the highest-leverage duplicated primitive, factor it into a canonical semantic token/component/interaction owner, migrate representative consumers, and prove both visual/behavioral parity plus intentional theming differences before expanding the system.",
        proof_gate="Shared semantics have one canonical owner; raw style constants and interaction rules are not needlessly duplicated; components expose complete states; accessibility/keyboard/touch conventions are reusable; themes can express legitimate app identity without forking behavior; migrations are incremental and versionable; and representative consumers prove the system in real UI rather than documentation alone.",
        copy_content=r'''FACTOR UX ACROSS THESE APPS INTO A REUSABLE DESIGN SYSTEM AND INTERACTION LANGUAGE. DO NOT FORCE EVERY PRODUCT TO LOOK IDENTICAL.

Apps/repos/surfaces: xyz_apps_or_repos
Shared UX pain: xyz_cross_app_ux_drift
Existing shared UI package/system, if any: xyz_existing_design_system

MISSION
Make repeated UX decisions durable: semantic tokens, component primitives, state variants, layout conventions, feedback, responsive behavior, accessibility, keyboard/touch semantics, and command/shortcut ownership. Preserve legitimate brand/product differences through explicit themes and extension seams instead of copy-pasted forks.

1. INVENTORY THE CURRENT DESIGN LANGUAGES
Across representative apps record typography, color semantics, spacing, density, radius, borders/elevation, iconography, motion, breakpoints, forms, tables/cards, navigation, dialogs, feedback, loading/empty/error states, focus/touch conventions, and shortcut/command patterns. Distinguish real intentional product differences from accidental drift.

2. DEFINE SEMANTIC TOKENS BEFORE COMPONENT SPRAWL
Prefer semantic concepts such as surface, text-muted, action-primary, danger, success, spacing rhythm, type roles, elevation roles, motion durations/easing, and density modes over raw values embedded across apps. Keep brand/theme values replaceable behind the semantic layer.

3. FACTOR COMPLETE COMPONENT CONTRACTS
For high-value primitives define structure, API, states, variants, accessibility semantics, responsive behavior, focus/keyboard/touch behavior, loading/empty/error treatment where relevant, and composition rules. A shared button/card/input is not useful if each app still reinvents its states and interaction meaning.

4. CENTRALIZE INTERACTION PATTERNS WHERE THEY ARE SHARED
Standardize recurring navigation, dialogs, menus, confirmation, success/error feedback, progressive disclosure, selection, search/filter semantics, and keyboard shortcuts/commands when products genuinely share them. Use a registry or canonical action owner for shortcuts when the product supports hotkeys so agents cannot introduce competing bindings ad hoc.

5. PRESERVE PRODUCT IDENTITY THROUGH CONTROLLED EXTENSION
Define what is globally invariant, themeable, product-specific, or intentionally exceptional. Do not create a universal component that needs dozens of boolean flags to represent unrelated app semantics. Prefer stable primitives plus product composition.

6. MIGRATE INCREMENTALLY
Choose one high-leverage duplicated pattern, implement/factor the canonical owner, migrate representative consumers, and remove the duplicate path only after parity/acceptance proof. Keep rollback/version compatibility when shared package changes could affect several apps.

7. PROVE THE SYSTEM IN REAL INTERFACES
Use component/unit tests, visual fixtures/snapshots when useful, accessibility checks, and live browser/runtime proof on representative consumers. Verify normal/hover/focus/pressed/disabled/loading/error states and responsive behavior. A design-system document without adopted consumers is not completion.

8. GUARD AGAINST DRIFT
Add the smallest practical lint/test/story/contract or ownership rule that prevents new raw tokens, duplicate primitives, incompatible shortcut bindings, or missing required states from silently reappearing. Do not make the guard so rigid that product-specific extension becomes impossible.

ROUTING BOUNDARY
Use UX Product Designer & Interaction Architect for one product's new experience architecture. Use UX Polish & Sophistication Refiner for local craft improvements that do not warrant shared-system changes. Use Reference UX Emulator & Adaptation Builder when an external/reference interface is the source model. Use UX Integrity & Cross-Viewport Acceptance Guard for release-grade UX acceptance across supported modes.

DELIVER
Report the inventory, canonical tokens/patterns/components, global-vs-theme-vs-product boundary, representative migrations, drift guard, visual/behavioral proof, versioning impact, files/packages, and commit/PR/merge state.''',
        keywords=[
            "design system",
            "cross app ux",
            "shared ui",
            "design tokens",
            "component library",
            "ui consistency",
            "interaction patterns",
            "semantic tokens",
            "shared components",
            "theming",
            "shortcut registry",
            "ux standards",
        ],
    ),
    draft(
        name="UX Integrity & Cross-Viewport Acceptance Guard",
        type_="VERIFY + UX ACCEPTANCE",
        class_="PRODUCT / UX ACCEPTANCE",
        sprint_role="Prove and harden an interface across viewport, browser, keyboard/focus, touch, responsive, accessibility, and composed-state transitions so a visually polished change cannot ship with broken real interaction",
        use_when="An interface, redesign, or polish pass needs release-grade proof that it is not broken across supported widths, browser/runtime geometry, keyboard/focus, touch, reduced motion, state transitions, and protected journeys, including audits where no single recent code change defines the scope.",
        inspect_first="Supported routes/journeys; viewport/browser/device targets; existing component/interaction and layout/browser-proof harnesses; protected regression behaviors; DOM/CSS/runtime state; keyboard/focus order; touch target contract; reduced-motion/accessibility rules; loading/empty/error/dialog/menu/filter/search states; screenshots or runtime receipts tied to current head.",
        expected_output="A UX acceptance matrix, automated geometry/state/sequence guards where practical, real browser/device observations for claims static tests cannot prove, repaired defects, exact-head evidence per supported mode, and a reusable acceptance gate that prevents recurrence without replacing broader P94 regression ownership.",
        next_step="Run the highest-risk representative journey through the supported viewport/input matrix using the repository's existing browser/layout harness when available, repair the first real overlap/focus/state/responsive defect, then rerun both the failing mode and impacted protected controls before broadening the matrix.",
        proof_gate="No required control/content is overlapped, clipped, inaccessible, stale, or unreachable in the tested modes; keyboard/focus order and touch interactions complete the user action; orthogonal state survives composed transitions; reduced-motion/accessibility contracts hold; live geometry/input claims are tied to the exact head and observed runtime; and static source/DOM assertions are not promoted to browser/device acceptance proof.",
        copy_content=r'''PROVE THIS UX IS NOT BROKEN ACROSS REAL VIEWPORTS, INPUT MODES, STATES, AND BROWSERS. REPAIR FAILURES; DO NOT CERTIFY FROM STATIC SOURCE INSPECTION ALONE.

Repo/product: xyz_repo_or_product
UX surface/journey: xyz_ux_surface
Supported viewport/browser/device contract: xyz_ux_acceptance_targets_or_resolve_from_repo

MISSION
Build and execute the smallest serious UX acceptance gate for the surface. Protect geometry, visibility, action completion, focus/keyboard, touch, responsive transformations, reduced motion, accessibility, and composed state transitions. Reuse the repository's existing browser/layout harness before inventing another one.

1. PIN THE ACCEPTANCE SUBJECT
Record exact candidate head/artifact, route, browser/runtime, viewport dimensions or device class, input mode, relevant feature flags/data state, and the user journey under test. Evidence from another head or materially different runtime is historical, not current proof.

2. BUILD THE MODE + STATE MATRIX
Cover representative combinations rather than every Cartesian permutation. Include as applicable:
- wide desktop, constrained desktop/tablet, narrow/mobile;
- mouse/pointer, keyboard-only, touch;
- default, search/filter/selection/editing, menu/dialog open;
- loading, empty/no-results, success, error/retry, disabled/permission states;
- reduced-motion mode;
- high-risk content lengths or dense data.
Preserve product-specific target-size contracts; where an existing app requires 40px touch targets, verify that exact contract rather than silently substituting another number.

3. AUTOMATE WHAT CAN BE PROVEN DETERMINISTICALLY
Use component/interaction tests for state transitions and event semantics; browser automation for viewport geometry, visibility, focus, keyboard action completion, dialog/menu bounds, overflow, and responsive transformations; accessibility tooling for semantic issues; visual snapshots/diffs where they catch meaningful drift. Prefer real bounding boxes/computed behavior to checking that a CSS string exists.

4. DO NOT OVERCLAIM STATIC PROOF
Static HTML/CSS/DOM/string checks can prove structure or configuration but cannot by themselves prove scrolling ergonomics, actual overlap/clipping, browser focus behavior, touch completion, rendered text collision, animation comfort, or real mobile acceptance. Obtain live/browser/device evidence for the claim being made or lower the proof ceiling explicitly.

5. PROTECT COMPOSED INTERACTION STATE
Test sequences, not only isolated controls. Examples:
- active search -> unrelated filter show/hide/toggle -> query and results remain valid;
- clear temporary mode -> prior relevant context restores when that is the product contract;
- Favorites/selection membership changes -> subordinate navigation refreshes rather than describing stale scope;
- shortcut -> terminal action occurs exactly once and normal success feedback appears;
- modal/menu -> focus enters, stays controlled where required, returns sensibly, and Escape semantics do not erase unrelated state.

6. CHECK VISUAL GEOMETRY + ACTION REACHABILITY
Fail on required content/control overlap, clipping, off-canvas primary actions, unreadable wrapping, broken sticky/fixed regions, dialogs/menus outside viewport, inaccessible scroll regions, or controls whose visible state disagrees with active application state. Test with realistic content, not only empty fixtures.

7. REPAIR AND RERUN THE IMPACTED CONTROL SET
For each defect, trace the shared layout/component/state owner, make the smallest durable repair, add a focused regression, rerun the failing mode, and rerun protected adjacent controls likely to share the same seam. Do not fix one viewport by breaking another with a one-off override.

8. CLOSE WITH EXACT-HEAD ACCEPTANCE
Attach/record the executable test results plus browser/device observations that prove the claimed modes on the exact integrated candidate. Refresh after integration; if the head or relevant layout/component dependency moves, rerun affected proof.

ROUTING BOUNDARY
Use P94 Regression Test & Live Behavior Guard when the primary job is broad change-impact regression across non-UX behavior too. Use P08 when a specific live environment/production observation is the missing proof rather than a UX acceptance matrix. Use UX Polish & Sophistication Refiner when the interface is correct but lacks craft/finish. Use P99 when the main defect is journey friction or state semantics rather than rendering/input integrity.

DELIVER
Report the acceptance matrix, exact candidate identity, automated guards, live browser/device evidence, defects repaired, impacted regression controls rerun, proof ceiling, files, and commit/PR/merge state.''',
        keywords=[
            "ux acceptance",
            "ui regression",
            "responsive testing",
            "cross viewport",
            "browser proof",
            "visual regression",
            "keyboard ux",
            "focus testing",
            "touch testing",
            "layout overlap",
            "mobile acceptance",
            "interaction integrity",
        ],
    ),
]


def add_prompts() -> list[dict[str, object]]:
    inspect = json.loads(run("scripts/prompt_registry_ops.py", "inspect"))
    print(json.dumps({"helper_inspect": inspect, "pass1_ledger": PASS1_LEDGER}, indent=2))
    receipts: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="ux-prompt-suite-") as tmp:
        tmp_path = Path(tmp)
        for index, item in enumerate(DRAFTS, start=1):
            path = tmp_path / f"{index:02d}.json"
            path.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            receipt = json.loads(
                run(
                    "scripts/prompt_registry_ops.py",
                    "add",
                    "--input",
                    str(path),
                    "--registry",
                    REGISTRY,
                )
            )
            receipts.append(receipt)
    return receipts


def patch_p65(receipts: list[dict[str, object]]) -> None:
    path = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    p65 = next(item for item in payload["prompts"] if item["id"] == "P65")
    id_by_name = {str(item["name"]): str(item["id"]) for item in receipts}

    use_sentence = (
        " It also routes the UX design lifecycle when the user is deciding whether to architect a new experience, "
        "emulate a reference, polish a working interface, factor a cross-app design system, or prove cross-viewport acceptance."
    )
    if "routes the UX design lifecycle" not in p65["useWhen"]:
        p65["useWhen"] = p65["useWhen"].rstrip() + use_sentence

    expected_sentence = (
        " For UX requests, the route distinguishes creation/interaction architecture, reference emulation, polish, "
        "cross-app design-system factoring, acceptance proof, generic prototyping, flow friction, program design, and regression ownership."
    )
    if "creation/interaction architecture" not in p65["expectedOutput"]:
        p65["expectedOutput"] = p65["expectedOutput"].rstrip() + expected_sentence

    lines = [
        f'- {id_by_name["UX Product Designer & Interaction Architect"]} UX Product Designer & Interaction Architect: create or substantially redesign the information architecture, journeys, interaction states, responsive/accessibility behavior, and representative functional UX slice.',
        f'- {id_by_name["Reference UX Emulator & Adaptation Builder"]} Reference UX Emulator & Adaptation Builder: decompose a screenshot/live/reference interface and reproduce its useful hierarchy, interaction, and responsive behavior in the target product with explicit observed-vs-inferred fidelity.',
        f'- {id_by_name["UX Polish & Sophistication Refiner"]} UX Polish & Sophistication Refiner: iteratively make an already-working interface sleeker and more finished across hierarchy, spacing, typography, density, feedback, motion, microcopy, responsive behavior, and edge states without gratuitous redesign.',
        f'- {id_by_name["Cross-App UX Design System & Pattern Factorer"]} Cross-App UX Design System & Pattern Factorer: factor repeated UX decisions across apps into semantic tokens, reusable components, interaction/accessibility conventions, themes, and centralized shortcut/command ownership.',
        f'- {id_by_name["UX Integrity & Cross-Viewport Acceptance Guard"]} UX Integrity & Cross-Viewport Acceptance Guard: prove and repair real browser/layout/focus/touch/responsive/state integrity across supported viewport and input modes when static checks are not enough.',
    ]
    routing_block = "\n".join(lines)
    if "UX Product Designer & Interaction Architect:" not in p65["copyContent"]:
        anchor = "- P95 Program Design & Call-Stack Prototype Architect: design runtime modules/seams/state ownership and prototype representative success/failure call stacks before broad implementation.\n"
        if anchor not in p65["copyContent"]:
            raise SystemExit("P65 UX routing insertion anchor missing")
        p65["copyContent"] = p65["copyContent"].replace(anchor, anchor + routing_block + "\n", 1)

    wanted_keywords = [
        "ux design",
        "user experience",
        "interaction design",
        "reference ux",
        "ui emulation",
        "ux polish",
        "design system",
        "cross app ux",
        "ux acceptance",
        "responsive ux",
        "visual regression",
    ]
    existing = {str(item).casefold() for item in p65["keywords"]}
    for keyword in wanted_keywords:
        if keyword.casefold() not in existing:
            p65["keywords"].append(keyword)
            existing.add(keyword.casefold())

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_focused_test(receipts: list[dict[str, object]]) -> None:
    ids = {str(item["name"]): str(item["id"]) for item in receipts}
    path = ROOT / "tests/test_ux_design_prompt_suite.py"
    source = f'''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
RAW_SPEC = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
RAW_DISCOVERY = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"

NAMES = {{
    "architect": "UX Product Designer & Interaction Architect",
    "emulate": "Reference UX Emulator & Adaptation Builder",
    "polish": "UX Polish & Sophistication Refiner",
    "system": "Cross-App UX Design System & Pattern Factorer",
    "accept": "UX Integrity & Cross-Viewport Acceptance Guard",
}}
EXPECTED_IDS = {json.dumps(ids, indent=4)}


class UXDesignPromptSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = {{p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}}
        cls.by_name = {{p["name"]: p for p in cls.full.values()}}
        cls.raw_spec = json.loads(RAW_SPEC.read_text(encoding="utf-8"))["prompts"]
        cls.raw_by_name = {{p["name"]: p for p in cls.raw_spec}}
        cls.policy = build_prompt_kit_registry.load_actionability_policy()

    def test_suite_has_five_distinct_helper_allocated_owners(self) -> None:
        prompts = [self.by_name[name] for name in NAMES.values()]
        self.assertEqual(len({{p["id"] for p in prompts}}), 5)
        for prompt in prompts:
            self.assertEqual(prompt["id"], EXPECTED_IDS[prompt["name"]])
            self.assertEqual(prompt["seq"], prompt["id"][1:])
            self.assertEqual(prompt["copySheet"], f"{{prompt['id']}}_COPY_SAFE")
            self.assertEqual(prompt["profile"], "spec-architecture")
            self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
            self.assertIn(self.policy["marker"], prompt["copyContent"])
            self.assertLess(len(self.raw_by_name[prompt["name"]]["copyContent"]), 8000)

    def test_architect_owns_creation_without_absorbing_program_design_or_flow_telemetry(self) -> None:
        prompt = self.by_name[NAMES["architect"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX ARCHITECTURE")
        content = prompt["copyContent"]
        for phrase in (
            "RECOVER THE USER JOB AND TERMINAL VALUE",
            "DESIGN INFORMATION ARCHITECTURE BEFORE CHROME",
            "MODEL INTERACTION STATE EXPLICITLY",
            "DESIGN RESPONSIVE + ACCESSIBLE BEHAVIOR AS CORE BEHAVIOR",
            "IMPLEMENT ONE REAL VERTICAL UX SLICE",
            "Preserve orthogonal state",
            "Use P95 Program Design & Call-Stack Prototype Architect",
            "Use P99 User-Flow Friction & Preference Telemetry Refiner",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("DERIVE THE DASHBOARD FROM EVENTS", content)
        self.assertNotIn("PROTOTYPE FAILURE CALL STACKS TOO", content)

    def test_reference_emulator_requires_observed_vs_inferred_functional_fidelity(self) -> None:
        prompt = self.by_name[NAMES["emulate"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX REFERENCE EMULATION")
        content = prompt["copyContent"]
        for phrase in (
            "PIN THE REFERENCE EVIDENCE",
            "BUILD A FIDELITY MATRIX",
            "OBSERVED, INFERRED, TARGET-SPECIFIC, or INTENTIONAL DEVIATION",
            "EXTRACT RULES, NOT JUST COORDINATES",
            "IMPLEMENT REAL BEHAVIOR",
            "COMPARE MATCHED STATES",
            "Static HTML/source inspection is not proof",
        ):
            self.assertIn(phrase, content)
        self.assertIn("unknown", prompt["proofGate"].lower())
        self.assertNotIn("Do not present a prototype as final", content)

    def test_polisher_revisits_craft_to_bounded_fixed_point_without_flow_role_collapse(self) -> None:
        prompt = self.by_name[NAMES["polish"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX POLISH")
        content = prompt["copyContent"]
        for phrase in (
            "BUILD A POLISH LEDGER",
            "VISUAL HIERARCHY",
            "COMPONENT CONSISTENCY",
            "EDGE STATES",
            "MAKE FEEDBACK FEEL COMPLETE",
            "POLISH RESPONSIVELY",
            "deliberate second sweep",
            "bounded polish fixed point",
            "route to P99 rather than hiding flow debt with styling",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("INSTRUMENT SEMANTIC USAGE, NOT NOISE", content)

    def test_design_system_factors_cross_app_rules_without_forcing_uniformity(self) -> None:
        prompt = self.by_name[NAMES["system"]]
        self.assertEqual(prompt["class"], "PRODUCT / DESIGN SYSTEM")
        content = prompt["copyContent"]
        for phrase in (
            "DEFINE SEMANTIC TOKENS BEFORE COMPONENT SPRAWL",
            "FACTOR COMPLETE COMPONENT CONTRACTS",
            "CENTRALIZE INTERACTION PATTERNS WHERE THEY ARE SHARED",
            "shortcut/command",
            "PRESERVE PRODUCT IDENTITY THROUGH CONTROLLED EXTENSION",
            "MIGRATE INCREMENTALLY",
            "GUARD AGAINST DRIFT",
        ):
            self.assertIn(phrase, content)
        self.assertIn("without becoming identical", prompt["sprintRole"])

    def test_acceptance_guard_requires_live_geometry_input_and_composed_state_proof(self) -> None:
        prompt = self.by_name[NAMES["accept"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX ACCEPTANCE")
        content = prompt["copyContent"]
        for phrase in (
            "PIN THE ACCEPTANCE SUBJECT",
            "BUILD THE MODE + STATE MATRIX",
            "DO NOT OVERCLAIM STATIC PROOF",
            "Static HTML/CSS/DOM/string checks",
            "PROTECT COMPOSED INTERACTION STATE",
            "active search -> unrelated filter show/hide/toggle",
            "clear temporary mode -> prior relevant context restores",
            "Favorites/selection membership changes",
            "shortcut -> terminal action occurs exactly once",
            "CHECK VISUAL GEOMETRY + ACTION REACHABILITY",
            "exact head",
        ):
            self.assertIn(phrase, content)
        self.assertIn("40px", content)
        self.assertIn("P94 Regression Test & Live Behavior Guard", content)

    def test_existing_iteration_flow_program_and_regression_owners_remain_distinct(self) -> None:
        for prompt_id, expected in (
            ("P82", "ENGINEERING / PROTOTYPING"),
            ("P94", "TESTING / REGRESSION"),
            ("P95", "SOFTWARE ARCHITECTURE / PROGRAM DESIGN"),
            ("P99", "PRODUCT / UX FLOW + TELEMETRY"),
        ):
            self.assertEqual(self.full[prompt_id]["class"], expected)
        self.assertIn("HYPOTHESIS -> BUILD -> MEASURE -> CRITIQUE -> DECIDE", self.full["P82"]["copyContent"])
        self.assertIn("PRESERVE ORTHOGONAL STATE", self.full["P99"]["copyContent"])
        self.assertIn("PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES", self.full["P94"]["copyContent"])
        self.assertIn("PROTOTYPE FAILURE CALL STACKS TOO", self.full["P95"]["copyContent"])

    def test_p65_routes_the_full_ux_lifecycle_without_replacing_existing_owners(self) -> None:
        raw = json.loads(RAW_DISCOVERY.read_text(encoding="utf-8"))["prompts"]
        p65 = next(p for p in raw if p["id"] == "P65")
        self.assertIn("routes the UX design lifecycle", p65["useWhen"])
        self.assertIn("creation/interaction architecture", p65["expectedOutput"])
        for name, prompt_id in EXPECTED_IDS.items():
            self.assertIn(f"{{prompt_id}} {{name}}", p65["copyContent"])
        for keyword in (
            "ux design", "interaction design", "reference ux", "ux polish",
            "design system", "ux acceptance", "responsive ux", "visual regression",
        ):
            self.assertIn(keyword, p65["keywords"])
        for existing in (
            "P82 Prototype-Measure-Refine Delivery Loop",
            "P94 Regression Test & Live Behavior Guard",
            "P99 User-Flow Friction & Preference Telemetry Refiner",
            "P95 Program Design & Call-Stack Prototype Architect",
        ):
            self.assertIn(existing, p65["copyContent"])

    def test_generated_site_is_exact_and_contains_ux_suite(self) -> None:
        expected = build_prompt_kit_registry.render()
        actual = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        for name in NAMES.values():
            self.assertIn(name, actual)


if __name__ == "__main__":
    unittest.main()
'''
    path.write_text(source, encoding="utf-8")


def pass2(receipts: list[dict[str, object]]) -> dict[str, object]:
    names = {str(item["name"]) for item in receipts}
    expected = {str(item["name"]) for item in DRAFTS}
    if names != expected:
        raise SystemExit(f"helper receipt set mismatch: {names ^ expected}")
    full = {p["name"]: p for p in __import__("scripts.build_prompt_kit_registry", fromlist=["load_prompt_kit_registry"]).load_prompt_kit_registry()}
    checks = {
        "creation owner": "DESIGN INFORMATION ARCHITECTURE BEFORE CHROME" in full["UX Product Designer & Interaction Architect"]["copyContent"],
        "reference owner": "BUILD A FIDELITY MATRIX" in full["Reference UX Emulator & Adaptation Builder"]["copyContent"],
        "polish owner": "deliberate second sweep" in full["UX Polish & Sophistication Refiner"]["copyContent"],
        "cross-app owner": "shortcut/command" in full["Cross-App UX Design System & Pattern Factorer"]["copyContent"],
        "live acceptance owner": "DO NOT OVERCLAIM STATIC PROOF" in full["UX Integrity & Cross-Viewport Acceptance Guard"]["copyContent"],
        "existing flow owner preserved": "PRESERVE ORTHOGONAL STATE" in full["User-Flow Friction & Preference Telemetry Refiner"]["copyContent"],
        "generic prototype owner preserved": "HYPOTHESIS -> BUILD -> MEASURE -> CRITIQUE -> DECIDE" in full["Prototype-Measure-Refine Delivery Loop"]["copyContent"],
        "program design owner preserved": "PROTOTYPE FAILURE CALL STACKS TOO" in full["Program Design & Call-Stack Prototype Architect"]["copyContent"],
        "regression owner preserved": "PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES" in full["Regression Test & Live Behavior Guard"]["copyContent"],
    }
    missed = [key for key, value in checks.items() if not value]
    if missed:
        raise SystemExit(f"whole-chat pass 2 found unresolved coverage defects: {missed}")
    return {
        "pass2": "bounded fixed point",
        "checks": checks,
        "missed_material_insights": [],
        "routing_decision": "Five new bounded UX owners; P82/P94/P95/P99 retained as adjacent canonical owners; P65 strengthened as lifecycle router.",
    }


def main() -> None:
    receipts = add_prompts()
    patch_p65(receipts)
    write_focused_test(receipts)
    run("scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    result = pass2(receipts)
    print(json.dumps({"helper_receipts": receipts, "whole_chat_pass2": result}, indent=2))


if __name__ == "__main__":
    main()
