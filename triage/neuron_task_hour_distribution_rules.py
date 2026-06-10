"""Neuron task-hour distribution rules.

Rules for turning roster-backed Neuron hours into task lanes.
Ordinary 9-to-6 Neuron work is support by default, not deployment by default.
Deployment classification requires explicit evidence or a local override.
Client-facing Neuron Track Hours must not expose internal distributed-hour helper columns.
"""
from __future