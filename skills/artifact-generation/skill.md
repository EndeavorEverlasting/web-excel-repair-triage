# Artifact Generation Skill

Use P56. Inspect accepted examples, generators, schemas, artifact registry, validators, and output policy. Generate the actual artifact and supporting manifest/bundle when required. Inspect the output itself, record path/hash, run focused and broad gates, and state field acceptance separately.

For website/spreadsheet requests, run `triage.harness_bidirectional_conversion_contract` before implementation. Preserve the source, fingerprint it, classify the source kind, choose the registered direction, and emit `conversion_analysis.json`. Implement website-to-spreadsheet first for structured sidecar portals; both directions must use `web-spreadsheet-ir-v1`.

Do not substitute an analysis artifact for a requested conversion. Conversion requires the actual workbook or website, conversion manifest, semantic IR hash, direction-specific validators, and explicit browser or Excel field gates.
