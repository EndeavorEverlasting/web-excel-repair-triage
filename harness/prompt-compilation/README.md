# Prompt Compilation

Bounded Prompt Kit subsystem for compiling semantic prompt policy into effective instructions without owning lifecycle events.

- Architecture: [`PROMPT_COMPILATION_ARCHITECTURE.md`](./PROMPT_COMPILATION_ARCHITECTURE.md)
- Sprint map: [`PROMPT_COMPILATION_SPRINT_MAP.md`](./PROMPT_COMPILATION_SPRINT_MAP.md)
- Compiler: `scripts/prompt_language_compiler.py`
- Context Engine adapters: `scripts/prompt_context_engine.py`
- Focused tests: `tests/test_prompt_compilation.py`, `tests/test_prompt_context_engine.py`

```bash
python -m unittest tests.test_prompt_compilation tests.test_prompt_context_engine -v
python scripts/prompt_language_compiler.py validate-fixtures --summary
python scripts/prompt_context_engine.py resolve-profile --summary
```
