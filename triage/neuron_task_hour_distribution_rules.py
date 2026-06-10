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
PROJECT_SUPPORT = "Project Support"

APRIL_DEPLOYMENT_DATES = {date(2026, 4, 4), date(2026, 4, 11)}
APRIL_LOOSE_DEPLOYMENT_WEEKDAYS = {0, 2}  # Monday, Wednesday
AFTER