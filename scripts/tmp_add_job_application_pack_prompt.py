#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "management-operations-prompts.v1.json"
TEST = ROOT / "tests" / "test_job_search_prompt_registry.py"
TUTORIAL = ROOT / "docs" / "JOB_APPLICATION_PROMPT_WORKFLOW.md"
NAME = "Verified Job Opportunity Application Pack Builder"

COPY = textwrap.dedent(
    r"""
    TURN ONE VERIFIED JOB OPPORTUNITY INTO A TRUTHFUL, APPLICATION-READY PACKET. PREPARE EVERYTHING THAT CAN SAFELY BE PREPARED NOW; DO NOT AUTO-SUBMIT, ATTEST, OR INVENT QUALIFICATIONS.

    INPUT ABOVE THIS PROMPT
    The user may provide a recruiter message, job posting, company/role name, application link, prior fit analysis, resume/master profile, tracker row, or application questions. Reuse accessible context and connected workspace evidence. Do not make the user restate facts or upload artifacts that can already be recovered from authorized sources.

    MISSION
    Take one concrete opportunity from discovery to a reviewable Ready to Apply state. Verify the opportunity and destination, measure fit honestly, tailor a derivative resume/application packet from canonical career evidence, synchronize the packet reference into the existing tracker/workspace when writable, and stop at the human submission/attestation boundary unless the user separately authorizes that exact external action.

    1. ISOLATE THE SUBJECT AND CANONICAL CAREER SOURCES
    - State whose application this is. Never mix another person's credentials, work history, education, compensation, location, or application history into the packet.
    - Discover and reuse the strongest existing master resume/profile, current role/trajectory notes, prior truthful resume variants, portfolio/site links, and canonical application tracker before creating replacements.
    - Treat the master resume/profile and evidence-backed prior variants as fact sources, not as permission to embellish. Preserve exact employer/title/date/credential truth unless stronger source evidence supports a correction.
    - When `EndeavorEverlasting/EscapeHatch` is accessible, use its current resume-presentation and application-assist contracts as implementation authority for ATS-conservative formatting, privacy, fill-plan discipline, and manual submission boundaries. Do not require that repository merely to perform a portable document-only version of this workflow.

    2. VERIFY THE OPPORTUNITY BEFORE CALLING IT READY
    Use current web or connected evidence when available. Establish as much of the following as the environment can actually prove:
    - company identity and official domain;
    - role title and material job description;
    - direct employer posting or otherwise attributable application destination;
    - requisition/posting identity when present;
    - posting/application status and relevant date evidence;
    - recruiter identity/relationship when recruiter outreach is involved;
    - compensation/work-mode/employment claims and whether they come from the employer, recruiter, or another source.
    Prefer the direct employer posting as canonical when it exists. A recruiter message is evidence of outreach, not proof of employment, an offer, interview status, or employer authorization. A polished page, accessible form, or matching company/role text alone is not sufficient identity proof.

    Return an OPPORTUNITY VERIFICATION RECEIPT with VERIFIED / PARTIAL / UNVERIFIED for identity, posting status, and application destination. If the destination cannot be verified, do not label the packet Ready to Apply and do not route sensitive identity, tax, banking, government-ID, or credential material to it. Preserve the exact verification gap and safest next check.

    3. BUILD A FACT-GROUNDED FIT / GAP MATRIX
    Compare the material requirements in the posting against source-backed candidate evidence. Separate:
    - DIRECT MATCH — clearly supported experience/skill/credential;
    - TRANSFERABLE MATCH — adjacent evidence that can be described accurately without pretending it is identical experience;
    - GAP / UNKNOWN — not established by current evidence;
    - HARD GATE — license, clearance, work authorization, location, degree, years, schedule, or other requirement that may actually prevent application.
    Do not convert tool familiarity into years of experience, project exposure into employment tenure, coursework into a credential, leadership adjacency into a management title, or aspiration into current proficiency. Fit scores may summarize evidence but may not hide a hard gate.

    4. TAILOR THE RESUME AS A DERIVATIVE, NOT A NEW BIOGRAPHY
    Build the strongest truthful resume variant for this exact opportunity from canonical career evidence.
    - Preserve factual employer/title/date/education/credential identity.
    - Reorder and tighten existing evidence so the most relevant supported accomplishments appear first.
    - Use job-language alignment only where the underlying claim remains true; never keyword-stuff unsupported skills.
    - Quantified achievements must come from a source that already supports the number. Do not manufacture scale, savings, uptime, headcount, device counts, percentages, budgets, or years.
    - Prefer ATS-conservative single-column selectable text, clear headings, ordinary fonts, sensible minimum text size, and no decorative layout that damages parsing. Keep a master resume richer than any one application derivative.
    - Never commit private resume bytes, addresses, phone numbers, personal email addresses, government identifiers, or other candidate PII into a public repository merely to automate this workflow.

    When a connected document workspace is writable, create or update a clearly named derivative using the existing workspace convention and preserve the master. Produce the useful delivery forms the environment supports (for example Google Doc plus DOCX/PDF projection) and report exact artifact identities/links actually created. When writes or rendering are unavailable, return complete copy-ready resume content plus an exact patch/export plan; do not claim a file exists.

    5. PREPARE SUPPORTING APPLICATION MATERIAL
    Prepare only what the opportunity actually needs: concise cover note, recruiter reply, short-answer drafts, role-specific highlights, interview talking points, or an application checklist. Keep all claims traceable to the same candidate evidence.
    - Draft employer/recruiter messages when useful, but sending is a separate external-action gate.
    - Do not infer or answer demographic/EEO, disability, veteran, salary-history, legal attestation, background, work-authorization, relocation, confidentiality, non-compete, or signature questions for the user unless the answer is explicitly supplied and the user has authorized use of it.
    - Do not fabricate references, certifications, degrees, portfolio items, availability, notice period, or compensation history.

    6. STAGE THE CANONICAL TRACKER / WORKSPACE
    Reuse the workspace discipline of `Connected Job Search Workspace & Tracker Synchronizer` rather than creating another tracker.
    If the same opportunity already exists, update that row instead of duplicating it. Preserve posting status separately from application status.
    When verification and packet preparation are sufficient, stage the opportunity as Ready to Apply and attach/reference the exact tailored artifacts, canonical posting/application link, verification notes, fit/gaps, and smallest next action.
    Never change `Applied?`, Date Applied, Submitted, Interview, Rejected, Offer, or equivalent status merely because a packet was prepared. Those states require observed user statement or external evidence that the event actually occurred.

    7. HUMAN SUBMISSION / ATTESTATION BOUNDARY
    DO NOT AUTO-SUBMIT. Do not click a final submit button, accept terms, provide a signature, make a legal attestation, send an employer/recruiter message, withdraw an application, schedule/accept an interview, or disclose sensitive candidate data merely because the packet is complete.
    If the user separately and explicitly authorizes one of those exact actions and the active environment has a permitted tool, treat that as a new action gate: recheck the destination and current packet, surface any material changed terms/questions, execute only the authorized action, and capture the resulting receipt. Preparation authority is not submission authority.

    8. RELATIONSHIP TO ADJACENT PROMPTS
    - `Job Opportunity Search & Trajectory Mapper` owns broad current opportunity discovery and source saturation. Do not repeat a broad search when one concrete opportunity is already selected.
    - This prompt owns single-opportunity verification, fit/gap analysis, truthful tailoring, application-packet preparation, and Ready to Apply staging.
    - `Connected Job Search Workspace & Tracker Synchronizer` owns broader workspace reconciliation, deduplication, application-status evidence, and ongoing tracker persistence. Reuse it rather than creating competing career truth.

    OUTPUT ORDER
    A. SUBJECT + SOURCE RESOLUTION — candidate, canonical career sources/workspace actually used, and write capabilities observed.
    B. OPPORTUNITY VERIFICATION RECEIPT — company/role/posting/destination/recruiter evidence, current status, and unresolved trust/privacy gaps.
    C. FIT / GAP MATRIX — direct matches, transferable matches, gaps/unknowns, hard gates.
    D. APPLICATION PACK — exact resume/letter/message/answer artifacts created or complete copy-ready content when writes are unavailable.
    E. MUTATION RECEIPT — exact tracker/file rows, ranges, artifact IDs/links, or `NO WRITE` with row-ready changes.
    F. SUBMISSION BOUNDARY — what is ready, what still needs human review/input, and every action intentionally not performed.
    G. NEXT ACTION — one concrete step that advances this opportunity from its actual current state.

    FAIL-CLOSED
    - Do not call an opportunity verified when only recruiter marketing or an unattributed repost is available.
    - Do not request or disclose sensitive PII merely to improve automation throughput.
    - Do not invent candidate experience, qualifications, metrics, employment history, application status, recruiter authority, or employer response.
    - Do not overwrite the master resume when a derivative is sufficient.
    - Do not create a duplicate tracker/workspace when the canonical one can represent the packet.
    - Do not treat a generated resume, completed form fill, or Ready to Apply row as proof that an application was submitted.

    DELIVER
    Perform every safe preparatory action available now. The success state is a verified, truthful, traceable application packet staged for quick human submission, with exact artifact/write receipts and a clear proof ceiling — not a fabricated submission receipt.
    """
).strip()

