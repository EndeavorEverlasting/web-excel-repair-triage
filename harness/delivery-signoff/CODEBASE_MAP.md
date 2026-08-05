# Delivery Sign-Off Harness — Codebase Map

## Repository authority

`web-excel-repair-triage` owns artifact construction, layout, package checks, comparison, and operator-facing generation workflows. For delivery sign-offs it consumes a validated evidence specification from `EndeavorEverlasting/FUN` plus protected active-roster inputs when required. It must not rewrite evidence truth.

## Operational surfaces

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Governance, proof ceilings, branch isolation, artifact consumption, and next-command contract. |
| `docs/ACTIVE_ROSTER_LOG_MECHANICS.md` | Per-date roster resolution: approved override, worked project, assignment, default. |
| `triage/admin_billing_summary/reader.py` | Existing active-roster resolution implementation to reuse, not duplicate. |
| `triage/delivery_signoff/generator.py` | Validates `delivery-signoff-spec/v1`, builds the editable DOCX, renders PDF/PNG proof, reconciles counts, and emits the manifest/log. |
| `scripts/generate_delivery_signoff.py` | Operator CLI entry point. |
| `scripts/validate_delivery_signoff_harness.py` | Harness and generated-manifest validator. |
| `tests/fixtures/delivery_signoff/` | Protected-data-safe acceptance specs, including equipment-only Melville and Huntington examples. |
| `tests/test_delivery_signoff_generator.py` | Product generation, rendering, count, cable, duplicate, and quantity regression tests. |
| `tests/test_delivery_signoff_harness_validator.py` | Fail-closed manifest proof regression tests. |
| `.github/workflows/delivery-signoff-generator.yml` | Installs renderer dependencies, runs tests, generates fixtures, validates manifests, and publishes packages. |
| `Outputs/delivery-signoff/` | Canonical generated artifact destination; never overwrite protected inputs. |
| `harness/delivery-signoff/registry.json` | Machine-readable harness map and artifact contract. |
| `configs/delivery_signoff_layout_v1.json` | Serial-first, ink-ready page and typography contract. |
| `skills/delivery-signoff-generation/SKILL.md` | Repeatable generation and validation procedure. |
| `capabilities/delivery-signoff-generation.json` | Explicit machine-readable operation boundary. |
| `triggers/delivery-signoff-generation.json` | Deterministic routing conditions. |

## Input contract

Primary input is `delivery-signoff-spec/v1`. It carries site and sign-off identity, recipient fields, one or more distinct equipment rows, optional serialized asset groups, optional provenance, stale-content rejection tokens, and proof ceiling. Equipment-only sign-offs are valid; serial counts become mandatory only when the spec declares serialized assets.

Active-roster data is resolved through existing mechanics. It may support date/person/project context; it does not replace physical counts or serial evidence.

## Output contract

- editable, unprotected DOCX;
- rendered PDF plus per-page PNG previews;
- artifact manifest with contained relative paths, SHA-256 values, page count, serial reconciliation, equipment rows, draw-surface checks, stale-content scan, and proof ceiling;
- validation log and operator handoff.

## Commands

```bash
python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff
python scripts/validate_delivery_signoff_harness.py
python scripts/validate_delivery_signoff_harness.py --manifest <artifact-manifest.json>
python -m pytest -q tests/test_delivery_signoff_generator.py tests/test_delivery_signoff_harness_validator.py
git diff --check
```

CI entry points: `.github/workflows/delivery-signoff-harness.yml` and `.github/workflows/delivery-signoff-generator.yml`.
