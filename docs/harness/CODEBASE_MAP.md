# Harness Codebase Map

| Surface | Authority | Purpose |
|---|---|---|
| Agent rules | `AGENTS.md` | Non-negotiable repository and artifact safety rules |
| Harness entry | `HARNESS.md` | Fresh-agent execution order |
| Harness manifest | `configs/harness/harness_manifest_v1.json` | Machine-readable discovery index |
| Workflow routing | `configs/harness/workflows_v1.json` | Selects P03/P06/P07/P14/P15/P20/P12/P56/P57 and the conversion specialization |
| Run context | `configs/harness/run_context.schema.json` | Names repo, branch/worktree, sprint, lane, scopes, artifacts, and validation order |
| Artifact registry | `configs/harness/artifact_registry_v1.json` | Generator/output/validator/field-gate ownership |
| Bidirectional conversion policy | `configs/harness/bidirectional_web_spreadsheet_v1.json` | Input analysis, direction order, action commitment, safety, and proof levels |
| Shared web/spreadsheet IR | `configs/harness/web_spreadsheet_ir_v1.schema.json` | One semantic representation for both conversion directions |
| Conversion analyzer | `triage/harness_bidirectional_conversion_contract.py` | Validates doctrine and classifies local HTML/XLSX/bundle inputs |
| Sidecar website renderer | `triage/sidecar_html/portal.py`, `triage/sidecar_html/adapters.py` | Existing manifest/CSV/JSON-to-HTML authority reused by the reverse lane |
| Prompt Kit | `triage/prompt_kit_v39_generator.py`, `triage/prompt_kit_v39_ooxml_base.py` | Package-preserving V39 generation and enforcement |
| Visual policy | `configs/harness/prompt_library_visual_policy_v1.json` | Bare placeholders and semantic row/tab colors |
| Validators | `triage/harness_operational_discipline.py`, `triage/harness_troubleshooting_contract.py`, `triage/harness_bidirectional_conversion_contract.py`, `triage/prompt_kit_visual_contract.py` | Fail closed on harness, troubleshooting, conversion, or visual contract drift |
| Reports/handoff | `triage/harness_operator_report.py`, `triage/harness_handoff.py` | English evidence report and compressed closeout |
