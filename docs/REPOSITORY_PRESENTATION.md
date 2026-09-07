# Repository Presentation Contract

The GitHub repository page is part of the public product surface. A working site hidden only in README text is not enough: the repository's **About** metadata, first-screen README, licensing signal, and public entrypoint must converge before a public product extraction or handoff is considered polished.

## Canonical Triage presentation

Repository: `EndeavorEverlasting/web-excel-repair-triage`

| Surface | Expected state |
|---|---|
| GitHub About description | `Spreadsheet intelligence, Excel-for-Web repair tooling, and the current Operant operator surface.` |
| GitHub About website | `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/` |
| GitHub topics | `excel`, `xlsx`, `ooxml`, `spreadsheet`, `excel-for-web`, `ai-agents`, `prompt-engineering`, `agentic-workflows` |
| Visibility | Public |
| GitHub Pages | Enabled |
| README first screen | Must expose the canonical browser surface without requiring a clone |
| License | **UNRESOLVED OPERATOR DECISION** — do not invent or silently add a license |
| Social preview | **UNRESOLVED PRESENTATION ITEM** — choose/upload deliberately before declaring the repository presentation-complete |

The canonical normal-browser surface is the Prompt Kit compatibility path above until the Operant cutover is completed. Do not point the About website field at a temporary branch preview, local file, loopback runtime, or an unproved future Operant repository.

## Provider metadata is not source-code metadata

GitHub About description, website, topics, license detection, and social preview are provider-facing presentation state. README links do not populate the About sidebar automatically. A repository may therefore have a correct README and still present poorly in GitHub chrome.

When provider mutation is unavailable to the active agent/tool, report that exact boundary and give the operator the smallest UI action. Do not claim the repository presentation is complete merely because tracked files are correct.

## Current application path

On the repository page, use the **About** gear and set the expected description, website, and topics above. Save the changes, then re-read repository metadata and verify that GitHub reports the same values.

License selection is a separate consequential decision and remains user-owned. Social-preview artwork is also a deliberate product decision; do not fabricate one merely to satisfy a checklist.

## Operant extraction gate

Before `UnderDeskDev/Operant` is created or declared ready for users, explicitly prove each of these:

1. product/repository name and public description are final;
2. canonical website/homepage is live and placed in GitHub About metadata;
3. repository topics describe the actual product rather than donor-repo history;
4. README first screen exposes the live product, install/use path, and concise purpose;
5. license choice is explicit and visible;
6. social-preview/brand presentation is intentionally selected or explicitly waived;
7. provider metadata is re-read after mutation rather than assumed from source files;
8. donor Triage and new Operant authorities are not both presented as canonical after cutover.

This gate is presentation and authority hygiene. It must not delay unrelated safe Triage work, but Operant extraction should not close while these items are silently missing.
