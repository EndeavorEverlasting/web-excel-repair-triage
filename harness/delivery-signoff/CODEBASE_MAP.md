# Delivery Sign-Off Harness — Codebase Map

`web-excel-repair-triage` owns sign-off artifact construction, layout, package checks, replacement safety, typed routing, and operator-facing generation. `EndeavorEverlasting/FUN` remains evidence authority.

| Path | Purpose |
| --- | --- |
| `triage/delivery_signoff/schema.py` | Input normalization, duplicate checks, quantity/serial binding, safe identity limits. |
| `triage/delivery_signoff/document.py` | Editable DOCX construction and density-based layout selection. |
| `triage/delivery_signoff/proof.py` | LibreOffice/PDF rendering, page rasterization, rendered-text extraction, path/hash checks. |
| `triage/delivery_signoff/generator.py` | Locking, temporary generation, reconciliation, backup, atomic publication, manifest/log output. |
| `scripts/generate_delivery_signoff.py` | Canonical CLI constrained to `Outputs/delivery-signoff/`. |
| `scripts/evaluate_delivery_signoff_trigger.py` | Typed trigger evaluation with deny precedence. |
| `scripts/validate_delivery_signoff_harness.py` | Full layout/harness validation and input-spec/manifest reconciliation. |
| `tests/fixtures/delivery_signoff/` | Melville and Huntington protected-data-safe acceptance specs. |
| `tests/fixtures/delivery_signoff_trigger/` | Allow, evidence-route, deny, and no-match trigger fixtures. |
| `tests/test_delivery_signoff_generator.py` | Product, render, replacement, collision, layout, and CLI regressions. |
| `tests/test_delivery_signoff_harness_validator.py` | Fail-closed manifest evidence-binding tests. |
| `tests/test_delivery_signoff_trigger.py` | Deterministic route and deny-precedence tests. |
| `.github/workflows/delivery-signoff-generator.yml` | Full generator acceptance lane. |

Canonical command:

```bash
python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff/<new-run-root>
```
