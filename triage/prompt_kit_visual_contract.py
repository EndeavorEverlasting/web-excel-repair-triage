"""Prompt placeholder ergonomics and semantic row/tab color policy."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

DEFAULT_POLICY_PATH = Path(__file__).parents[1] / "configs/harness/prompt_library_visual_policy_v1.json"
_PLACEHOLDER_TOKEN = r"xyz_[A-Za-z0-9_]+(?:/xyz_[A-Za-z0-9_]+)*"
_QUOTE_CHARS = '"\\\'“”‘’'
QUOTED_PLACEHOLDER_RE = re.compile(rf"(?P<open>[{re.escape(_QUOTE_CHARS)}])(?P<token>{_PLACEHOLDER_TOKEN})(?P<close>[{re.escape(_QUOTE_CHARS)}])")


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("prompt visual policy must be one JSON object")
    return payload


def validate_policy(policy: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if policy.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    if policy.get("policy_id") != "prompt-library-visual-and-placeholder-policy":
        issues.append("policy_id drift")
    placeholder = policy.get("placeholder_ergonomics")
    if not isinstance(placeholder, Mapping) or placeholder.get("quote_wrapped_placeholders_forbidden") is not True:
        issues.append("quote-wrapped placeholder prohibition missing")
    library = policy.get("prompt_library")
    if not isinstance(library, Mapping):
        issues.append("Prompt Library visual policy missing")
    else:
        if library.get("semantic_color_column") != "N":
            issues.append("semantic Color column must remain N")
        if library.get("row_color_columns") != "B:O":
            issues.append("semantic row color columns must remain B:O")
        if library.get("sparse_navigation_columns") != ["A", "P"]:
            issues.append("sparse navigation columns must remain A and P")
        if library.get("prompt_tab_color_source") != "Prompt Library semantic Color label":
            issues.append("prompt tab color source drift")
    palette = policy.get("palette")
    if not isinstance(palette, Mapping) or "Cream" not in palette:
        issues.append("semantic color palette or Cream entry missing")
    else:
        for label, item in palette.items():
            if not isinstance(item, Mapping):
                issues.append(f"palette entry {label} must be an object")
                continue
            for field in ("fill", "text"):
                value = str(item.get(field, ""))
                if not re.fullmatch(r"[0-9A-F]{6}", value):
                    issues.append(f"palette {label}.{field} must be six uppercase hex digits")
    return tuple(issues)


def unquote_placeholders(text: str) -> str:
    previous = None
    while text != previous:
        previous = text
        text = QUOTED_PLACEHOLDER_RE.sub(lambda match: match.group("token"), text)
    return text


def quoted_placeholders(text: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in QUOTED_PLACEHOLDER_RE.finditer(text))


def palette(path: str | Path = DEFAULT_POLICY_PATH) -> dict[str, tuple[str, str]]:
    policy = load_policy(path)
    issues = validate_policy(policy)
    if issues:
        raise ValueError(f"invalid prompt visual policy: {list(issues)[:8]}")
    return {label: (item["fill"], item["text"]) for label, item in policy["palette"].items()}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--text")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        issues = list(validate_policy(policy))
        result = {"valid": not issues, "policy": str(args.policy), "issues": issues}
        if args.text is not None:
            result.update({"input": args.text, "normalized": unquote_placeholders(args.text), "quoted_placeholders": list(quoted_placeholders(args.text))})
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"valid": False, "policy": str(args.policy), "issues": [str(exc)]}
    print(json.dumps(result, indent=2) if args.json or not result["valid"] or args.text is not None else "prompt visual and placeholder policy: PASS")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