DRAFT = {
    "registry_id": "management-operations-prompts",
    "name": NAME,
    "type": "BUILD + ARTIFACT",
    "class": "CAREER / APPLICATION EXECUTION",
    "sprintRole": "Turn one concrete job opportunity or recruiter outreach into a verified, truthful, application-ready packet by reusing canonical career evidence and workspace owners while preserving privacy and a manual submission/attestation boundary",
    "useWhen": "A specific job opportunity has already been selected and the user wants to verify it, assess fit, tailor the resume/application materials, stage the canonical tracker/workspace as Ready to Apply, and minimize remaining manual work without fabricating submission or qualifications.",
    "inspectFirst": "The selected posting/recruiter outreach and current live evidence; job-search subject identity; existing master resume/profile and truthful variants; canonical application tracker/workspace; current opportunity row/status; connected Drive/Docs/Sheets or files actually available; and current EscapeHatch resume/application contracts when that repository is accessible.",
    "expectedOutput": "An opportunity-verification receipt, evidence-grounded fit/gap matrix, truthful tailored resume/application packet with exact created-artifact identities or copy-ready fallback content, canonical tracker/workspace staging receipt, explicit manual submission/attestation boundary, and one concrete next action.",
    "nextStep": "Resolve the selected opportunity and canonical candidate sources now, verify the current posting/application destination, build the strongest truthful derivative packet, stage the existing tracker as Ready to Apply only when supported, then surface the exact remaining human review or separately authorized external action.",
    "proofGate": "The opportunity identity/destination and posting state are evidenced or explicitly partial/unverified; every candidate claim traces to canonical career evidence; hard gaps remain visible; created document/tracker mutations have observed receipts; sensitive PII is not committed to public Git; Ready to Apply remains distinct from Applied; and no submit/send/attestation state is claimed without observed authorization and external-action evidence.",
    "color": "Indigo",
    "category": "standard",
    "copyContent": COPY,
    "keywords": [
        "job application packet",
        "tailored resume",
        "ready to apply",
        "verify job opportunity",
        "recruiter outreach verification",
        "application preparation",
        "resume tailoring",
        "job fit gaps",
        "application checklist",
        "manual job submission",
        "career application workflow",
        "official job posting",
    ],
}


