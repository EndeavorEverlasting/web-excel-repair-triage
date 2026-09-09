#!/usr/bin/env python3
"""Temporary branch carrier: add the repository SSH setup prompt through the canonical helper."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "Repository SSH Setup + Usage Completer"
REGISTRY = "ai-engineering-level-up-prompts"

COPY_CONTENT = r'''COMPLETE THIS REPOSITORY'S SSH SETUP AND PROVE IT WORKS. THEN EXPLAIN EXACTLY HOW TO USE THE VERIFIED SSH SETUP. DO NOT STOP AT INSTRUCTIONS WHEN THE CURRENT ENVIRONMENT CAN PERFORM THE SETUP.

Repository: xyz_repo_url_owner_name_or_current_repo
Access intent: xyz_read_write_read_only_or_infer_from_task
Provider/account: xyz_provider_account_or_infer
Preferred existing key: xyz_key_path_or_auto_reuse_safe_existing

MISSION
Leave the requested Git repository using a verified SSH transport path for the access actually required. Preserve existing keys, SSH config, remotes, and unrelated work. Complete every agent-capable step now. After proof, give a short shell-correct post-setup usage guide for clone/fetch/pull/push and explain what key material must never be shared.

SUCCESS
Do not claim COMPLETE until every applicable layer is proved: exact repo/root and host; SSH tool; suitable key pair; provider registration/authorization; host trust; correct SSH remote; fail-fast noninteractive repository read; safe write authorization proof when push access is required; and the post-setup usage guide. Key generation, key upload, `ssh -T`, a remote URL change, or one successful fetch alone is not enough when a stronger gate remains.

1. GROUND REPOSITORY + SHELL
- Detect OS, actual shell/runtime, current directory, Git/SSH availability, repository identity, and requested access.
- Git Bash/MSYS2 on Windows is not Linux. Never mix PowerShell cmdlets into Bash or POSIX syntax into PowerShell.
- For an existing checkout run from the proven root: `git rev-parse --show-toplevel`, `git status --short --branch`, `git branch --show-current`, `git rev-parse HEAD`, and `git remote -v`.
- Normalize repository identity without printing embedded credentials. Detect GitHub, GitLab, Bitbucket, enterprise Git, or another SSH-capable provider from evidence; do not assume GitHub.
- Preserve every unrelated remote.

2. REUSE OR CREATE KEY MATERIAL SAFELY
- Inspect the SSH directory, currently loaded identities, and relevant `~/.ssh/config` before changing anything.
- Prefer a healthy suitable existing key over creating duplicate identities.
- PUBLIC KEY (`.pub`): may be registered with the provider.
- PRIVATE KEY: never print it, paste it into chat, commit it, upload it to a repository, or expose its contents in logs.
- Never ask the operator to send a private key or passphrase in chat.
- Never overwrite an existing key file. If a new key is required, generate a modern provider-supported key such as Ed25519 at a non-colliding path; keep passphrase entry local and interactive. Do not silently create a passphrase-less key just to avoid a prompt.
- Do not delete old keys merely because a new one works.
- Load the selected identity into the platform SSH agent when required. Do not expose the passphrase. State whether loading persists across a new terminal/reboot.
- Preserve existing SSH config. Add/modify a Host stanza only when evidence requires it, such as multiple accounts/keys or a non-default identity. Do not make a global Git/SSH-policy change when a per-repository remote or Host entry is sufficient.

3. REGISTER ONLY THE PUBLIC KEY WITH THE CORRECT AUTHORITY
- Prefer an already authenticated provider CLI/API/app when it can register the public key without secret exposure.
- GitHub: an authenticated `gh` session may register the public key; never use `--show-token`, print token-bearing variables, or globally change Git protocol merely to fix one repo.
- GitLab/Bitbucket/enterprise/other: use the provider's supported account or repository mechanism. Do not assume deploy/access keys are writable; some are read-only. For ordinary developer push access, prefer the user/account SSH-key mechanism unless repo policy requires another write-capable key type.
- Never broaden permission beyond the access intent.
- If browser/OAuth/passphrase/account consent is genuinely user-only, complete all other safe steps first, then give ONE exact USER_ONLY action that registers or unlocks only the PUBLIC-key path. Resume at the first unproven layer afterward.

4. VERIFY HOST TRUST
- Do not blindly answer `yes` to an unknown-host authenticity prompt.
- For a new host, compare its fingerprint against authoritative provider evidence before storing trust.
- Treat a changed-host-key warning as BLOCKED_HOST_TRUST until reconciled. Do not delete `known_hosts` entries just to make the warning disappear.

5. CONFIGURE THIS REPO'S SSH REMOTE
- Derive the canonical SSH URL from verified provider/repository identity. Typical shapes are `git@github.com:OWNER/REPO.git`, `git@gitlab.com:OWNER/REPO.git`, and `git@bitbucket.org:WORKSPACE/REPO.git`, but use the provider's verified form.
- If `origin` already points to the correct working SSH URL, preserve it.
- If `origin` is HTTPS and SSH is the mission, change only `origin` with `git remote set-url origin <verified-ssh-url>` after the key/provider path is ready. Preserve other remotes and intentional distinct push URLs.
- Re-run `git remote get-url origin` and `git remote -v`; prove they still identify the requested repository.

6. PROVE THE TRANSPORT FAIL-FAST; NEVER LOOP PASSWORD PROMPTS
Use a bounded noninteractive read proof so bad SSH fails immediately:
- POSIX/Git Bash: `GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=8' git ls-remote --heads origin`
- PowerShell: set process-scoped `GIT_TERMINAL_PROMPT=0` and `GIT_SSH_COMMAND=ssh -o BatchMode=yes -o ConnectTimeout=8`, run `git ls-remote --heads origin`, then restore only the process variables this prompt set.
Adapt quoting to the detected shell.

Classify and repair the failing layer before retrying:
- `Permission denied (publickey)` / password fallback -> key selection/loading/provider registration/authentication.
- repository not found/access denied after SSH identity succeeds -> repository permission or wrong owner/path.
- timeout/DNS/refused connection -> BLOCKED_NETWORK_POLICY.
- host-key mismatch -> BLOCKED_HOST_TRUST.
- malformed remote -> repository identity/URL.
Do not keep asking for passwords.

`ssh -T git@github.com` may help diagnosis, but GitHub can report successful authentication with a nonzero exit because it offers no shell. Do not use that exit code alone as the oracle; prefer the repository `git ls-remote` proof.

7. PROVE WRITE AUTHORIZATION WHEN REQUIRED
- Read-only intent can close on successful bounded read proof plus verified remote/key state.
- For read-write intent, confirm a normal branch and intended target without changing remote state.
- When safe, run a non-mutating proof shaped as `git push --dry-run origin HEAD:<verified-branch>`. Do not create a remote branch, tag, commit, or force update merely to test credentials.
- If branch protection, detached HEAD, repository policy, or unavailable target prevents safe dry-run write proof, state the exact proof ceiling.
- Distinguish authentication success from authorization to push to a particular branch.

8. PRECISE BLOCKERS
Use the narrow terminal state that matches evidence:
- BLOCKED_USER_ONLY — local passphrase/browser/OAuth/account consent or another human-controlled action.
- BLOCKED_AUTHENTICATION — host rejects the available identity and no agent-capable registration path remains.
- BLOCKED_PERMISSION — SSH identity works but repository authorization is insufficient.
- BLOCKED_NETWORK_POLICY — network/VPN/firewall/proxy/DNS/port policy blocks SSH.
- BLOCKED_HOST_TRUST — provider fingerprint/change cannot be safely reconciled.
Advance every other safe setup step before stopping. Give one exact continuation action, not a generic checklist.

9. HOW TO USE THIS SSH SETUP
After success, emit this exact section heading and tailor every command to the values just proved:
`HOW TO USE THIS SSH SETUP`
Explain that normal Git commands in this repository now use SSH automatically through its configured remote; no separate SSH command is required for every pull/push. Include:
- actual verified `origin` and `git remote get-url origin`;
- shell-correct `git fetch origin`;
- the repository-appropriate pull/update command;
- `git push` or `git push -u origin <verified-branch>` only when correct for the actual upstream state;
- future clone command `git clone <verified-ssh-url>`;
- the exact bounded `git ls-remote` test to rerun if access later breaks;
- public-key and private-key paths without private contents, with: register/share the public key only; never share the private key or passphrase;
- the exact post-login/reboot key-agent action only when loading is not persistent;
- provider/branch-policy limitations separately from SSH failures.

FINAL REPORT
Report repository/root, OS/shell, provider/account when safely observable, access intent, key decision REUSED or GENERATED, public/private key paths without contents, provider registration, host trust, old/final remote, bounded read proof, write dry-run when applicable, COMPLETE or exact BLOCKED_* state, proof ceiling, `HOW TO USE THIS SSH SETUP`, and the first exact next action for the user's repository task. Use `none; no safe actionable work remains` only when SSH setup was the whole task and all applicable proof is complete.
'''

DRAFT = {
    "name": NAME,
    "type": "SETUP",
    "class": "STANDARD AI / REPOSITORY SSH TRANSPORT",
    "sprintRole": "Complete and verify repository SSH transport/authentication, then teach the operator the exact ongoing Git usage for the verified repository",
    "progress": "YES",
    "useWhen": "An existing or newly resolved Git repository needs SSH transport configured, repaired, converted from HTTPS, or proven for fetch/pull/push, and the operator also needs to know how to use the completed setup afterward.",
    "inspectFirst": "Actual OS/shell/runtime, verified repository root and remotes, Git host/provider, current branch/HEAD/status, SSH tool and key inventory, agent state, existing SSH config/known_hosts, provider authentication/key registration, access intent, repository permissions, network/policy state, and current task.",
    "expectedOutput": "A completed or precisely blocked SSH setup with preserved keys/config/remotes, verified provider registration and host trust, fail-fast repository read proof, safe write dry-run when read-write access requires it, exact remote/key evidence without secret exposure, and a tailored HOW TO USE THIS SSH SETUP guide.",
    "nextStep": "Use the now-verified SSH repository path for the requested Git/repository task; when a genuine user-only provider/passphrase/browser gate remains, perform that one exact action and resume at the first unproven SSH layer rather than restarting setup.",
    "proofGate": "Repository identity and shell are grounded; private key/passphrase contents never leave the local credential boundary; existing keys/config/remotes are preserved unless specifically owned; all applicable SSH layers are completed; `git ls-remote` succeeds noninteractively; read-write intent receives safe write-authorization proof when practical or an explicit ceiling; and the final response explains exact ongoing clone/fetch/pull/push/test usage.",
    "color": "Teal",
    "category": "standard",
    "copyContent": COPY_CONTENT,
    "keywords": [
        "ssh setup",
        "git ssh",
        "repository ssh",
        "ssh key",
        "git remote ssh",
        "github ssh",
        "gitlab ssh",
        "bitbucket ssh",
        "ssh authentication",
        "git push ssh",
        "repository transport",
        "public key private key"
    ],
}


def run() -> None:
    temp_root = Path(os.environ.get("RUNNER_TEMP", ROOT / "Outputs" / "tmp-repository-ssh-prompt"))
    temp_root.mkdir(parents=True, exist_ok=True)
    draft_path = temp_root / "repository-ssh-setup-prompt-draft.json"
    draft_path.write_text(json.dumps(DRAFT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    inspect = subprocess.run(
        [sys.executable, "scripts/prompt_registry_ops.py", "inspect"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    print("PROMPT_REGISTRY_INSPECT=" + inspect.stdout.strip())

    proc = subprocess.run(
        [sys.executable, "scripts/prompt_registry_ops.py", "add", "--input", str(draft_path), "--registry", REGISTRY],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode:
        raise SystemExit(proc.returncode)
    receipt = json.loads(proc.stdout)
    if receipt.get("status") != "added" or receipt.get("name") != NAME:
        raise SystemExit(f"unexpected prompt helper receipt: {receipt}")
    external = receipt.get("external_prior_art") or {}
    if not external.get("all_registered_sources_searched"):
        raise SystemExit("helper did not prove all registered external sources were searched")
    if external.get("automatic_prompt_authoring") is not False:
        raise SystemExit("external prior art unexpectedly gained prompt-authoring authority")
    if not external.get("distinct_residual_terms"):
        raise SystemExit("helper did not prove a distinct residual")
    sources = external.get("sources") or []
    if len(sources) < 3:
        raise SystemExit(f"expected registered donor coverage, observed {len(sources)} sources")
    print("SSH_PROMPT_HELPER_RECEIPT=" + json.dumps(receipt, sort_keys=True))

    prompt_id = str(receipt["id"])
    test_path = ROOT / "tests" / "test_repository_ssh_setup_prompt.py"
    test_path.write_text(
        f'''import unittest\n\nfrom scripts.build_prompt_kit_registry import load_prompt_registry\n\n\nclass RepositorySshSetupPromptTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.prompts = load_prompt_registry()\n        cls.prompt = next(p for p in cls.prompts if p.get("name") == {NAME!r})\n        cls.p55 = next(p for p in cls.prompts if p.get("id") == "P55")\n        cls.p61 = next(p for p in cls.prompts if p.get("id") == "P61")\n\n    def test_helper_allocated_distinct_identity_without_stealing_adjacent_owners(self):\n        self.assertEqual(self.prompt["id"], {prompt_id!r})\n        self.assertEqual(self.p55["name"], "GitHub CLI Repository Bootstrapper")\n        self.assertEqual(self.p61["name"], "Existing Repository Clone + Working-Directory Bootstrapper")\n        self.assertNotEqual(self.prompt["id"], self.p55["id"])\n        self.assertNotEqual(self.prompt["id"], self.p61["id"])\n\n    def test_ssh_owner_completes_transport_before_teaching_usage(self):\n        lower = self.prompt["copyContent"].lower()\n        required = [\n            "complete this repository's ssh setup",\n            "public key",\n            "private key",\n            "batchmode=yes",\n            "connecttimeout=8",\n            "git ls-remote --heads origin",\n            "git push --dry-run",\n            "git remote set-url origin",\n            "how to use this ssh setup",\n            "git clone <verified-ssh-url>",\n            "blocked_user_only",\n            "blocked_permission",\n            "blocked_network_policy",\n            "do not blindly answer `yes`",\n            "git bash/msys2",\n        ]\n        for phrase in required:\n            self.assertIn(phrase, lower)\n        self.assertLess(lower.index("prove the transport fail-fast"), lower.index("how to use this ssh setup"))\n\n    def test_secret_scope_and_safe_write_boundaries(self):\n        lower = self.prompt["copyContent"].lower()\n        self.assertIn("never ask the operator to send a private key or passphrase in chat", lower)\n        self.assertIn("do not make a global git/ssh-policy change", lower)\n        self.assertIn("preserve every unrelated remote", lower)\n        self.assertIn("never overwrite an existing key file", lower)\n        self.assertIn("do not delete old keys", lower)\n        self.assertIn("non-mutating proof", lower)\n        self.assertIn("do not create a remote branch, tag, commit, or force update merely to test credentials", lower)\n        self.assertIn("distinguish authentication success from authorization", lower)\n        self.assertIn("read-only intent", lower)\n        self.assertIn("read-write intent", lower)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    run()
