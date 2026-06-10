"""Neuron task-hour distribution rules.

The roster proves who worked and when, but it usually does not prove the exact
intra-day Neuron task mix. These rules make the generator choose conservative,
repeatable task lanes when event-level evidence is thin.

Important posture: ordinary 9-to-6 Neuron work is support by default, not field
deployment by default. Deployment classification requires explicit evidence or a
private/local override. Client-facing Neuron Track Hours should stay clean and
should not expose internal-only distributed-hour helper columns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable