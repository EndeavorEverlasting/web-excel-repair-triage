# July NTH Public-Disclosure Producer State — 2026-08-04

## Scope

July share-ready NTH workbook only. No May artifact behavior is changed.

## Upstream contract

- FUN policy: `fun-july-nth-public-disclosure-policy/v1`
- Pinned schema blob: `836e1bb5af0bd7ddd329cef62f7a76baa48fff01`
- Merged source commit: `454b2563d90773f6de635026df979e3c8ead18af`

## Producer behavior

- consumes the complete FUN result and matching policy;
- fails on any public-disclosure, package, math-lock, or scope violation;
- reports rule IDs and locations without repeating protected workbook text;
- scans its own JSON and Markdown output against the protected rules;
- does not independently reinterpret July math.

## Current repaired artifact

- Drive file ID: `1i-cMvf20h8V4vkv7K0GjnbUQC6cu5Dv9`
- SHA-256: `83791d1a0cf28c69000b4c2603968cf9cccaa9e3b72f5ca685fa214d36cffeec`
- Size: `18484` bytes
- FUN disclosure rules: `10`, violations `0`
- FUN numeric locks: `27`, violations `0`

## Boundary

The producer report establishes safe report generation from a passing FUN result. It does not substitute for the FUN byte scan or existing July math and artifact validators.
