# Artifact profiles

Committed JSON profiles drive stop-ship checks and approved-reference comparison.
Private blessed workbooks live under `References/approved/` (gitignored).

## Approved delta file

When a semantic change is intentional, provide a sidecar JSON:

```json
{
  "allow_candidate_semantic_sha256": "<candidate semantic_sha256>",
  "reason": "April totals corrected after roster override",
  "approved_utc": "2026-06-02"
}
```

Compare passes on semantic mismatch only when the candidate hash matches this allowlist.
