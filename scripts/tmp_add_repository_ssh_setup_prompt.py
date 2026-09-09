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
Provider/account context: xyz_provider_account_or_infer
Preferred existing key: xyz_key_path_or_auto_reuse_safe_existing

MISSION
Leave the requested repository with a verified SSH transport path appropriate to the required access, while preserving existing keys, remotes, config, and unrelated work. Complete every agent-capable setup step now. After proof, give the operator a short, shell-correct usage guide for normal clone/fetch/pull/push work and explain what key material must never be shared.

SUCCESS MEANS ALL APPLICABLE LAYERS ARE PROVEN
1. the exact repository/root and Git host are resolved;
2. SSH tooling is available in the actual shell/runtime;
3. a suitable private/public key pair exists and the private key remains private;
4. the provider account/repository recognizes the public key with only the access needed for the task;
5. host identity/trust is valid without blindly accepting an unknown host;
6. this repository's remote is a canonical SSH URL when SSH is the intended transport;
7. a fail-fast noninteractive remote read succeeds;
8. when read-write access is required, a non-mutating push dry-run proves write authorization when branch state permits;
9. the final response explains how to use the working setup from this repository and how to clone future checkouts over SSH.
Do not claim COMPLETE from key generation, key upload, `ssh -T`, a changed remote URL, or a single successful fetch alone when a stronger applicable gate remains.

0. RESOLVE THE EXECUTION CONTEXT BEFORE EMITTING COMMANDS
- Identify OS, current shell/interpreter, current directory, Git availability, SSH availability, and the requested repository identity.
- A Bash-looking shell on Windows may be Git Bash/MSYS2, not Linux. Do not mix PowerShell cmdlets into Bash or POSIX syntax into PowerShell.
- When a local checkout is available, prove its root with `git rev-parse --show-toplevel`, then inspect `git status --short --branch`, `git branch --show-current`, `git rev-parse HEAD`, and `git remote -v` from that root.
- Normalize the remote/repository identity without printing embedded credentials. Detect GitHub, GitLab, Bitbucket, an enterprise host, or another SSH-capable Git provider from current evidence; do not assume GitHub merely because GitHub CLI exists.
- Preserve every unrelated remote. This prompt owns only the SSH transport/authentication changes required for the requested repository.

1. INSPECT BEFORE CREATING OR CHANGING KEYS
- Inspect the user's SSH directory and relevant agent state using shell-correct commands. Reuse a healthy suitable existing key when that avoids needless duplicate identities.
- Distinguish key material explicitly:
  - PUBLIC KEY: the `.pub` material may be registered with the Git provider.
  - PRIVATE KEY: never print it, paste it into chat, commit it, upload it to a repository, or expose its contents in logs.
- Never ask the operator to send a private key or passphrase in chat.
- Do not overwrite an existing key file. If a new key is necessary, generate a modern provider-supported key such as Ed25519 at a non-colliding path and keep passphrase entry local/interactively controlled. Do not silently create a passphrase-less private key merely to avoid a prompt.
- Do not delete old keys simply because a new key works.

2. MAKE THE KEY USABLE IN THE CURRENT SESSION WITHOUT DESTROYING PERSISTENT CONFIG
- Determine whether the key needs `ssh-agent`/platform key-agent loading for this shell and whether that state survives a new terminal or reboot.
- Reuse an already loaded valid identity. If loading is required and agent-capable, perform it without exposing the passphrase.
- Inspect an existing `~/.ssh/config` before editing it. Preserve all unrelated hosts/identities/comments. Add a Host stanza only when evidence shows one is needed, such as multiple accounts/keys or a non-default identity path.
- Do not make a global Git/SSH-policy change when a per-repository remote or Host entry is sufficient.

3. REGISTER THE PUBLIC KEY WITH THE CORRECT PROVIDER AUTHORITY
- Prefer an already authenticated provider CLI/API/app when it can register the public key safely without displaying secret material.
- For GitHub, an authenticated `gh` session may register the public key; do not use `--show-token` or expose token-bearing environment variables. Do not change global Git protocol merely to repair one repository.
- For Bitbucket, GitLab, enterprise Git, or another provider, use that provider's current supported account/repository key mechanism. Do not assume a repository/deploy/access key is writable: some provider key types are read-only. For ordinary developer push access, prefer the provider's user/account SSH-key mechanism unless repository policy explicitly requires a deploy key with write permission.
- If provider registration requires browser/OAuth/account consent that the agent cannot perform, advance every local step first, then present ONE exact USER_ONLY action: identify the provider screen/CLI flow and provide only the PUBLIC key to register. Resume verification after that gate; do not restart the setup.
- Never broaden repository or organization permissions beyond the requested access intent.

