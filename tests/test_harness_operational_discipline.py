from __future__ import annotations

from triage import harness_operational_discipline as discipline


def test_portable_harness_policy_is_valid_and_complete() -> None:
    policy = discipline.load_policy()
    assert discipline.validate_policy(policy) == ()
    assert policy["connected_mutation_fallback"]["mutation_surface"] == "connected GitHub branch"
    prompt_library = policy["artifact_policy"]["prompt_library"]
    assert prompt_library["whole_row_link_columns"] == "B:O"
    assert prompt_library["sparse_navigation_columns"] == ["A", "P"]
    assert prompt_library["allowed_sparse_cadences"] == [10, 5, 2]
    assert prompt_library["placeholder_format"].startswith("bare underscore-delimited")
    assert prompt_library["semantic_row_color_columns"] == "B:O"
    assert prompt_library["prompt_tab_color_source"] == "Prompt Library semantic Color label"
    assert policy["required_harness_components"] == [
        "repo_agent_rules", "codebase_map", "workflow_specs", "run_context", "artifact_registry",
        "validators", "local_hooks_where_useful", "scoped_skills", "read_only_code_intelligence_where_useful",
        "english_operator_reports", "final_handoff_compression",
    ]


def test_run_context_requires_named_operational_surfaces() -> None:
    assert discipline.validate_run_context({})
    context = {
        "repo": "owner/repo",
        "branch_or_worktree": "feat/example",
        "pr_or_sprint": "PR #1",
        "lane": "artifact",
        "owned_scope": "generator and validator",
        "forbidden_scope": "release",
        "expected_artifacts": "workbook and manifest",
        "validation_order": "focused then broad",
    }
    assert discipline.validate_run_context(context, validation_order_specified=True) == ()
