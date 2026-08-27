from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TESTS = ROOT / "tests" / "test_gemini_youtube_playlist_ingestion_prompt.py"
NAME = "Gemini YouTube Playlist Ingestion Builder"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
matches = [p for p in payload["prompts"] if p.get("name") == NAME]
if len(matches) != 1:
    raise SystemExit(f"expected one Gemini prompt, found {len(matches)}")
source = matches[0]
auto = {"id", "seq", "copySheet", "actionabilityPolicy"}
draft = {k: v for k, v in source.items() if k not in auto}
draft["registry_id"] = "ai-engineering-level-up-prompts"
compact = r'''GEMINI YOUTUBE PLAYLIST INGESTION BUILD. PRODUCE THE ACTUAL STANDALONE IMPLEMENTATION PACKET; DO NOT RETURN ONLY AN ARCHITECTURE ESSAY, AND DO NOT PRETEND YOU CAN ACCESS THE TARGET REPOSITORY.

Consumer/product: xyz_consumer_product
Target repository identity, if one exists: xyz_repo_name_for_handoff_only
YouTube playlist URL or saved yt-dlp playlist JSON: xyz_playlist_or_fixture
Verified donor dossier / pinned source research: xyz_donor_dossier
Consumer data-model requirements: xyz_consumer_contract
Required JSON fields / CSV columns: xyz_output_fields
Known accepted decisions: xyz_accepted_decisions
Known rejected decisions: xyz_rejected_decisions

MISSION
Turn supplied playlist requirements and verified donor research into a complete runnable standalone ingestion packet for later repository integration. Implementation synthesis is required; fake repository work is forbidden.

GEMINI CAPABILITY BOUNDARY
Assume the target repository is NOT accessible unless the current Gemini environment actually exposes it. A repository name or pasted excerpt is not repository access.
- Use only supplied/accessed files, URLs, saved yt-dlp JSON, and verified donor evidence.
- MUST NOT fabricate a repository patch, imports, paths, schemas, tests, CI, branches, SHAs, merges, or runtime proof.
- Suggested destinations are `PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY`.
- Classify material repo claims as SUPPLIED_CONTEXT, PROPOSED, or UNKNOWN_REQUIRES_REPO_INSPECTION.

SOURCE AUTHORITY / DONOR CONTRACT
- yt-dlp owns YouTube extraction; consume its JSON and do not reimplement YouTube HTML parsing, InnerTube continuation/signature/player behavior, or playlist scraping.
- Consumer code owns normalization, schemas, tests, and exports. do not create two competing extraction authorities.
- TubeArchivist and NewPipeExtractor are reference sources only where license boundaries require it; do not copy GPL implementation code into an incompatible consumer.
- Record supplied donor pins and runtime `yt-dlp --version`; never invent missing versions or observations.

WINDOWS-FIRST EXTRACTION CONTRACT
Normal live extraction uses external yt-dlp metadata only: `--skip-download`, `--dump-single-json`, and `--no-warnings` when suitable. It runs without downloading media and does not request media download. `--flat-playlist` is an explicit lower-metadata census mode, never a silent substitute. Support `--input-json` for offline deterministic fixtures and return an actionable missing-executable error.

NORMALIZATION CONTRACT
Canonical normalized JSON owns playlist identity/provenance plus video/source records and ordered occurrences. Preserve supplied metadata and repeated occurrences; tracking parameters do not create new source identity.

IDENTITY / OCCURRENCE INVARIANTS
- A unique source/video entity represents stable video identity; a playlist occurrence is ordered membership and references source identity.
- Repeated appearances must not duplicate the canonical source entity merely because the same video appears again; preserve every observed occurrence and its order.
- A share/tracking parameter such as `si=` must not create a new video identity.
- Emit an input census when explicit URLs are supplied: occurrence count, unique IDs, repeated positions, and unparseable entries.

SOURCE-LIST REGRESSION EXAMPLE
The supplied corpus has 25 URL occurrences and 23 unique video IDs. `_CuibYl_Fh0` repeats and `bBdq2hf5R0I` repeats with different `si=` values. Correct normalization preserves all 25 occurrences while reusing 23 identities.

UNAVAILABLE / COMPLETENESS CONTRACT
- A null/deleted/private/unavailable slot keeps an occurrence tombstone; occurrence count must not silently shrink.
- Record COMPLETE, PARTIAL, EMPTY_CONFIRMED, EMPTY_UNPROVEN, or FAILED.
- Empty usable results require extractor evidence or explicit `--allow-empty`; otherwise fail closed or preserve uncertain completeness.
- Prefer extractor-supplied `playlist_index`; use encounter-order fallback only when needed and record `position_source`.

JSON + CSV CONTRACT
The normalized JSON is canonical; CSV is a projection from it, not a competing truth.
- Preserve Unicode, commas, quotes, newlines, missing values, and stable columns.
- Use `utf-8-sig` for spreadsheet-facing CSV unless the supplied contract overrides it, and verify actual UTF-8 BOM bytes.
- CSV cells beginning with `=`, `+`, `-`, or `@` are spreadsheet-safe while canonical JSON must remain unchanged.

DONOR EVIDENCE / VERSION CONTRACT
Never invent pins, releases, versions, licenses, or observations. Missing values are NOT_SUPPLIED or UNKNOWN. Preserve ADOPT / ADAPT / REFERENCE_ONLY / REJECT / DEFER dispositions unless new evidence explicitly changes one; must not silently change a supplied donor disposition. Separate `normalization_schema_version` from `adapter_version`. `donor_manifest.json` is a distinct machine-readable artifact.

IMPLEMENTATION PACKET — PRODUCE ALL APPLICABLE FILES
Return complete contents for:
1. `source_ingest_youtube.py` with CLI;
2. `source_import_contract.json`;
3. `youtube_playlist_fixture.json` with repeated occurrence, actual non-ASCII Unicode fixture, embedded quote, commas, and newlines;
4. `test_youtube_source_ingestion.py`;
5. `donor_manifest.json`;
6. deterministic representative normalized JSON/CSV outputs;
7. compact Windows README/run sheet.
Do not import from hypothetical consumer-repository modules. Keep the packet standalone except for external yt-dlp on live extraction.

RUNNABILITY GATE
Actually run deterministic tests when execution exists; otherwise mark UNRUN. Tests must import `subprocess` when used, validate/create the output directory, exercise all four formula prefixes, verify UTF-8 BOM bytes, use a fixture-mode CLI, use the same normalization/export path for fixture and live input, support a deterministic timestamp/clock override, and prove the fixture-mode CLI writes both JSON and CSV plus the donor manifest. A code-looking response is not runtime proof.

MINIMUM DETERMINISTIC TESTS
Prove full-mode no-download command construction; explicit flat mode; normal metadata; repeated video ID preserves multiple ordered occurrences; CSV derives from canonical JSON; comma/newline/Unicode round-trip; spreadsheet-safe while JSON remains semantically unchanged; malformed/unpinned donor failure when required; and fixture-mode CLI writes both JSON and CSV deterministically.

BACKEND-NEUTRAL NORMALIZATION CONTRACT
Raw extractor responses are backend-local and must not be the shared domain contract. Each backend adapts its native response to the same canonical source schema. A YouTube Data API adapter must not impersonate yt-dlp JSON. JSON serialization and CSV projection consume the canonical boundary.

LIVE-PROOF CEILING
If real yt-dlp execution is unavailable, say so: fixture tests do NOT prove current YouTube behavior, authentication/private-playlist access, real playlist metadata, target-repository compatibility, or integration. If live proof runs, record runtime version, playlist identity/count, outputs, and failures without credentials/cookies.

REPOSITORY-CAPABLE HANDOFF
End with one copy-paste handoff for an agent that has consumer-repository access.

PRE-MUTATION MISSION DECLARATION
Before tracked mutation, that agent declares repository and branch/worktree, lane and mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, and mutation authority. It then refreshes remote truth and find the existing source/import/domain owners, schemas, CLI patterns, artifact registry, validators, and tests.
Preserve the authority boundary: yt-dlp owns YouTube parsing, consumer owns normalization/schema/tests/exports. Forbidden scope includes copied GPL code, a second YouTube parser, media download, fabricated repo facts, and lossy JSON/CSV round trips. Do not make the operator restate the donor research.

FINAL RESPONSE
Return capability mode; source/donor authority ledger; complete standalone files; deterministic test results actually run; representative outputs; Windows commands; live proof performed or explicitly unperformed; repository claim ledger; risks/gaps; proof ceiling; and repo-capable handoff. The result is incomplete if it is only design, pseudocode, a repository plan, or a fake repository patch.'''
if len(compact) >= 12000:
    raise SystemExit(f"compacted Gemini body still exceeds ceiling: {len(compact)}")
