# Use Case: Rezaul Roman Neuron Project Attribution

Captured: 2026-06-03

## Problem

Rezaul Roman's hours should be attributed to the Neuron project when the updated tracker marks him that way. Otherwise his hours may be missed or excluded because he is not tracked through the same path as the standard Neuron team.

## Required behavior

The billing generator must support explicit project attribution from the latest validated tracker.

If the latest tracker marks Rezaul Roman as Neuron project work, then the generated billing summaries must include those hours under Neuron unless a stronger approved exception says otherwise.

## Source priority

Use this order:

1. Approved manual override
2. Latest validated roster/tracker project attribution
3. Worked Projects tab
4. Note-derived project evidence
5. Default assignment rules

## Do not infer silently

Do not include Rezaul Roman in Neuron just because the name exists. The inclusion must come from:

- updated tracker data
- approved override
- explicit project assignment table

## Output behavior

Share-ready billing summary should include Rezaul Roman's hours in Neuron totals when validated.

Internal review should preserve evidence:

- source tab
- source row or date span when available
- project attribution reason
- override status

## Test expectations

Synthetic tests should cover:

- Rezaul absent from project assignment: not included by default
- Rezaul explicitly mapped to Neuron: included
- Rezaul mapped to a non-Neuron project: excluded from Neuron
- approved override beats default assignment

## Practical rule

If Rezaul Roman's latest tracker data was updated, regenerate from that source. Do not guess from stale workbook state.
