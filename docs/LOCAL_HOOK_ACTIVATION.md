# Local Git Hook Activation

This repository tracks `.githooks/pre-commit` and `.githooks/pre-push`, but Git does not automatically activate a repository's tracked hook directory in a fresh checkout. Activation is deliberately repository-local.

## Activate once per editable checkout

### Windows

From the repository root:

```bat
Install-Local-Hooks.cmd
```

The wrapper resolves the repository-owned Python installer beside itself, prefers the Windows `py -3` launcher when available, falls back to `python`, and propagates the installer exit code.

### Any platform with Python 3

```bash
python scripts/install_local_hooks.py
```

Successful output includes:

```text
[harness] local hooks configured: core.hooksPath=.githooks
[harness] tracked hooks: pre-commit and pre-push are present at Git mode 100755
```

## Verify without changing configuration

Windows:

```bat
Install-Local-Hooks.cmd --check
```

Any platform with Python 3:

```bash
python scripts/install_local_hooks.py --check
```

A successful check proves, for the current checkout only, that:

- `.githooks/pre-commit` and `.githooks/pre-push` exist;
- both hook paths are tracked by Git;
- both are recorded in the index with executable mode `100755`;
- local `core.hooksPath` is exactly `.githooks`.

The installer writes only `git config --local core.hooksPath .githooks`. It never changes global Git configuration.

## Existing custom hook configuration

If the checkout already has another local `core.hooksPath`, the installer fails closed and preserves it. Review that setup before intentionally replacing it:

```bash
python scripts/install_local_hooks.py --replace
```

On Windows the equivalent is `Install-Local-Hooks.cmd --replace`.

`--replace` is an explicit operator action. Automation should not use it to overwrite an unknown hook setup.

## Proof boundary

The installer and CI can prove that activation works in a tested checkout on Windows and Linux, including the Windows CMD entrypoint. They cannot make Git automatically trust or activate tracked hooks in every future clone before an operator/bootstrap command runs. A newly cloned editable checkout therefore still needs the one-time activation command above.

Local hook activation complements remote validation; it is not a substitute for repository CI, review, or branch controls. The hook installer also does not scan file contents, Git history, or OneDrive synchronization state.
