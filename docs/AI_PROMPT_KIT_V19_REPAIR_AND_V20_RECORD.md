# AI Prompt Kit V19 Repair and V20 Accepted Source Record

Date: 2026-07-14

## Authority used by the V21 sprint

The authoritative V20 workbook was supplied in the operator bundle and verified before mutation:

```text
AI_Harness_Prompt_Kit_v20.xlsx
SHA-256 9b0934ef7bca9b308bf605c9be0c98f75f420c92d5a3f6e1995df1465747c076
```

The source is treated as the accepted Microsoft-normalized structural fixture. This sprint did not replace it with an earlier generated package or infer acceptance from ZIP inspection.

## Preserved V20 facts

- P00-P20 copy surfaces are dense and bounded.
- Prompt Library forward hyperlinks target exact `A1:A<last_payload_row>` ranges.
- The Prompt Library field is `Color`.
- Visible workbook fonts use Aptos.
- Prompt Library column H uses 12-point regular Aptos.
- The workbook retains a synchronized calculation chain. Its sheet index is one-based and must move when a sheet is inserted earlier in workbook order.

## Validator correction

Earlier validator drafts were tied to V19 naming, expected 21 prompts universally, and expected `Color Meaning`. V21 replaces those assumptions with explicit V20 and V21 profiles. The accepted V20 source remains valid without pretending it already contains V21 backlinks.

## Proof boundary

V20 field acceptance is inherited from the operator-designated source and exact hash. This V21 run independently verified the source hash and static package shape; it did not rerun the historical V20 browser session.
