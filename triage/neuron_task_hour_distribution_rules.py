from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping

CONFIGURATIONS = "Configurations"
DEPLOYMENTS = "Deployments"
LOGISTICS = "Logistics"
INVENTORY_MANAGEMENT = "Inventory Management"
DOCUMENTATION = "Documentation"
CLIENT_COORDINATION = "Client Coordination"
TICKET_FORWARDING = "Ticket Forwarding"
TROUBLESHOOTING = "Troubleshooting / Incident Response"
WAREHOUSE_MAINTENANCE = "Warehouse Maintenance"
SURVEY = "Survey"

# Conservative default: weekday Neuron support is not deployment-heavy.
# The public repo must not infer