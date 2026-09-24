"""Synthetic roster for the Bonita Neuron Track Hours generator tests.

One workbook with Live / Worked Projects / Assignments tabs for April and May,
engineered to exercise every inclusion and exclusion branch of the resolver:

April (counted shifts):
  Alpha Tech   Apr 01  9h   default Neuron (full-month start)
  Alpha Tech   Apr 30  8h   default Neuron (full-month end; proves span > Apr 1-4)
  Bravo Tech   Apr 03  8h   note-bearing punch (note must not leak to cells)
  Delta Tech   Apr 02  8h   default Delivery, Worked-Projects override -> Neuron
  Foxtrot Tech Apr 03  8h   Neuron, Delivery/Transport activity sub-label
  Hotel Tech   Apr 15  17h  long shift (counted + flagged)
  India Tech   Apr 02  8h   default Delivery, Assignments override -> Neuron
  => 7 rows, 66.0h

April (excluded, recorded in review):
  Charlie Tech Apr 01  / Bonita off-project coverage punch
  Echo Tech    Apr 02  default Neuron, Worked-Projects override -> Delivery
  Golf Tech    Apr 04  PTO non-work marker
  Yostinn Minaya Apr 01  excluded name

May (counted shifts):
  Alpha Tech   May 01  8h
  Bravo Tech   May 02  8h
  => 2 rows, 16.0h
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook


def write_bonita_roster(path: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    # ── Live - April 2026 ────────────────────────────────────────────
    apr = wb.create_sheet("Live - April 2026")
    apr.append(["April 2026 - Attendance"])
    apr.append([
        "Staff Name", "Project",
        "Apr 01 - Clock In", "Apr 01 - Clock Out",
        "Apr 02 - Clock In", "Apr 02 - Clock Out",
        "Apr 03 - Clock In", "Apr 03 - Clock Out",
        "Apr 04 - Clock In", "Apr 04 - Clock Out",
        "Apr 15 - Clock In", "Apr 15 - Clock Out",
        "Apr 30 - Clock In", "Apr 30 - Clock Out",
    ])
    # Alpha: full-month bookends.
    apr.append(["Alpha Tech", "Neuron Deployments",
                "9:00 AM", "6:00 PM", "", "", "", "", "", "", "", "",
                "8:00 AM", "4:00 PM"])
    # Bravo: note-bearing punch on Apr 03.
    apr.append(["Bravo Tech", "Neuron Deployments",
                "", "", "", "", "8:00 AM", "4:00 PM - lunch covered",
                "", "", "", "", "", ""])
    # Charlie: off-project / Bonita coverage punch on Apr 01.
    apr.append(["Charlie Tech", "Neuron Deployments",
                "9:00:00 AM/ Bonita", "1:00 PM", "", "", "", "",
                "", "", "", "", "", ""])
    # Delta: default Delivery, override-to-Neuron via Worked Projects on Apr 02.
    apr.append(["Delta Tech", "Delivery / Transport",
                "", "", "7:00 AM", "3:00 PM", "", "", "", "", "", "", "", ""])
    # Echo: default Neuron, override-away-from-Neuron via Worked Projects Apr 02.
    apr.append(["Echo Tech", "Neuron Deployments",
                "", "", "9:00 AM", "5:00 PM", "", "", "", "", "", "", "", ""])
    # Foxtrot: Neuron with a Delivery/Transport activity note on Apr 03.
    apr.append(["Foxtrot Tech", "Neuron Deployments",
                "", "", "", "", "6:00 AM", "2:00 PM - Delivery / Transport",
                "", "", "", "", "", ""])
    # Golf: PTO non-work marker on Apr 04.
    apr.append(["Golf Tech", "Neuron Deployments",
                "", "", "", "", "", "", "PTO", "", "", "", "", ""])
    # Hotel: long shift on Apr 15.
    apr.append(["Hotel Tech", "Neuron Deployments",
                "", "", "", "", "", "", "", "", "6:00 AM", "11:00 PM", "", ""])
    # Yostinn Minaya: excluded name (never counted).
    apr.append(["Yostinn Minaya", "Neuron Deployments",
                "9:00 AM", "6:00 PM", "", "", "", "", "", "", "", "", "", ""])
    # India: default Delivery, Assignments-override-to-Neuron on Apr 02.
    apr.append(["India Tech", "Delivery / Transport",
                "", "", "8:00 AM", "4:00 PM", "", "", "", "", "", "", "", ""])

    # ── Worked Projects - April 2026 ─────────────────────────────────
    wapr = wb.create_sheet("Worked Projects - April 2026")
    wapr.append(["April 2026 - Worked Projects"])
    wapr.append(["Staff Name", "Default Project",
                 datetime(2026, 4, 2), datetime(2026, 4, 3)])
    wapr.append(["Delta Tech", "Delivery / Transport", "Neuron Deployments", ""])
    wapr.append(["Echo Tech", "Neuron Deployments", "Delivery / Transport", ""])

    # ── Assignments - April 2026 ─────────────────────────────────────
    aapr = wb.create_sheet("Assignments - April 2026")
    aapr.append(["Staff Name", datetime(2026, 4, 2)])
    aapr.append(["India Tech", "Neuron Deployments"])

    # ── Live - May 2026 ──────────────────────────────────────────────
    may = wb.create_sheet("Live - May 2026")
    may.append(["May 2026 - Attendance"])
    may.append([
        "Staff Name", "Project",
        "May 01 - Clock In", "May 01 - Clock Out",
        "May 02 - Clock In", "May 02 - Clock Out",
    ])
    may.append(["Alpha Tech", "Neuron Deployments", "8:00 AM", "4:00 PM", "", ""])
    may.append(["Bravo Tech", "Neuron Deployments", "", "", "9:00 AM", "5:00 PM"])

    wmay = wb.create_sheet("Worked Projects - May 2026")
    wmay.append(["May 2026 - Worked Projects"])
    wmay.append(["Staff Name", "Default Project", datetime(2026, 5, 1)])
    wmay.append(["Alpha Tech", "Neuron Deployments", ""])

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def build_bonita_fixtures(base: Path) -> dict:
    base.mkdir(parents=True, exist_ok=True)
    roster = base / "bonita_roster.xlsx"
    write_bonita_roster(roster)
    return {"roster": roster}
