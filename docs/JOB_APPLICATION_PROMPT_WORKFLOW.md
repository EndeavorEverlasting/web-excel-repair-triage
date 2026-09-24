# Job Application Prompt Workflow

Use this flow when you want a low-friction application session without collapsing discovery, preparation, persistence, and submission into one unsafe step.

## 1. Discover: P126

**P126 — Job Opportunity Search & Trajectory Mapper** owns broad current search, source coverage, hard-constraint filtering, fit ranking, and tracker-ready opportunities. Stop repeating broad search once one concrete opportunity is selected.

## 2. Prepare: P139

**P139 — Verified Job Opportunity Application Pack Builder** owns one selected opportunity. It verifies the posting/application destination, separates recruiter outreach from employer proof, builds the truthful fit/gap matrix, creates a derivative resume/application packet from canonical career evidence, and stages the existing tracker as **Ready to Apply** when the evidence supports that state.

A prepared packet is not a submitted application. The prompt deliberately keeps final submission, signatures, legal attestations, sensitive candidate disclosures, and employer/recruiter sends behind a separate authorization gate. This keeps the fast path useful without teaching automation to invent consent.

## 3. Synchronize: P127

**P127 — Connected Job Search Workspace & Tracker Synchronizer** owns the durable workspace: deduplication, canonical tracker reuse, application-status evidence, follow-up timing, and related career-artifact references. Use it after preparation or after a real external application/recruiter event so the workspace reflects observed state rather than inferred state.

## Weekend fast path

Repeat the middle step for each already-selected opportunity: verify -> tailor -> stage Ready to Apply -> human review/manual submission. After actual submissions or recruiter replies, run P127 once to reconcile the observed application states and follow-ups. If you need more leads, return to P126 rather than turning the application-packet prompt into an unbounded search agent.

## Proof boundary

Repository/Prompt Kit validation proves the prompt contract and generated catalog parity. It does not prove that a private resume rendered correctly in every ATS, that an employer form accepted the packet, or that an application was submitted. Those require the corresponding document/runtime/external-action evidence.
