# Finding: legacy-comment VML identity collisions can trigger Excel repair

Date: 2026-07-31  
Status: confirmed from candidate/repaired workbook pair; detector + bounded repair added  
Scope: Excel legacy comments/notes stored as worksheet-linked VML drawings

## Executive finding

A workbook can pass XML well-formedness and relationship-target existence checks and still be repair-prone when **two legacy-comment VML drawing parts reuse the same shape-id namespace**.

The field pair analyzed on 2026-07-31 showed this exact progression:

| Surface | Candidate | Excel-repaired copy |
|---|---|---|
| First note drawing | `idmap data="1"`; `_x0000_s1026`, `_x0000_s1027`, `_x0000_s1028` | retained in the `1xxx` block |
| Second note drawing | **also** `idmap data="1"`; **also** `_x0000_s1026`, `_x0000_s1027` | re-indexed to a different block (`idmap data="4"`; `4xxx` shape ids) |
| Comment payloads | 5 notes | 5 notes preserved |
| Comment/VML part naming | nested/noncanonical generated paths | Excel rewrote to conventional `xl/commentsN.xml` + `xl/drawings/vmlDrawingN.vml` paths |

The strongest repair signal is the package-wide collision: the candidate had duplicate `_x0000_s1026` and `_x0000_s1027` values in distinct worksheet-linked VML parts, while the repaired copy did not.

## Why existing gates missed it

The candidate was still structurally plausible at the generic OPC/XML level:

- XML parsed.
- Relationship targets existed.
- There were no duplicate ZIP entry names.
- The legacyDrawing relationships resolved.

`rels_missing_targets` therefore cannot detect this class. The defect is an **identity collision across otherwise valid parts**, not a missing part.

## Regression history from the same workbook family

The pre-edit workbook had one legacy-comment VML drawing only, using the `1xxx` shape-id block. After a new note-bearing surface was generated, a second VML drawing was created and reused the same `idmap data="1"` block and shape ids. That is the point at which the package acquired the collision.

This makes the failure especially relevant to workbook automation that:

1. imports an existing workbook containing notes, and
2. adds new notes/comments on another worksheet, then
3. reserializes legacy-comment VML.

## New guard

`triage.vml_comment_integrity.scan_vml_comment_integrity()` inventories worksheet-linked VML drawings and fails when either of these package-wide collisions occurs:

- the same `_x0000_s####` shape id appears in more than one VML part;
- the same `o:idmap/@data` block is claimed by more than one VML part.

The shape-id collision is the primary signal. Duplicate idmap data is retained as a companion signal because the repaired field pair changed both together.

Run it directly:

```bash
python -m triage.vml_comment_integrity path/to/workbook.xlsx --json
```

Exit code is `0` on pass and `1` when collisions are found.

## Bounded repair

The module can now repair this specific identity collision in a copied workbook:

```bash
python -m triage.vml_comment_integrity candidate.xlsx \
  --repair-out output.xlsx \
  --json
```

`repair_vml_comment_collisions()` keeps the first owner of each collision stable and re-indexes later colliding worksheet-linked VML drawings into a fresh idmap block with new package-unique `_x0000_s####` ids.

The repair is intentionally narrow:

- the source workbook is never overwritten;
- comment text and cell references are untouched;
- worksheet relationship parts are untouched;
- only the colliding VML drawing XML is rewritten;
- the output is rescanned before it is accepted.

This repair does **not** claim Excel-for-Web acceptance by itself. Package gates, semantic-preservation checks, and operator acceptance remain separate gates.

## Repair guidance

Do **not** "fix" this by deleting notes. Preserve note text and cell references.

For a generated workbook with multiple legacy-comment VML drawings:

1. allocate a distinct VML idmap block per drawing;
2. renumber `_x0000_s####` ids so they do not collide package-wide;
3. keep each worksheet's `legacyDrawing` relationship paired with the correct VML drawing;
4. preserve the comments part and note cell references;
5. re-run package gates, this VML identity gate, semantic-preservation checks, and then Excel-for-Web/operator acceptance.

The Excel-repaired field copy also canonicalized comments/VML part names and relationship targets. Treat that path rewrite as **corroborating normalization**, not yet as the proven root cause: the package-wide identity collision has the clearer before/after causal signal.

## Privacy / fixture policy

The real operational workbook is **not** committed. The regression test synthesizes a tiny OOXML ZIP containing only the relationship/VML identity pattern needed to prove the gate and the bounded re-index repair.
