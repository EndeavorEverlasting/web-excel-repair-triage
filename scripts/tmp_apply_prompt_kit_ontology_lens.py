#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = BUILDER.read_text(encoding="utf-8")

    constants_old = '''FEEDBACK_PRODUCTION_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-feedback-production.js"
ACTIONABILITY_POLICY = (
'''
    constants_new = '''FEEDBACK_PRODUCTION_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-feedback-production.js"
ONTOLOGY_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-ontology.js"
CAPABILITIES_REGISTRY = REPO_ROOT / "harness" / "capabilities.v1.json"
SKILLS_ROOT = REPO_ROOT / ".ai" / "skills"
ACTIONABILITY_POLICY = (
'''
    text = replace_once(text, constants_old, constants_new, "ontology constants")

    helper_old = '''def _read_runtime(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} is missing: {path}") from exc


def render() -> str:
'''
    helper_new = '''def _read_runtime(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} is missing: {path}") from exc


def _skill_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.parent.name


def build_ontology_model(prompts: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a repository-backed capability/skill/implementation lens for Prompt Kit."""
    payload = _load_json(CAPABILITIES_REGISTRY)
    if not isinstance(payload, dict):
        raise SystemExit(f"Capability registry must be an object: {CAPABILITIES_REGISTRY}")
    if payload.get("schema_version") != "web-excel-capabilities/v1":
        raise SystemExit(f"Unsupported capability registry schema in {CAPABILITIES_REGISTRY}")
    source_capabilities = payload.get("capabilities")
    if not isinstance(source_capabilities, list):
        raise SystemExit("Capability registry must define a capabilities array")

    prompt_by_id = {str(prompt["id"]): prompt for prompt in prompts}
    capability_ids: set[str] = set()
    skill_links: dict[str, list[str]] = {}
    capabilities: list[dict[str, Any]] = []
    implementations: list[dict[str, Any]] = []

    for index, source in enumerate(source_capabilities):
        if not isinstance(source, dict):
            raise SystemExit(f"Capability record {index} is not an object")
        capability_id = str(source.get("id", "")).strip()
        if not capability_id:
            raise SystemExit(f"Capability record {index} has no id")
        if capability_id in capability_ids:
            raise SystemExit(f"Duplicate capability id: {capability_id}")
        capability_ids.add(capability_id)

        skill = str(source.get("skill", "")).strip()
        operation = str(source.get("operation", "")).strip()
        proof_ceiling = str(source.get("proof_ceiling", "")).strip()
        implementation = source.get("implementation")
        trigger_ids = source.get("trigger_ids", [])
        inputs = source.get("inputs", [])
        outputs = source.get("outputs", [])
        if not skill or not operation or not proof_ceiling:
            raise SystemExit(
                f"Capability {capability_id} must define skill, operation, and proof_ceiling"
            )
        if not isinstance(implementation, dict):
            raise SystemExit(f"Capability {capability_id} implementation must be an object")
        if not isinstance(trigger_ids, list) or not isinstance(inputs, list) or not isinstance(outputs, list):
            raise SystemExit(
                f"Capability {capability_id} trigger_ids, inputs, and outputs must be arrays"
            )
        kind = str(implementation.get("kind", "")).strip()
        if not kind:
            raise SystemExit(f"Capability {capability_id} implementation has no kind")

        normalized = {
            "id": capability_id,
            "version": source.get("version"),
            "status": source.get("status"),
            "skill": skill,
            "trigger_ids": list(trigger_ids),
            "operation": operation,
            "inputs": list(inputs),
            "outputs": list(outputs),
            "implementation": dict(implementation),
            "proof_ceiling": proof_ceiling,
        }
        capabilities.append(normalized)
        skill_links.setdefault(skill, []).append(capability_id)

        prompt_id = str(implementation.get("prompt_id", "")).strip()
        path = str(implementation.get("path", "")).strip()
        if prompt_id:
            locator = prompt_id
        elif path:
            locator = path
        else:
            locator = ", ".join(
                f"{key}: {value}"
                for key, value in implementation.items()
                if key != "kind"
            ) or "registered without locator"
        implementation_record: dict[str, Any] = {
            "capability_id": capability_id,
            "skill": skill,
            "kind": kind,
            "locator": locator,
        }
        if prompt_id:
            if prompt_id not in prompt_by_id:
                raise SystemExit(
                    f"Capability {capability_id} references unknown prompt implementation: {prompt_id}"
                )
            implementation_record["prompt_id"] = prompt_id
            implementation_record["prompt_name"] = str(prompt_by_id[prompt_id].get("name", ""))
        if path:
            implementation_record["path"] = path
        implementations.append(implementation_record)

    skills: list[dict[str, Any]] = []
    for path in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        skills.append(
            {
                "id": path.parent.name,
                "title": _skill_title(path),
                "path": relative,
                "capability_ids": list(skill_links.get(relative, [])),
            }
        )

    registered_skill_paths = set(skill_links)
    actual_skill_paths = {item["path"] for item in skills}
    missing_skills = sorted(registered_skill_paths - actual_skill_paths)
    if missing_skills:
        raise SystemExit(
            "Capability registry references missing skill files: " + ", ".join(missing_skills)
        )

    return {
        "schema_version": "prompt-kit-ontology/v1",
        "capabilities": capabilities,
        "skills": skills,
        "implementations": implementations,
    }


def render() -> str:
'''
    text = replace_once(text, helper_old, helper_new, "ontology model helper")

    render_head_old = '''    prompts = load_prompt_kit_registry()
    reference = _load_json(REFERENCE)
    html = build_prompt_kit.build_html(prompts, reference)
    guided_script = _read_runtime(GUIDED_RECOMMENDATIONS, "Guided recommendation behavior")
'''
    render_head_new = '''    prompts = load_prompt_kit_registry()
    reference = _load_json(REFERENCE)
    ontology = build_ontology_model(prompts)
    ontology_json = json.dumps(ontology, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = build_prompt_kit.build_html(prompts, reference)
    guided_script = _read_runtime(GUIDED_RECOMMENDATIONS, "Guided recommendation behavior")
'''
    text = replace_once(text, render_head_old, render_head_new, "render ontology data")

    runtime_old = '''    feedback_production_script = _read_runtime(
        FEEDBACK_PRODUCTION_RUNTIME, "Prompt Kit production feedback behavior"
    )
    closing = "</body>"
'''
    runtime_new = '''    feedback_production_script = _read_runtime(
        FEEDBACK_PRODUCTION_RUNTIME, "Prompt Kit production feedback behavior"
    )
    ontology_script = _read_runtime(
        ONTOLOGY_RUNTIME, "Prompt Kit ontology lens behavior"
    )
    closing = "</body>"
'''
    text = replace_once(text, runtime_old, runtime_new, "ontology runtime load")

    supplemental_old = '''    supplemental = (
        f"<script>\\n{guided_script}\\n</script>\\n"
        f"<script>\\n{journey_script}\\n</script>\\n"
        f"<script>\\n{profile_script}\\n</script>\\n"
        f"<script>\\n{polish_script}\\n</script>\\n"
        f"<script>\\n{correspondence_script}\\n</script>\\n"
        f"<script>\\n{management_script}\\n</script>\\n"
        f"<script>\\n{spec_architecture_script}\\n</script>\\n"
        f"<script>\\n{feedback_production_script}\\n</script>\\n"
    )
'''
    supplemental_new = '''    supplemental = (
        f"<script>\\nwindow.PROMPT_KIT_ONTOLOGY = {ontology_json};\\n</script>\\n"
        f"<script>\\n{guided_script}\\n</script>\\n"
        f"<script>\\n{journey_script}\\n</script>\\n"
        f"<script>\\n{profile_script}\\n</script>\\n"
        f"<script>\\n{polish_script}\\n</script>\\n"
        f"<script>\\n{correspondence_script}\\n</script>\\n"
        f"<script>\\n{management_script}\\n</script>\\n"
        f"<script>\\n{spec_architecture_script}\\n</script>\\n"
        f"<script>\\n{feedback_production_script}\\n</script>\\n"
        f"<script>\\n{ontology_script}\\n</script>\\n"
    )
'''
    text = replace_once(text, supplemental_old, supplemental_new, "ontology runtime injection")

    BUILDER.write_text(text, encoding="utf-8")
    print(f"patched {BUILDER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
