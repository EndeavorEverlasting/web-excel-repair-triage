"""Neuron task-hour distribution rules.

Conservative rules for turning roster-backed Neuron hours into task lanes.
Ordinary 9-to-6 Neuron work is support by default, not deployment by default.
Deployment classification requires explicit evidence or a private/local override.
Client-facing Neuron Track Hours should not expose internal distributed-hour helper columns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Mapping, Optional

CONFIGURATIONS = "Configurations"
DEPLOYMENTS = "Deployments"
LOGISTICS = "Logistics"
INVENTORY_MANAGEMENT = "Inventory Management"
DOCUMENTATION = "Documentation"
CLIENT_COORDINATION = "Client Coordination"
TICKET_FORWARDING = "Ticket Forward