def load_registry() -> list[dict]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [p for p in payload.get("prompts", []) if isinstance(p, dict)]


def ensure_prompt() -> dict:
    existing = next((p for p in load_registry() if p.get("name") == NAME), None)
    if existing:
        return {"status": "already-present", "id": existing["id"], "name": NAME}
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(DRAFT, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        draft_path = handle.name
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/prompt_registry_ops.py",
            "add",
            "--input",
            draft_path,
            "--registry",
            "management-operations-prompts",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode:
        raise SystemExit(proc.returncode)
    return json.loads(proc.stdout)


def ensure_tests(prompt_id: str) -> None:
    text = TEST.read_text(encoding="utf-8")
    if 'TUTORIAL = ROOT / "docs" / "JOB_APPLICATION_PROMPT_WORKFLOW.md"' not in text:
        text = text.replace(
            'SITE = ROOT / "web" / "prompt-kit" / "index.html"\n',
            'SITE = ROOT / "web" / "prompt-kit" / "index.html"\nTUTORIAL = ROOT / "docs" / "JOB_APPLICATION_PROMPT_WORKFLOW.md"\n',
            1,
        )
    if "cls.application_pack = next(" not in text:
        text = text.replace(
            "        cls.sync = cls.prompts['P127']\n",
            "        cls.sync = cls.prompts['P127']\n"
            "        cls.application_pack = next(\n"
            "            p for p in cls.prompts.values()\n"
            f"            if p[\"name\"] == {NAME!r}\n"
            "        )\n"
            "        cls.tutorial = TUTORIAL.read_text(encoding=\"utf-8\")\n",
            1,
        )
    marker = "    def test_application_pack_verifies_tailors_and_stops_before_submission(self) -> None:\n"
    if marker not in text:
        method = textwrap.dedent(
            f'''\
                def test_application_pack_verifies_tailors_and_stops_before_submission(self) -> None:
                    p = self.application_pack
                    c = p["copyContent"]
                    self.assertEqual(p["id"], {prompt_id!r})
                    self.assertEqual(p["name"], {NAME!r})
                    self.assertEqual(p["type"], "BUILD + ARTIFACT")
                    self.assertEqual(p["class"], "CAREER / APPLICATION EXECUTION")
                    for required in (
                        "OPPORTUNITY VERIFICATION RECEIPT",
                        "FIT / GAP MATRIX",
                        "Ready to Apply",
                        "DO NOT AUTO-SUBMIT",
                        "recruiter message is evidence of outreach",
                        "Job Opportunity Search & Trajectory Mapper",
                        "Connected Job Search Workspace & Tracker Synchronizer",
                        "EndeavorEverlasting/EscapeHatch",
                        "sensitive PII",
                        "MUTATION RECEIPT",
                    ):
                        self.assertIn(required, c)
                    self.assertNotIn("Richard Perez", c)
                    self.assertNotIn("micro1", c.casefold())
                    self.assertEqual(p["actionabilityPolicy"], self.policy["policy_id"])
                    self.assertIn(self.policy["marker"], c)
                    self.assertIn(p["name"], self.site)

                def test_job_application_tutorial_connects_discovery_pack_and_sync(self) -> None:
                    self.assertIn("P126", self.tutorial)
                    self.assertIn({prompt_id!r}, self.tutorial)
                    self.assertIn("P127", self.tutorial)
                    self.assertIn({NAME!r}, self.tutorial)
                    self.assertIn("manual submission", self.tutorial.casefold())
                    self.assertIn("Ready to Apply", self.tutorial)

            '''
        )
        text = text.replace("\n\nif __name__ == \"__main__\":\n", "\n\n" + method + "if __name__ == \"__main__\":\n", 1)
    TEST.write_text(text, encoding="utf-8")


def ensure_tutorial(prompt_id: str) -> None:
    TUTORIAL.write_text(
        textwrap.dedent(
            f"""\
            # Job Application Prompt Workflow

            Use this flow when you want a low-friction application session without collapsing discovery, preparation, persistence, and submission into one unsafe step.

            ## 1. Discover: P126

            **P126 — Job Opportunity Search & Trajectory Mapper** owns broad current search, source coverage, hard-constraint filtering, fit ranking, and tracker-ready opportunities. Stop repeating broad search once one concrete opportunity is selected.

            ## 2. Prepare: {prompt_id}

            **{prompt_id} — {NAME}** owns one selected opportunity. It verifies the posting/application destination, separates recruiter outreach from employer proof, builds the truthful fit/gap matrix, creates a derivative resume/application packet from canonical career evidence, and stages the existing tracker as **Ready to Apply** when the evidence supports that state.

            A prepared packet is not a submitted application. The prompt deliberately keeps final submission, signatures, legal attestations, sensitive candidate disclosures, and employer/recruiter sends behind a separate authorization gate. This keeps the fast path useful without teaching automation to invent consent.

            ## 3. Synchronize: P127

            **P127 — Connected Job Search Workspace & Tracker Synchronizer** owns the durable workspace: deduplication, canonical tracker reuse, application-status evidence, follow-up timing, and related career-artifact references. Use it after preparation or after a real external application/recruiter event so the workspace reflects observed state rather than inferred state.

            ## Weekend fast path

            Repeat the middle step for each already-selected opportunity: verify -> tailor -> stage Ready to Apply -> human review/manual submission. After actual submissions or recruiter replies, run P127 once to reconcile the observed application states and follow-ups. If you need more leads, return to P126 rather than turning the application-packet prompt into an unbounded search agent.

            ## Proof boundary

            Repository/Prompt Kit validation proves the prompt contract and generated catalog parity. It does not prove that a private resume rendered correctly in every ATS, that an employer form accepted the packet, or that an application was submitted. Those require the corresponding document/runtime/external-action evidence.
            """
        ),
        encoding="utf-8",
    )


def main() -> int:
    receipt = ensure_prompt()
    prompt_id = receipt["id"]
    ensure_tests(prompt_id)
    ensure_tutorial(prompt_id)
    print(json.dumps({"prompt": receipt, "test": str(TEST.relative_to(ROOT)), "tutorial": str(TUTORIAL.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
