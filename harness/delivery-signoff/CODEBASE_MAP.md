# Delivery Sign-Off Harness — Codebase Map

## Repository authority

`web-excel-repair-triage` owns artifact construction, layout, package checks, comparison, and operator-facing generation workflows. For delivery sign-offs it consumes a validated evidence specification from `EndeavorEverlasting/FUN` plus protected active-roster inputs when required. It must not rewrite evidence truth.

## Existing surfaces to inspect

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Governance, proof ceilings, branch isolation, artifact consumption, and next-command contract. |
| `README.md` | Product entry points, generators, validators, and lifecycle folders. |
| `docs/ACTIVE_ROSTER_LOG_MECHANICS.md` | Per-date roster resolution: approved override, worked project, assignment, default. |
| `triage/admin_billing_summary/reader.py` | Existing active-roster resolution implementation to reuse, not duplicate. |
| `Outputs/` | Generated artifact destination; never overwrite protected inputs. |
| `harness/delivery-signoff/registry.json` | Machine-readable harness map and artifact contract. |
| `configs/delivery_signoff_layout_v1.json` | Serial-first, ink-ready page and typography contract. |
| `skills/delivery-signoff-generation/SKILL.md` | Repeatable generation and validation procedure. |
| `capabilities/delivery-signoff-generation.json` | Explicit machine-readable operation boundary. |
| `triggers/delivery-signoff-generation.json` | Deterministic routing conditions. |
| `scripts/validate_delivery_signoff_harness.py` | Completeness, layout-contract, and manifest validator. |

## Input contract

Primary input is `delivery-signoff-spec/v1`. It carries site, delivery, people, distinct equipment lines, serialized asset groups, provenance, layout requirements, unresolved fields, and proof ceiling.

Active-roster data is resolved through existing mechanics. It may support date/person/project context; it does not replace physical counts or serial evidence.

## Output contract

- editable, unprotected DOCX;
- rendered PDF or page-preview images;
- artifact manifest with page count, hashes, serial counts, equipment-row counts, draw-surface checks, and proof ceiling;
- operator report and handoff.

## Validation commands

```bash
python scripts/validate_delivery_signoff_harness.py
python -m pytest -q
git diff --check
```

CI entry point: `.github/workflows/delivery-signoff-harness.yml`.
