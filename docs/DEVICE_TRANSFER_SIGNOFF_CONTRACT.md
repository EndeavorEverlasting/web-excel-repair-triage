# Device Transfer / Stock Sign-Off Contract

## Classification

`device_transfer_signoff` is a repository-supported **workbook artifact family** for shipping and site handoff. It is not an inventory recon, billing workbook, or configuration-target dashboard.

The canonical operator artifact is a one-sheet `.xlsx` workbook named from the site code and delivery date, with JSON manifest and preflight sidecars.

## Source lineage

The contract preserves the useful behavior proven by recent Mather and Huntington sign-offs:

- `Device Transfer / Stock Sign-Off` as the canonical title;
- shipping metadata prefilled when known so the field team does not re-enter it;
- one exact shipment register supplied by the operator;
- compact serial-number drawboxes for serialized Neuron/Cybernet devices;
- signature and exception surfaces;
- landscape, fit-to-one-page printing;
- serial-first readability;
- no invented accessories or substituted shipment rows.

Real Mather/Huntington workbooks, contacts, serials, addresses, and other client data are runtime evidence only and must not be committed.

## Truth hierarchy

1. **Site config JSON** is the sole authority for site metadata and shipment rows.
2. **Source configuration workbook** is the sole authority for serialized device identifiers.
3. Generator code may derive layout, numbering, filenames, hashes, and validation results only.
4. Generator code must **never add** an item, accessory, part/model number, quantity, contact, or delivery detail that is absent from the site config.
5. Serialized shipment quantities must equal the extracted serial count exactly or generation fails closed.

This rule exists specifically to prevent the failure mode where an accessory from prior context is silently inserted into a later site's sign-off.

## Inputs

### Source configuration workbook

Read-only `.xlsx`. The generator locates a worksheet containing:

- the configured `device_type_header` (normally `Device Type`);
- each configured serialized-item header, such as `Cybernet Serial` or `Neuron S/N`.

An explicit worksheet may be provided in the site config. Otherwise the first worksheet containing all required headers is selected.

### Site config

Validate against:

`configs/device_transfer_signoff/site-config.schema.json`

Required site fields:

- name;
- code;
- address;
- point of contact;
- delivery date (`YYYY-MM-DD`);
- delivery time;
- origin;
- prepared by;
- sign-off ID.

`shipment` is an ordered list of exact rows. Each row requires `item` and positive integer `qty`. A serialized row also requires both `serial_source` and `serial_header`.

At most two serialized shipment classes are supported by the one-page drawbox layout.

## Outputs

Default output directory:

`Outputs/device_transfer_signoff/`

For site code `SITE` and date `2026-07-28`:

```text
SITE_Device_Transfer_SignOff_20260728.xlsx
SITE_Device_Transfer_SignOff_20260728_manifest.json
SITE_Device_Transfer_SignOff_20260728_preflight.json
```

Generated outputs are gitignored runtime artifacts. Do not write them to `Candidates/` or `Active/`.

## Workbook contract

Exactly one sheet:

`Sign-Off`

Required surfaces, in order:

1. title and delivery/sign-off metadata;
2. transfer details;
3. exact shipment register;
4. zero, one, or two serialized device drawboxes;
5. verification / exceptions;
6. signatures.

The workbook is values-only: no formulas, external links, calc chain, or worksheet `inlineStr` cells after the repository's existing inline-string repair runs.

The workbook uses calm dark/slate headers and a muted blue accent, following the repository visual-design doctrine. It is configured landscape and fit-to-one-page for field printing.

## CLI

```powershell
python -m triage.device_transfer_signoff_cli `
  --source-configs "Candidates\signoffs\Bayshore\configs.xlsx" `
  --site-config "Candidates\signoffs\Bayshore\site-config.json" `
  --out-dir "Outputs\device_transfer_signoff"
```

Validate independently:

```powershell
python -m triage.device_transfer_signoff_validator `
  --workbook "Outputs\device_transfer_signoff\<generated>.xlsx" `
  --source-configs "Candidates\signoffs\Bayshore\configs.xlsx" `
  --site-config "Candidates\signoffs\Bayshore\site-config.json" `
  --json-out "Outputs\device_transfer_signoff\validation.json"
```

The operator supplies Bayshore's private site config and source workbook at runtime. The public repository must not hard-code real site contacts, addresses, serials, or shipment quantities.

## Acceptance gates

Generation is accepted at repository level only when:

- exact shipment rows equal the site config in order and quantity;
- every serialized item quantity equals the source serial count;
- serialized values in the workbook equal source values exactly;
- no unconfigured shipment item appears;
- package ZIP test passes;
- workbook has exactly one `Sign-Off` sheet;
- formula count is zero;
- `inlineStr`, calc chain, and external-link package parts are absent;
- required metadata is nonblank;
- focused tests and independent validator pass;
- manifest contains artifact SHA-256 and proof ceiling.

Excel for Web opening, print appearance, signatures, physical count, and handoff acceptance remain separate operator/runtime gates.
