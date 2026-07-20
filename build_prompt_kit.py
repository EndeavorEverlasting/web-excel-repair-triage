"""Build prompt-kit.html from prompts.json and reference.json.

Usage:
    python build_prompt_kit.py
    python build_prompt_kit.py --output web/prompt-kit/index.html
    python build_prompt_kit.py --output ../AgentSwitchboard/docs/prompt-kit.html
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "docs")
PROMPTS_PATH = os.path.join(DATA_DIR, "prompts.json")
REFERENCE_PATH = os.path.join(DATA_DIR, "reference.json")
JS_PATH = os.path.join(DATA_DIR, "prompt-kit.js")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


COLOR_HEX = {
    "slate": "#64748b", "gray": "#6b7280", "sky": "#0ea5e9", "amber": "#f59e0b",
    "blue": "#3b82f6", "green": "#22c55e", "rose": "#f43f5e", "purple": "#a855f7",
    "peach": "#fb923c", "teal": "#14b8a6", "lavender": "#8b5cf6", "cyan": "#06b6d4",
    "indigo": "#6366f1", "blue-green": "#2dd4bf", "gold": "#eab308", "sand": "#d4a574",
    "orange": "#f97316", "emerald": "#10b981", "coral": "#f87171", "ocean": "#0284c7",
    "mint": "#34d399", "night": "#1e293b", "violet": "#7c3aed", "cream": "#fef3c7",
}

SECTIONS = [
    {"name": "Foundation", "glow": "#64748b",
     "types": ["SETUP", "HARVEST", "CLOSEOUT", "CLOSEOUT + VALIDATE"]},
    {"name": "Discover & Plan", "glow": "#f59e0b",
     "types": ["DISCOVERY + BUILD", "PLAN", "PORTFOLIO PLAN", "TUTORIAL PLAN",
               "CONSOLIDATE + EXECUTE", "ANALYZE + DIRECTORY", "ANALYZE + FACTOR",
               "ANALYZE + TEST"]},
    {"name": "Build & Repair", "glow": "#22c55e",
     "types": ["BUILD", "CLEANUP", "REPAIR", "REVIEW + REPAIR", "REVIEW + BUILD",
               "BUILD + FACTOR", "BUILD + ARTIFACT", "BUILD + BOOTSTRAP",
               "BUILD + SAFETY"]},
    {"name": "Validate & Protect", "glow": "#14b8a6",
     "types": ["VALIDATE", "VALIDATE + CLOSE", "SAFETY", "RUNTIME PROOF", "IMPROVE"]},
    {"name": "Integrate & Ship", "glow": "#6366f1",
     "types": ["INTEGRATE", "INTEROP", "MAINTENANCE", "MAINTENANCE + BUILD",
               "ENABLEMENT", "ENABLEMENT + BUILD", "OPERATE", "OPPORTUNITY",
               "COMPILE ONLY", "INSTALL + ENFORCE", "ENVIRONMENT + CONFIGURE"]},
    {"name": "Autonomy & Night Shift", "glow": "#7c3aed",
     "types": ["AUTONOMY + VALIDATE", "AUTONOMY + BUILD", "AUTONOMY + PLAN",
               "AUTONOMY + PREFLIGHT", "AUTONOMY + QUEUE", "RECOVER + BUILD",
               "RECOVER + COMMIT", "HARNESS + BUILD", "HARNESS + EXECUTE",
               "CURSOR + LIVE CERT"]},
]

SYNONYMS = {
    "doctrine": "P00 P01", "repo rules": "P00 P01", "agent rules": "P00 P01",
    "harness": "P00 P01", "install harness": "P00", "build harness": "P01",
    "night shift": "P37 P38 P39 P40 P41 P42 P43 P44",
    "overnight": "P37 P38 P39 P40 P41 P42 P43 P44",
    "cleanup": "P06", "pr cleanup": "P06",
    "sprint": "P07", "implement": "P07", "code change": "P07",
    "validate": "P11", "validator": "P11", "gate": "P11",
    "closeout": "P12", "handoff": "P12", "compress": "P12",
    "merge": "P15", "release": "P15", "integrate": "P15",
    "review": "P14", "pr review": "P14",
    "documentation": "P18", "docs": "P18", "tutorial": "P18",
    "deploy": "P19", "install": "P19", "deployment": "P19",
    "dependency": "P17", "upgrade": "P17", "packages": "P17",
    "discovery": "P03", "enter repo": "P03", "unfamiliar repo": "P03",
    "plan": "P04", "distribute": "P04", "factor": "P04",
    "launch pack": "P05", "multi chat": "P05", "sprint plan": "P05",
    "opportunity": "P20", "sprint from opportunity": "P20",
    "portfolio": "P22 P23", "gap priority": "P22", "circumstance": "P23",
    "rules": "P13", "improve rules": "P13", "self improving": "P13",
    "cross repo": "P16", "interop": "P16", "contribute": "P16",
    "navigation": "P09", "code intelligence": "P09", "read only": "P09",
    "hygiene": "P10", "secrets": "P10", "hooks": "P10",
    "runtime": "P08", "live proof": "P08", "behavior proof": "P08",
    "conversation": "P02", "harvest chat": "P02",
    "consolidate": "P21", "many to one": "P21",
    "tutorial plan": "P25", "repo tutorial": "P25",
    "app coach": "P24", "usage coach": "P24",
    "spawn": "P37", "agent spawn": "P37", "preflight": "P37",
    "queue": "P30 P38", "night queue": "P38", "finite queue": "P30",
    "recovery": "P27 P43", "interrupted": "P27", "recover run": "P43",
    "cluster": "P40", "failure cluster": "P40",
    "stateful": "P41", "game safe": "P41",
    "refill": "P42", "queue refill": "P42",
    "morning": "P44", "closeout morning": "P44",
    "ci repair": "P32", "validation repair": "P32",
    "harness hardening": "P33", "harden": "P33",
    "technician": "P34", "ux": "P34",
    "pr branch": "P36", "branch repair": "P36",
    "compiler": "P45", "ai to gnhf": "P45",
    "repo harness builder": "P46",
    "harness executor": "P47", "workflow executor": "P47",
    "cursor": "P48", "live cert": "P48",
    "auto config": "P49", "environment config": "P49",
    "directory": "P50", "command guard": "P50",
    "test planner": "P51", "zero token": "P51",
    "factoring analyzer": "P52", "factoring builder": "P53",
    "local validation": "P54", "bootstrap": "P55", "github cli": "P55",
    "portable discipline": "P57", "harness discipline": "P57",
    "troubleshoot": "P58", "diagnose": "P58", "debug": "P58", "root cause": "P58",
    "artifact": "P56", "build artifact": "P56", "generate artifact": "P56",
    "context to artifact": "P56", "create artifact": "P56",
}


def build_doctrine():
    return {
        "agents": {
            "title": "Agent Operating Contract",
            "subtitle": "Universal entry point for all coding agents",
            "sections": [
                {"heading": "Required Reading Order", "content":
                 "1. `AGENTS.md`\n2. Nearest nested `AGENTS.md` governing the files in scope\n"
                 "3. `CODEBASE_MAP.md` to load the smallest relevant control-plane or harness surface\n"
                 "4. `README.md`, `CONTRIBUTING.md`, and repository-specific operating docs\n"
                 "5. The tool adapter when applicable, such as `CLAUDE.md`\n"
                 "6. `SKILLS.md`\n7. `CAPABILITIES.md`\n8. `TRIGGERS.md`\n"
                 "9. The specific skill under `.ai/skills/` selected by the trigger\n"
                 "10. Current plans, handoffs, tests, validators, open PRs, and recent Git history"},
                {"heading": "Instruction Precedence", "content":
                 "1. Platform, security, legal, and repository-owner instructions always win\n"
                 "2. A child repository's current tracked product and safety law controls work inside that child\n"
                 "3. A nested `AGENTS.md` may add or strengthen rules for its subtree\n"
                 "4. A tool adapter such as `CLAUDE.md` may explain tool-specific behavior but may not weaken this contract\n"
                 "5. A task prompt selects work; it does not silently grant capabilities forbidden by repository policy\n"
                 "6. When instructions conflict, stop the conflicting action, preserve evidence, and name the conflict"},
                {"heading": "Mandatory Operating Discipline", "content":
                 "- **Evidence before action.** Inspect the repository, current Git state, relevant contracts, and existing patterns before inventing.\n"
                 "- **Floor before furniture.** Repair unsafe repository state and shared contract gaps before dependent features.\n"
                 "- **Bound the sprint.** State owned scope, forbidden scope, expected artifacts, validation, and proof ceiling.\n"
                 "- **Isolate writers.** One branch and worktree per active writing lane. Never share uncommitted state between agents.\n"
                 "- **Reuse before replacing.** Existing healthy tools, directories, helpers, contracts, and artifacts should be used.\n"
                 "- **Separate skills from code.** Skills describe procedures and judgment. Deterministic behavior belongs in scripts, modules, validators, schemas, registries, and workflows.\n"
                 "- **Treat prompts as artifacts.** Prompts may orchestrate harness operations; they are not the harness.\n"
                 "- **Checkpoint before expansion.** Commit coherent progress before broad validation, expensive runtime proof, or scope growth.\n"
                 "- **Route failures with evidence.** Return exact command output, structured errors, and artifact paths.\n"
                 "- **Do not inflate proof.** Static checks do not prove runtime behavior; synthetic proof does not prove live-target behavior.\n"
                 "- **Protect sensitive data.** Never commit secrets, credentials, personal data, private hostnames, raw customer evidence.\n"
                 "- **Deliver tracked progress.** When safe and authorized, modify tracked files, validate, commit, push, and open or update a PR."},
                {"heading": "Required Sprint Declaration", "content":
                 "Every writing sprint must establish:\n- repository and branch\n- lane and mission\n"
                 "- owned scope\n- forbidden scope\n- dependencies and collision risks\n"
                 "- expected tracked artifacts\n- validation commands\n- proof ceiling\n- commit and PR expectation"},
                {"heading": "Capability and Authority Rule", "content":
                 "A tool may perform an action only when all four are true:\n"
                 "1. The environment exposes the capability\n"
                 "2. The capability has been verified in the current environment\n"
                 "3. The task authorizes the action\n"
                 "4. Repository policy does not forbid it\n\nCapability presence is not authority."},
                {"heading": "Completion Standard", "content":
                 "A task is complete only when the final response and repository state agree about:\n"
                 "- files changed\n- generated artifacts and their tracked/untracked policy\n"
                 "- validation actually run\n- skipped checks and exact follow-up commands\n"
                 "- commit SHA\n- push and PR state\n- remaining blockers and risks\n"
                 "- proof level and proof ceiling\n- final Git status\n- one exact next command"},
            ],
        },
        "skills": {
            "title": "Skills Catalog",
            "subtitle": "Versioned procedural knowledge for agents",
            "sections": [
                {"heading": "Skill Contract", "content":
                 "Every canonical skill must define:\n- skill ID, version, and status\n"
                 "- trigger conditions\n- required inputs\n- bounded procedure\n"
                 "- expected outputs and artifacts\n- deterministic validation\n"
                 "- stop and escalation conditions\n- forbidden scope"},
                {"heading": "Lifecycle", "content":
                 "- `proposed` - design exists but is not approved for routine use\n"
                 "- `experimental` - bounded use is allowed with explicit review\n"
                 "- `canonical` - approved baseline workflow\n"
                 "- `deprecated` - retained for migration only\n"
                 "- `retired` - must not be selected"},
                {"heading": "Canonical Skills", "content":
                 "| Skill | Purpose |\n|---|---|\n"
                 "| `repo-intake` | Recover repository truth and select safe work |\n"
                 "| `bounded-sprint` | Execute one scoped tracked change through commit/PR |\n"
                 "| `gnhf-prompt-compilation` | Compile one copy-ready bounded gnhf launch command |\n"
                 "| `evidence-validation` | Build honest proof and repair validation gaps |\n"
                 "| `pr-integration` | Reconcile stacked or parallel branches safely |\n"
                 "| `runtime-proof` | Move from static confidence to observed behavior |"},
                {"heading": "Authoring Rules", "content":
                 "- Skills must be small enough to select unambiguously\n"
                 "- Skills may reference scripts and validators but must not paste their logic\n"
                 "- Inputs and outputs should be machine-readable where practical\n"
                 "- A skill must state what it cannot prove\n"
                 "- A skill that can mutate live targets, deploy, merge, or access secrets requires an explicit escalation boundary\n"
                 "- Changes to canonical skills require a version change and validation"},
            ],
        },
        "capabilities": {
            "title": "Capability Contract",
            "subtitle": "What agents can technically do - not what they're allowed to do",
            "sections": [
                {"heading": "Capability States", "content":
                 "- `available` - the interface or command exists\n"
                 "- `verified` - a bounded probe succeeded in the current environment\n"
                 "- `constrained` - usable only within named limits\n"
                 "- `blocked` - unavailable, unsafe, unauthorized, or failing\n"
                 "- `unknown` - not yet probed\n\n"
                 "Agents must not infer `verified` from command presence, prior sessions, documentation, or another machine."},
                {"heading": "Canonical Capability Classes", "content":
                 "| Capability | Typical evidence | Default authority |\n|---|---|---|\n"
                 "| `repository.read` | files and Git history can be inspected | allowed |\n"
                 "| `repository.write` | tracked files can be modified | task-scoped |\n"
                 "| `command.execute` | local deterministic commands run | task-scoped |\n"
                 "| `network.read` | public or connected sources can be queried | task-scoped |\n"
                 "| `dependency.install` | package manager or installer works | explicit setup/repair scope |\n"
                 "| `git.commit` | commits can be created | allowed for bounded sprint |\n"
                 "| `git.push` | branch can be pushed | explicit task or repo contract |\n"
                 "| `pr.write` | PRs/comments can be created or updated | allowed when delivery requires it |\n"
                 "| `merge` | PR can be merged | blocked unless explicitly authorized |\n"
                 "| `release.deploy` | release or deployment interface exists | blocked unless explicitly authorized |\n"
                 "| `target.mutate` | external target can change | blocked unless explicitly authorized |\n"
                 "| `secrets.access` | credentials or secret stores are reachable | blocked by default |\n"
                 "| `destructive.git` | force-push, reset, branch deletion | blocked unless explicit recovery authorization |"},
                {"heading": "Authority Formula", "content":
                 "An action is permitted only when:\n\n"
                 "`verified capability + explicit task authority + repository policy + safe current state`\n\n"
                 "If any term is missing, the action is blocked or escalated."},
                {"heading": "Degradation Behavior", "content":
                 "When a capability is missing:\n- reuse a healthy alternative when the contract allows it\n"
                 "- install or repair only inside explicit setup scope\n"
                 "- record a precise skip or blocker\n- continue independent safe lanes\n"
                 "- never claim success from a fallback that provides lower proof"},
            ],
        },
        "triggers": {
            "title": "Trigger and Routing Contract",
            "subtitle": "Converts evidence or requests into reviewed skills",
            "sections": [
                {"heading": "Trigger Precedence", "content":
                 "1. Explicit owner instruction\n2. Repository safety state\n"
                 "3. Active PR/review and failing validation\n"
                 "4. Repository-local routing rules\n5. Canonical fallback mapping\n\n"
                 "Safety triggers may narrow or stop work even when a feature trigger is present."},
                {"heading": "Canonical Trigger Map", "content":
                 "| Trigger | Evidence | Route |\n|---|---|---|\n"
                 "| `repo.new-or-unknown` | unfamiliar repo, placeholder path, stale handoff | `repo-intake` |\n"
                 "| `repo.dirty-or-conflicted` | unowned changes, conflict markers, unsafe state | preserve/isolate; then `repo-intake` |\n"
                 "| `sprint.execute` | scoped request with safe owned files | `bounded-sprint` |\n"
                 "| `gnhf.prompt-request` | explicit GNHF prompt request | `gnhf-prompt-compilation` |\n"
                 "| `review.findings` | unresolved PR comments or failures | `evidence-validation` |\n"
                 "| `validation.requested` | proof gap, skipped checks, contract drift | `evidence-validation` |\n"
                 "| `integration.requested` | stacked PRs, consumed commits | `pr-integration` |\n"
                 "| `runtime.requested` | launcher, installer, behavior proof | `runtime-proof` |\n"
                 "| `docs.contract-change` | AGENTS, skills, capabilities, triggers, schemas | `bounded-sprint` + doc validator |\n"
                 "| `scope.collision` | two writers own overlapping paths | stop one lane or isolate |\n"
                 "| `secret-or-personal-data` | credentials, tokens, customer data | stop, sanitize, escalate |\n"
                 "| `live-target-mutation` | external machine, service, deployment | require explicit authority |"},
                {"heading": "Automatic Stop Triggers", "content":
                 "Stop or escalate when:\n- the task would overwrite unowned dirty work\n"
                 "- a required capability is unknown or blocked\n"
                 "- a path crosses forbidden scope\n"
                 "- a deterministic gate exposes a security or data-loss risk\n"
                 "- the next step requires merge, deployment, secrets, destructive Git, or live mutation without explicit authority\n"
                 "- repeated repair attempts exceed the workflow limit\n"
                 "- evidence contradicts the plan"},
                {"heading": "No Implicit Authority", "content":
                 "A trigger selects procedure; it does not grant authority. "
                 "The absence of a trigger does not block work that is already within scope and capability."},
            ],
        },
    }


CSS_TEXT = r"""
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg-primary:#0a0e17;--bg-secondary:#111827;--bg-card:#1a1f2e;--bg-card-hover:#232a3b;
  --bg-surface:#141a28;--border:#2a3148;--border-focus:#3b82f6;
  --text-primary:#e2e8f0;--text-secondary:#94a3b8;--text-muted:#64748b;
  --accent:#3b82f6;--accent-hover:#2563eb;--accent-glow:rgba(59,130,246,0.15);
  --success:#22c55e;--warning:#f59e0b;--danger:#ef4444;
  --radius:8px;--radius-lg:12px;--shadow:0 4px 24px rgba(0,0,0,0.3)
}
html{scroll-behavior:smooth}
body{font-family:'Inter','SF Pro Display',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.6;min-height:100vh}
.header{background:linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%);border-bottom:1px solid var(--border);padding:16px 24px 0;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}
.header-top{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-bottom:12px}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:32px;height:32px;background:linear-gradient(135deg,var(--accent),#8b5cf6);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;color:#fff;box-shadow:0 0 14px rgba(59,130,246,0.3)}
.logo h1{font-size:16px;font-weight:700;letter-spacing:-0.02em}
.logo span{font-size:11px;color:var(--text-muted);font-weight:400}
.search-container{position:relative;flex:1;max-width:400px}
.search-container input{width:100%;padding:9px 14px 9px 36px;background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius);color:var(--text-primary);font-size:13px;transition:all 0.2s}
.search-container input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow)}
.search-container input::placeholder{color:var(--text-muted)}
.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--text-muted);pointer-events:none}
.search-kbd{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:10px;color:var(--text-muted);background:var(--bg-card);padding:2px 5px;border-radius:3px;font-family:monospace;border:1px solid var(--border)}
.search-clear{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:16px;color:var(--text-muted);cursor:pointer;display:none;z-index:2;width:20px;height:20px;text-align:center;line-height:20px;border-radius:50%;transition:all 0.2s}
.search-clear:hover{color:var(--text-primary);background:var(--bg-card)}
.header-controls{display:flex;gap:12px;align-items:center}
.cat-tabs{display:flex;gap:3px;background:var(--bg-surface);padding:3px;border-radius:var(--radius)}
.cat-tab{padding:6px 14px;border-radius:5px;font-size:12px;font-weight:500;cursor:pointer;transition:all 0.2s;color:var(--text-secondary);border:none;background:none;white-space:nowrap}
.cat-tab:hover{color:var(--text-primary);background:var(--bg-card)}
.cat-tab.active{background:var(--accent);color:#fff;box-shadow:0 0 10px rgba(59,130,246,0.3)}
.cat-tab .kbd{font-size:8px;color:rgba(255,255,255,0.35);margin-left:3px;font-family:monospace}
.stats{display:flex;gap:12px;align-items:center}
.stat{text-align:center}
.stat-num{font-size:18px;font-weight:700;color:var(--accent)}
.stat-label{font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em}
.sections-nav{max-width:1400px;margin:0 auto;display:flex;gap:0;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.sections-nav::-webkit-scrollbar{display:none}
.section-tab{position:relative;padding:10px 16px;font-size:11px;font-weight:600;cursor:pointer;color:var(--text-muted);border:none;background:none;white-space:nowrap;transition:all 0.2s;text-transform:uppercase;letter-spacing:0.04em}
.section-tab:hover{color:var(--text-secondary)}
.section-tab.active{color:var(--text-primary)}
.section-tab::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;border-radius:1px 1px 0 0;transition:all 0.2s;opacity:0.3}
.section-tab.active::after{opacity:1}
.type-nav{max-width:1400px;margin:0 auto;padding:8px 0;display:flex;gap:4px;flex-wrap:wrap}
.type-chip{padding:3px 8px;font-size:10px;font-weight:500;border-radius:4px;cursor:pointer;border:1px solid transparent;transition:all 0.2s;background:var(--bg-card);color:var(--text-secondary)}
.type-chip:hover{border-color:var(--border);color:var(--text-primary)}
.type-chip.active{border-color:var(--accent);color:var(--accent);background:var(--accent-glow)}
.type-chip .dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:4px;vertical-align:middle}
.grid{max-width:1400px;margin:20px auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;padding:0 24px}
.prompt-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:16px;transition:all 0.3s;position:relative;overflow:hidden}
.prompt-card:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,0.4),0 0 20px rgba(59,130,246,0.15)}
.prompt-card:hover .glow-bar{height:4px;opacity:1;animation:glow-pulse-active 1s ease-in-out infinite}
@keyframes glow-pulse-active{0%,100%{opacity:0.7;filter:brightness(1)}50%{opacity:1;filter:brightness(1.5)}}
.prompt-card .glow-bar{position:absolute;top:0;left:0;right:0;height:3px;opacity:0.8;animation:glow-pulse 2s ease-in-out infinite;box-shadow:0 0 8px currentColor,0 0 16px currentColor}
@keyframes glow-pulse{0%,100%{opacity:0.5;filter:brightness(0.8)}50%{opacity:1;filter:brightness(1.3)}}
.prompt-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px}
.prompt-id{font-size:11px;font-weight:700;font-family:monospace;padding:2px 6px;border-radius:4px;background:var(--bg-surface);color:var(--text-muted)}
.prompt-name{font-size:13px;font-weight:600;color:var(--text-primary);flex:1;margin-left:8px}
.prompt-type{font-size:10px;color:var(--text-muted);margin-bottom:6px}
.prompt-desc{font-size:11px;color:var(--text-secondary);line-height:1.5;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.prompt-meta{display:flex;gap:8px;flex-wrap:wrap}
.prompt-badge{font-size:9px;padding:2px 6px;border-radius:3px;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border)}
.prompt-copy-btn{position:absolute;top:12px;right:12px;background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius);padding:4px 8px;font-size:10px;color:var(--text-muted);cursor:pointer;transition:all 0.2s;opacity:0}
.prompt-card:hover .prompt-copy-btn{opacity:1}
.prompt-copy-btn:hover{border-color:var(--accent);color:var(--accent)}
.prompt-copy-btn.copied{border-color:var(--success);color:var(--success)}
.prompt-card.gnhf{background:linear-gradient(145deg,#1c1710 0%,#211c13 40%,#1a1510 100%);border-color:rgba(245,158,11,0.3);box-shadow:inset 0 0 30px rgba(245,158,11,0.03)}
.prompt-card.gnhf:hover{border-color:#f59e0b;box-shadow:0 8px 32px rgba(0,0,0,0.4),0 0 24px rgba(245,158,11,0.2),inset 0 0 30px rgba(245,158,11,0.05)}
.prompt-card.gnhf .glow-bar{background:linear-gradient(90deg,#f59e0b,#fbbf24,#f59e0b) !important;box-shadow:0 0 8px rgba(245,158,11,0.6),0 0 16px rgba(245,158,11,0.3) !important}
.prompt-card.gnhf .prompt-id{background:rgba(245,158,11,0.15);color:#fbbf24;border-color:rgba(245,158,11,0.35)}
.prompt-card.gnhf .prompt-name{color:#fef3c7}
.prompt-card.gnhf .prompt-type{color:rgba(251,191,36,0.6)}
.prompt-card.gnhf .prompt-badge{border-color:rgba(245,158,11,0.2);color:rgba(251,191,36,0.7)}
.prompt-card.gnhf .gnhf-badge{display:inline-flex;align-items:center;gap:3px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.3);margin-left:6px;font-weight:600}
.prompt-card:not(.gnhf) .gnhf-badge{display:none}
.gnhf-badge{display:none}
.ref-toggle{position:fixed;bottom:24px;right:24px;background:var(--accent);color:#fff;border:none;border-radius:50%;width:48px;height:48px;font-size:20px;cursor:pointer;box-shadow:0 4px 20px rgba(59,130,246,0.4);z-index:200;transition:transform 0.2s}
.ref-toggle:hover{transform:scale(1.1)}
.ref-sidebar{position:fixed;top:0;right:-400px;width:380px;height:100vh;background:var(--bg-secondary);border-left:1px solid var(--border);z-index:150;transition:right 0.3s;overflow-y:auto;padding:20px}
.ref-sidebar.open{right:0}
.ref-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:140;display:none}
.ref-overlay.open{display:block}
.ref-section{margin-bottom:16px}
.ref-section h3{font-size:12px;color:var(--accent);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em}
.ref-item{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:8px 10px;margin-bottom:6px;font-size:11px;color:var(--text-secondary);cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:6px}
.ref-item:hover{border-color:var(--accent);color:var(--text-primary);background:var(--bg-card-hover);transform:translateX(2px)}
.ref-item .label{font-weight:600;color:var(--text-primary);font-family:monospace;font-size:10px;background:var(--bg-surface);padding:1px 5px;border-radius:3px;border:1px solid var(--border)}
.ref-item[data-prompt]::after{content:'\2192';margin-left:auto;color:var(--text-muted);font-size:12px;opacity:0;transition:opacity 0.2s}
.ref-item[data-prompt]:hover::after{opacity:1;color:var(--accent)}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--bg-card);border:1px solid var(--accent);border-radius:var(--radius);padding:8px 16px;font-size:12px;color:var(--text-primary);z-index:300;opacity:0;transition:opacity 0.3s;pointer-events:none}
.toast.show{opacity:1}
.doctrine-view{display:none;max-width:960px;margin:0 auto;padding:2rem}
.doctrine-view.active{display:block}
.doctrine-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin-bottom:1rem;transition:border-color 0.3s;cursor:pointer}
.doctrine-card:hover{border-color:var(--accent)}
.doctrine-card h3{font-size:1.1rem;color:var(--accent);margin:0 0 0.5rem}
.doctrine-card .subtitle{color:var(--text-muted);font-size:0.85rem;margin-bottom:0.5rem}
.doctrine-card .count{color:var(--text-muted);font-size:0.8rem}
.doctrine-detail{display:none}
.doctrine-detail.active{display:block}
.doctrine-back{background:none;border:1px solid var(--border);border-radius:8px;padding:0.4rem 0.8rem;color:var(--text-muted);cursor:pointer;font-size:0.8rem;margin-bottom:1rem}
.doctrine-back:hover{border-color:var(--accent);color:var(--accent)}
.doctrine-section{margin-bottom:1.25rem}
.doctrine-section h4{font-size:0.9rem;color:var(--text-primary);margin:0 0 0.5rem;padding-bottom:0.3rem;border-bottom:1px solid var(--border)}
.doctrine-section pre{background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;padding:0.75rem;font-size:0.8rem;line-height:1.5;white-space:pre-wrap;overflow-x:auto;color:var(--text-primary)}
.doctrine-section ul,.doctrine-section ol{margin:0.25rem 0;padding-left:1.5rem;font-size:0.85rem;color:var(--text-primary)}
.doctrine-section li{margin-bottom:0.25rem}
.doctrine-section table{width:100%;border-collapse:collapse;font-size:0.8rem}
.doctrine-section th,.doctrine-section td{text-align:left;padding:0.4rem 0.6rem;border:1px solid var(--border)}
.doctrine-section th{background:var(--bg-surface);color:var(--text-primary);font-weight:600}
.doctrine-section td{color:var(--text-primary)}
.doctrine-list{display:grid;gap:0.75rem}
.prompt-detail-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:250;display:none;align-items:center;justify-content:center;padding:20px}
.prompt-detail-overlay.open{display:flex}
.prompt-detail{background:var(--bg-secondary);border:1px solid var(--border);border-radius:12px;max-width:720px;width:100%;max-height:85vh;overflow-y:auto;padding:24px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.prompt-detail-close{position:absolute;top:12px;right:12px;background:none;border:none;color:var(--text-muted);font-size:20px;cursor:pointer;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:6px;transition:all 0.2s}
.prompt-detail-close:hover{background:var(--bg-card);color:var(--text-primary)}
.prompt-detail .pd-glow{height:4px;border-radius:2px;margin-bottom:16px;animation:glow-pulse 2s ease-in-out infinite}
.prompt-detail .pd-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.prompt-detail .pd-id{font-size:14px;font-weight:700;font-family:monospace;padding:4px 10px;border-radius:6px;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border)}
.prompt-detail .pd-name{font-size:18px;font-weight:700;color:var(--text-primary)}
.prompt-detail .pd-type{font-size:12px;color:var(--text-muted);margin-bottom:4px}
.prompt-detail .pd-badges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.prompt-detail .pd-badge{font-size:11px;padding:3px 8px;border-radius:4px;background:var(--bg-surface);color:var(--text-secondary);border:1px solid var(--border)}
.prompt-detail .pd-section{margin-bottom:16px}
.prompt-detail .pd-section h4{font-size:12px;color:var(--accent);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid var(--border)}
.prompt-detail .pd-section pre{background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:12px;line-height:1.6;white-space:pre-wrap;overflow-x:auto;color:var(--text-primary);font-family:'SF Mono','Fira Code',monospace}
.prompt-detail .pd-copy{display:inline-flex;align-items:center;gap:6px;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;margin-top:8px}
.prompt-detail .pd-copy:hover{background:var(--accent-hover);transform:translateY(-1px)}
.prompt-detail .pd-copy.copied{background:var(--success)}
.section-divider{grid-column:1/-1;padding:20px 0 8px;display:flex;align-items:center;gap:12px}
.section-divider .sd-line{flex:1;height:1px;background:var(--border)}
.section-divider .sd-label{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;white-space:nowrap;display:flex;align-items:center;gap:8px}
.section-divider .sd-icon{font-size:16px}
.section-divider .sd-count{font-size:10px;color:var(--text-muted);font-weight:400}
.cat-tab .tab-icon{margin-right:4px;font-size:12px}
.cat-tab[data-cat="all"]{border:1px solid rgba(226,232,240,0.2)}
.cat-tab[data-cat="all"].active{background:linear-gradient(135deg,#64748b,#94a3b8);box-shadow:0 0 12px rgba(100,116,139,0.4)}
.cat-tab[data-cat="standard"]{border:1px solid rgba(14,165,233,0.15)}
.cat-tab[data-cat="standard"].active{background:linear-gradient(135deg,#0ea5e9,#38bdf8);box-shadow:0 0 12px rgba(14,165,233,0.4)}
.cat-tab[data-cat="doctrine"]{border:1px solid rgba(139,92,246,0.15)}
.cat-tab[data-cat="doctrine"].active{background:linear-gradient(135deg,#8b5cf6,#a78bfa);box-shadow:0 0 12px rgba(139,92,246,0.4)}
.ref-toggle .ref-icon{font-size:18px}
.version-badge{position:fixed;bottom:24px;left:24px;font-size:10px;color:var(--text-muted);background:var(--bg-card);padding:4px 8px;border-radius:4px;border:1px solid var(--border);z-index:200;font-family:monospace}
.add-prompt-btn{background:var(--accent);color:#fff;border:none;border-radius:var(--radius);padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:4px}
.add-prompt-btn:hover{background:var(--accent-hover);transform:translateY(-1px);box-shadow:0 4px 12px rgba(59,130,246,0.3)}
"""


def build_html(prompts, ref):
    doctrine = build_doctrine()
    prompt_json = json.dumps(prompts, ensure_ascii=False)
    ref_json = json.dumps(ref, ensure_ascii=False)
    color_json = json.dumps(COLOR_HEX)
    sections_json = json.dumps(SECTIONS)
    synonyms_json = json.dumps(SYNONYMS)
    doctrine_json = json.dumps(doctrine, ensure_ascii=False)

    html = []
    html.append('<!DOCTYPE html>\n<html lang="en">\n<head>')
    html.append('<meta charset="UTF-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append('<title>AI Harness Prompt Kit v39</title>')
    html.append('<style>')
    html.append(CSS_TEXT)
    html.append('</style>\n</head>\n<body>')

    html.append('<div class="header">')
    html.append('  <div class="header-top">')
    html.append('    <div class="logo">')
    html.append('      <div class="logo-icon">AK</div>')
    html.append('      <div><h1>AI Harness Prompt Kit <span>v39</span></h1>'
                '<div style="font-size:10px;color:var(--text-muted)">Agent Control Panel</div></div>')
    html.append('    </div>')
    html.append('    <div class="search-container">')
    html.append('      <span class="search-icon">&#128269;</span>')
    html.append('      <input type="text" id="search" placeholder="Search prompts, types, keywords..." autocomplete="off">')
    html.append('      <span class="search-clear" id="searchClear">&times;</span>')
    html.append('      <span class="search-kbd">/</span>')
    html.append('    </div>')
    html.append('    <div class="header-controls">')
    html.append('      <div class="cat-tabs">')
    html.append('        <button class="cat-tab active" data-cat="all"><span class="tab-icon">&#128203;</span>All<span class="kbd">1</span></button>')
    html.append('        <button class="cat-tab" data-cat="standard"><span class="tab-icon">&#128196;</span>Standard<span class="kbd">2</span></button>')
    html.append('        <button class="cat-tab" data-cat="doctrine"><span class="tab-icon">&#128220;</span>Doctrine<span class="kbd">3</span></button>')
    html.append('      </div>')
    html.append('      <button class="add-prompt-btn" id="addPromptBtn">+ Add Prompt</button>')
    html.append('      <div class="stats">')
    html.append('        <div class="stat"><div class="stat-num" id="showing">0</div><div class="stat-label">Showing</div></div>')
    html.append('        <div class="stat"><div class="stat-num" id="total">0</div><div class="stat-label">Total</div></div>')
    html.append('        <div class="stat"><div class="stat-label" style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:linear-gradient(135deg,#f59e0b,#fbbf24)"></span> GNHF</div></div>')
    html.append('      </div>')
    html.append('    </div>')
    html.append('  </div>')
    html.append('  <div class="sections-nav" id="sectionsNav"></div>')
    html.append('  <div class="type-nav" id="typeNav"></div>')
    html.append('</div>')
    html.append('<div class="grid" id="grid"></div>')
    html.append('<div class="doctrine-view" id="doctrineView">')
    html.append('  <div class="doctrine-detail" id="doctrineDetail">')
    html.append('    <button class="doctrine-back" id="doctrineBack">&larr; Back to Overview</button>')
    html.append('    <div id="doctrineContent"></div>')
    html.append('  </div>')
    html.append('  <div class="doctrine-list" id="doctrineList"></div>')
    html.append('</div>')
    html.append('<div class="ref-overlay" id="refOverlay"></div>')
    html.append('<div class="ref-sidebar" id="refSidebar">')
    html.append('  <h2 style="font-size:14px;margin-bottom:16px;color:var(--accent)">&#128218; Reference Panel</h2>')
    html.append('  <div id="refContent"></div>')
    html.append('  <button id="refClose" style="position:absolute;top:16px;right:16px;background:none;border:none;color:var(--text-muted);font-size:18px;cursor:pointer">&times;</button>')
    html.append('</div>')
    html.append('<button class="ref-toggle" id="refBtn" title="Reference Panel (R)"><span class="ref-icon">&#9776;</span></button>')
    html.append('<div class="toast" id="toast"></div>')
    html.append('<div class="prompt-detail-overlay" id="promptDetailOverlay">')
    html.append('  <div class="prompt-detail" id="promptDetail"></div>')
    html.append('</div>')
    html.append('<div class="version-badge" id="versionBadge">v39</div>')

    html.append('<script>')
    html.append('var PROMPTS=' + prompt_json + ';')
    html.append('var REF=' + ref_json + ';')
    html.append('var COLORS=' + color_json + ';')
    html.append('var SECTIONS=' + sections_json + ';')
    html.append('var DOCTRINE=' + doctrine_json + ';')
    html.append('var SYNONYMS=' + synonyms_json + ';')

    with open(JS_PATH, "r", encoding="utf-8") as f:
        js_text = f.read()
    html.append(js_text)

    html.append('</script>\n</body>\n</html>')

    return '\n'.join(html)


def main():
    parser = argparse.ArgumentParser(description="Build prompt-kit.html")
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(REPO_ROOT, "web", "prompt-kit", "index.html"),
        help="Output path for the built HTML file",
    )
    args = parser.parse_args()

    prompts = load_json(PROMPTS_PATH)
    ref = load_json(REFERENCE_PATH)

    html = build_html(prompts, ref)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {args.output} ({len(html)} bytes, {len(prompts)} prompts)")


if __name__ == "__main__":
    main()
