# AI Harness Prompt Kit V21 Generation Record

Date: 2026-07-14

## Source and output

```text
Source: AI_Harness_Prompt_Kit_v20.xlsx
Source SHA-256: 9b0934ef7bca9b308bf605c9be0c98f75f420c92d5a3f6e1995df1465747c076
Output: AI_Harness_Prompt_Kit_v21.xlsx
Output SHA-256: 57462922b2bace621ae663d4ba03b5a40f9b130ef5098cdd8c04b9eae30033a0
```

The workbook was produced by bounded OOXML part and unique-cell replacement against the exact accepted V20 package. No production save through openpyxl or another general serializer occurred.

## Product changes

- Added `P21_COPY_SAFE` with the Many-to-One Prompt Consolidator.
- Added an explicit artifact execution mode so a chat generates the discussed artifact when source material and tools are available.
- Added Prompt Library and sequence records for P21.
- Updated version and P00-P21 references across prompt-kit contract sheets and portable registries.
- Added 44 exact-range forward links and 22 drawing-layer backlinks.
- Backlinks are anchored at C1, contain no worksheet cell payload, and target the matching Prompt Library B-row.

## Package delta

```text
Source parts: 62
Target parts: 129
Added parts: 67
Removed parts: 0
Modified parts: 38
Unchanged parts: 24
```

The 67 added parts are one worksheet, 22 worksheet relationship parts, 22 drawings, and 22 drawing relationship parts. Existing prompt worksheets changed only to reference their new drawing. Formula-bearing sheet order moved by one; `calcChain.xml` was updated and revalidated.

## Static validation

The exact output SHA passed:

- ZIP CRC and XML parse;
- all internal relationship targets;
- 22 prompt tabs and dense copy surfaces;
- zero duplicate coordinates;
- exact dimension coverage;
- 44 exact-range forward links;
- 22 matching drawing backlinks;
- Aptos-only font inventory;
- Prompt Library H body 12-point regular Aptos;
- one operational meaning per used color;
- no table parts, shared formulas, array formulas, dynamic-array tokens, or formula-error text;
- synchronized eight-entry calculation chain;
- synthetic focused suite: 16 passed;
- repository validator runs against the production artifact: all five validators passed;
- `artifact_tool` import, key-range inspection, formula/error scan, drawing inspection, and four PNG renders passed.

## CI result

The PR-local `AI Prompt Kit contracts` workflow passed on GitHub for the V21 branch.

The broader `Artifact engine tests` workflow remains blocked by the known `main`-baseline One Marcus fixture defect documented on PR #56:

```text
lxml.etree.XMLSyntaxError:
Namespace prefix r for id on externalReference is not defined
```

The 11 affected tests are under `tests/test_one_marcus_recon.py` and `tests/test_one_marcus_immutability.py`. PR #55 owns the `tests/fixtures/one_marcus_recon/fixtures.py` namespace repair. The V21 branch does not duplicate that unrelated fix.

## Field acceptance

Status: `NOT_RUN`.

No Excel-for-Web session was available in the execution environment. The candidate must not be classified as `CLEAN OPEN` until the exact SHA is uploaded, opened, copied, backlink-tested, downloaded, hashed, compared, and revalidated. Static and render proof do not establish click or clipboard behavior.