4. VERIFY HOST IDENTITY BEFORE FIRST-CONNECT ACCEPTANCE
- Do not blindly answer `yes` to an unknown-host authenticity prompt.
- When the host is not already trusted, obtain the expected SSH host-key fingerprint from an authoritative provider/source available to the environment and compare it before accepting/storing the host key.
- Treat a changed-host-key warning as a security/policy blocker until reconciled; do not delete known_hosts entries just to make the warning disappear.

5. CONFIGURE THIS REPOSITORY'S SSH REMOTE
- Derive the canonical SSH repository URL from verified provider/repository identity; do not guess owner/workspace/project names.
- Typical shapes include `git@github.com:OWNER/REPO.git`, `git@gitlab.com:OWNER/REPO.git`, and `git@bitbucket.org:WORKSPACE/REPO.git`, but use the provider's verified canonical form.
- If `origin` already points to the correct working SSH URL, preserve it.
- If `origin` is HTTPS and the mission is SSH, change only `origin` with `git remote set-url origin <verified-ssh-url>` after the SSH key/provider path is ready. Preserve other remotes and any intentional distinct push URL unless the task explicitly owns them.
- Re-run `git remote -v`/`git remote get-url origin` and prove the result still identifies the requested repository.

6. PROVE THE TRANSPORT FAIL-FAST; DO NOT LOOP PASSWORD PROMPTS
Use a noninteractive bounded read proof so a bad SSH setup fails instead of repeatedly asking for passwords.
- POSIX/Git Bash pattern: `GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=8' git ls-remote --heads origin`
- PowerShell pattern: set process-scoped `GIT_TERMINAL_PROMPT=0` and `GIT_SSH_COMMAND=ssh -o BatchMode=yes -o ConnectTimeout=8`, run `git ls-remote --heads origin`, then restore/remove only the process variables this prompt set.
Adapt quoting to the detected shell. Do not copy one shell's syntax into another.

Interpret failures by layer instead of retrying blindly:
- `Permission denied (publickey)` or repeated password fallback -> key selection/loading/provider registration/authentication problem.
- repository not found / access denied after successful SSH identity -> repository permission or wrong owner/path problem.
- timeout/DNS/refused connection -> network/firewall/VPN/proxy/policy problem.
- host-key mismatch -> host trust/security problem.
- malformed remote -> repository identity/URL problem.
Repair the identified layer and rerun the bounded proof.

`ssh -T git@github.com` may be a useful diagnostic, but GitHub can report successful authentication while returning a nonzero exit status because it does not provide shell access. Do not use that exit code alone as the completion oracle. Prefer an actual Git remote operation such as the bounded `git ls-remote` proof for repository access.

7. PROVE WRITE AUTHORIZATION WHEN THE TASK REQUIRES PUSH ACCESS
- Read-only intent can close on the successful bounded read proof plus the verified remote/key state.
- For read-write intent, first confirm a normal branch is checked out and determine the intended upstream/target without changing remote state.
- When safe, run a non-mutating proof shaped as `git push --dry-run origin HEAD:<verified-branch>` or the repository's equivalent. Do not create a remote branch, tag, commit, or force update merely to test credentials.
- If repository policy, branch protection, detached HEAD, or an unavailable target makes dry-run write proof inapplicable, state that exact proof ceiling rather than fabricating write success.
- Distinguish authentication success from authorization to push to a particular protected branch.

8. USER-ONLY AND EXTERNAL BLOCKERS
Classify terminal blockers precisely:
- BLOCKED_USER_ONLY — local interactive passphrase/browser/OAuth/account consent or another human-controlled action is required.
- BLOCKED_AUTHENTICATION — the host rejected the available identity and no agent-capable provider-registration path remains.
- BLOCKED_PERMISSION — SSH identity works but repository/account authorization is insufficient.
- BLOCKED_NETWORK_POLICY — DNS/firewall/VPN/proxy/port policy prevents the SSH path.
- BLOCKED_HOST_TRUST — host fingerprint/change cannot be safely reconciled.
Advance all other safe setup work before stopping at one of these gates. Provide one exact continuation action, not a generic troubleshooting list.