draft["copyContent"] = compact

draft_path = ROOT / ".tmp-gemini-reallocation-draft.json"
draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
try:
    payload["prompts"] = [p for p in payload["prompts"] if p.get("name") != NAME]
    if len(payload["prompts"]) != len(matches) + len([p for p in payload["prompts"]]):
        pass
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    proc = subprocess.run(
        ["python", "scripts/prompt_registry_ops.py", "add", "--input", str(draft_path), "--registry", "ai-engineering-level-up-prompts"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode:
        raise SystemExit(proc.stdout)
    receipt = json.loads(proc.stdout)
    new_id = receipt["id"]
    new_seq = receipt["seq"]

    text = TESTS.read_text(encoding="utf-8")
    replacements = {
        '# P122 is the identity allocated by prompt_registry_ops.py for this semantic draft.': '# Identity is allocated by prompt_registry_ops.py from the refreshed combined registry.',
        'EXPECTED_ID = "P122"': f'EXPECTED_ID = "{new_id}"',
        'self.assertEqual(self.prompt["seq"], "122")': f'self.assertEqual(self.prompt["seq"], "{new_seq}")',
        'self.assertEqual(self.prompt["copySheet"], "P122_COPY_SAFE")': f'self.assertEqual(self.prompt["copySheet"], "{new_id}_COPY_SAFE")',
        'test_generated_site_contains_strengthened_p122_semantics': 'test_generated_site_contains_gemini_ingestion_semantics',
    }
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f"missing focused-test identity anchor: {old}")
        text = text.replace(old, new, 1)
    TESTS.write_text(text, encoding="utf-8")
    print(json.dumps({"status": "reallocated", "id": new_id, "seq": new_seq, "copy_length": len(compact), "helper": receipt}, indent=2))
finally:
    draft_path.unlink(missing_ok=True)
