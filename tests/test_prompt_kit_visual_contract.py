from __future__ import annotations

from triage import prompt_kit_visual_contract as visual


def test_visual_policy_is_valid_and_has_cream_palette() -> None:
    policy = visual.load_policy()
    assert visual.validate_policy(policy) == ()
    assert visual.palette()["Cream"] == ("F7E6C4", "7C5A10")


def test_quote_wrapped_xyz_placeholders_become_bare_tokens() -> None:
    text = '$Repo = "xyz_repo_or_path"; --agent “xyz_agent_spec”; @(xyz_no_change)'
    normalized = visual.unquote_placeholders(text)
    assert normalized == '$Repo = xyz_repo_or_path; --agent xyz_agent_spec; @(xyz_no_change)'
    assert visual.quoted_placeholders('$Repo = "xyz_repo_or_path"') == ('"xyz_repo_or_path"',)
    assert visual.quoted_placeholders('Repository: xyz_repo_or_path') == ()