9. AFTER SUCCESS, EXPLAIN HOW TO USE THE VERIFIED SETUP
Do not end at `SSH works`. Teach the operator the concrete ongoing workflow using the values just proved.
Include a compact section named `HOW TO USE THIS SSH SETUP` that explains:
- Normal Git commands in this verified repository now use SSH automatically through its configured remote; there is no separate SSH command required for every push/pull.
- Show the actual verified `origin` URL and the exact command to inspect it (`git remote get-url origin`).
- Show shell-correct examples for `git fetch origin`, the repository-appropriate pull/update command, and `git push` or `git push -u origin <verified-branch>` only when appropriate to current branch/upstream state.
- Show the exact verified SSH clone URL for a future checkout: `git clone <verified-ssh-url>`.
- Show the bounded connection/read test the operator can rerun if access later breaks.
- Name the public-key path and private-key path without printing private-key contents, and say explicitly: share/register the public key only; never share the private key or passphrase.
- If agent/key loading is session-only, explain the one exact command/action required after a new login/reboot. If persistence is proven, say no manual reload is normally needed.
- Explain any provider-specific limitation that remains, such as protected-branch policy; do not confuse it with SSH failure.

FINAL REPORT
Return:
- repository and verified local root when available
- detected OS/shell
- Git provider and account identity if safely observable
- access intent
- key decision: REUSED or GENERATED, with public/private paths but never private contents
- provider registration result
- host-trust result
- old and final repository remote URL, credential material redacted
- bounded read-proof command/result
- write dry-run result when applicable
- final status: COMPLETE or the exact BLOCKED_* state
- proof ceiling
- `HOW TO USE THIS SSH SETUP` with exact values and commands
- one exact next action for the requested repository work; use `none; no safe actionable work remains` only when SSH setup itself was the entire requested task and all applicable proof is complete.
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
    "color": "Ocean",
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
        [
            sys.executable,
            "scripts/prompt_registry_ops.py",
            "add",
            "--input",
            str(draft_path),
            "--registry",
            REGISTRY,
        ],
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
        f'''import unittest\n\nfrom scripts.build_prompt_kit_registry import load_prompt_registry\n\n\nclass RepositorySshSetupPromptTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.prompts = load_prompt_registry()\n        cls.prompt = next(p for p in cls.prompts if p.get("name") == {NAME!r})\n        cls.p55 = next(p for p in cls.prompts if p.get("id") == "P55")\n        cls.p61 = next(p for p in cls.prompts if p.get("id") == "P61")\n\n    def test_helper_allocated_distinct_identity_without_stealing_adjacent_owners(self):\n        self.assertEqual(self.prompt["id"], {prompt_id!r})\n        self.assertEqual(self.p55["name"], "GitHub CLI Repository Bootstrapper")\n        self.assertEqual(self.p61["name"], "Existing Repository Clone + Working-Directory Bootstrapper")\n        self.assertNotEqual(self.prompt["id"], self.p55["id"])\n        self.assertNotEqual(self.prompt["id"], self.p61["id"])\n\n    def test_ssh_owner_completes_transport_before_teaching_usage(self):\n        text = self.prompt["copyContent"]\n        lower = text.lower()\n        required = [\n            "complete this repository's ssh setup",\n            "public key",\n            "private key",\n            "batchmode=yes",\n            "connecttimeout=8",\n            "git ls-remote --heads origin",\n            "git push --dry-run",\n            "git remote set-url origin",\n            "how to use this ssh setup",\n            "git clone <verified-ssh-url>",\n            "blocked_user_only",\n            "blocked_permission",\n            "blocked_network_policy",\n            "do not blindly answer `yes`",\n            "git bash/msys2",\n        ]\n        for phrase in required:\n            self.assertIn(phrase, lower)\n        self.assertLess(lower.index("prove the transport fail-fast"), lower.index("how to use this ssh setup"))\n\n    def test_secret_and_scope_boundaries_are_explicit(self):\n        lower = self.prompt["copyContent"].lower()\n        self.assertIn("never ask the operator to send a private key or passphrase in chat", lower)\n        self.assertIn("do not make a global git/ssh-policy change", lower)\n        self.assertIn("preserve every unrelated remote", lower)\n        self.assertIn("do not overwrite an existing key file", lower)\n        self.assertIn("do not delete old keys", lower)\n\n    def test_write_proof_is_safe_and_auth_is_not_confused_with_permission(self):\n        lower = self.prompt["copyContent"].lower()\n        self.assertIn("non-mutating proof", lower)\n        self.assertIn("do not create a remote branch, tag, commit, or force update merely to test credentials", lower)\n        self.assertIn("distinguish authentication success from authorization", lower)\n        self.assertIn("read-only intent", lower)\n        self.assertIn("read-write intent", lower)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    run()
