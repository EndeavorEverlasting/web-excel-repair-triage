# Prompt Compilation

Bounded Prompt Kit subsystem for compiling semantic prompt policy into effective instructions without owning lifecycle events.

- Architecture: [`PROMPT_COMPILATION_ARCHITECTURE.md`](./PROMPT_COMPILATION_ARCHITECTURE.md)
- Sprint map: [`PROMPT_COMPILATION_SPRINT_MAP.md`](./PROMPT_COMPILATION_SPRINT_MAP.md)
- Compiler: `scripts/prompt_language_compiler.py`
- Focused tests: `tests/test_prompt_compilation.py`

```bash
python -m unittest tests.test_prompt_compilation -v
python scripts/prompt_language_compiler.py validate-fixtures --summary
```
