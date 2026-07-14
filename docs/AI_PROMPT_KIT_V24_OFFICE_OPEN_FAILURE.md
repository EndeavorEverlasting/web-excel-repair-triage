# AI Harness Prompt Kit V24 — Office Open Failure Record

Date recorded: 2026-07-14

## Artifact

```text
AI_Harness_Prompt_Kit_v24.xlsx
SHA-256: 1115c85e62f80fd56c9fbd5a69b3670dbe4abd9829e46566103493756d5649f6
```

The workbook binary is not committed.

## Operator observation

- Excel for Web would not open the workbook.
- Desktop Excel also refused to open it.
- The earlier generation report had claimed static package, contract, navigation, color, and render success.

This is a failed artifact. The failure proves that the previous static gate and non-Office render proof were insufficient for delivery.

## Concrete package defect

`xl/workbook.xml` was well-formed XML, but its markup-compatibility prefix values referenced prefixes that were no longer declared.

The failed package contained declarations rewritten to generated names such as:

```xml
xmlns:ns1="http://schemas.openxmlformats.org/markup-compatibility/2006"
xmlns:ns8="http://schemas.microsoft.com/office/spreadsheetml/2010/11/main"
```

while retaining literal values such as:

```xml
ns1:Ignorable="x15 xr xr6 xr10 xr2"
<ns1:Choice Requires="x15">
```

The prefixes `x15`, `xr`, `xr6`, `xr10`, and `xr2` were not declared in that XML part.

An XML parser does not reject this condition because namespace prefixes inside `Ignorable` and `Requires` are text values. Office's markup-compatibility processor must resolve them and may refuse the package when it cannot.

The same undeclared-prefix pattern was detected in the generated V23 package, so V23 is not a valid fallback candidate.

## Root generation lesson

A generic XML round-trip can preserve element namespace URIs while changing lexical prefixes. That is not semantically safe for OOXML parts containing markup-compatibility attributes whose values themselves contain prefixes.

Accepted Microsoft-authored package parts must not be serialized through a prefix-renaming path unless the serializer also rewrites every dependent MC prefix list correctly.

## Repository enforcement

`triage/web_excel_compatibility_rules.py` now rejects:

- undeclared prefixes in `mc:Ignorable` and `mc:MustUnderstand`;
- undeclared prefixes in `mc:Choice/@Requires`;
- undeclared QName prefixes in `mc:ProcessContent`, `mc:PreserveAttributes`, and `mc:PreserveElements`.

The validator reports:

```text
undeclared_markup_compatibility_prefix
```

A synthetic regression fixture reproduces the V24 failure pattern while remaining well-formed XML, proving that ordinary XML parsing alone does not catch it.

The same patch also keeps same-workbook relationship fragments out of package-part resolution and validates retained calculation-chain entries by worksheet `sheetId` rather than display order.

## Acceptance policy after this incident

A generated workbook is not delivery-ready until the exact artifact hash passes:

1. ZIP integrity;
2. XML parsing;
3. markup-compatibility prefix resolution;
4. content-type and relationship validation;
5. workbook-profile structural checks;
6. non-Office import/render inspection;
7. desktop Excel clean open;
8. Excel for Web clean open;
9. required navigation and clipboard checks.

When Office-host tests are unavailable, report the proof ceiling honestly and do not describe the artifact as openable, accepted, or ready for use.

## Remaining gap

This commit prevents recurrence and records the failed-generation lesson. It does not repair or bless V24. A future workbook revision must be regenerated from the last field-accepted source package using bounded namespace-preserving OOXML edits, then tested in desktop and Web Excel before promotion.
