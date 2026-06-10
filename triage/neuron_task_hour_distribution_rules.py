"""Neuron task-hour distribution rules.

Roster-backed Neuron hours are support work by default. Deployment is only used
when explicit evidence or a local override proves field deployment work.
Client-facing outputs must not expose internal distributed-hour helper columns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Mapping, Optional

CONFIGURATIONS = "Configurations"
DEPLOYMENTS = "Deploy