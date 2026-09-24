# Deployment Tracker Reorganization and Fix Plan

## 1. File Reorganization
**Current State**: The tracker (`Active Deployment Tracker 2026-04-20.xlsx`) is stored in `Automate Billing Summary/raw data/`. 
**Issue**: As observed, this document contains deployment data rather than billing data, making its current location misleading and disorganized.
**Action**: Move `Active Deployment Tracker 2026-04-20.xlsx` to a more appropriate directory, such as `Active/` or `raw data/` at the root level, out of the billing folder. Update any references in scripts or documentation that expect it in the old location.

## 2. Fixing the Duplicate Formula
**Current State**: The `DupDeployed` formula in the `Deployments` tab is broken. Currently, it likely flags duplicates too aggressively without considering deployment status and location.
**New Logic Requirements**:
- A duplicate is only considered "real" if BOTH instances have `Deployed` = "Yes".
- BOTH instances must share the same unique identifier (e.g., Serial Number).
- They must be deployed in *different locations*. (Same identifier in two locations at the same time is an error).
**Action**: 
- Identify the exact unique identifiers used in the tracker (e.g. `Neuron S/N`, `Cybernet Serial`, etc.)
- Identify the location columns (e.g. `Current Building`, `Room`).
- Write a Python script using `openpyxl` that iterates over the `Deployments` sheet.
- Update the formula in the `DupDeployed` column to reflect this new logic, e.g., using an Excel `COUNTIFS` that checks for same Identifier, Deployed="Yes", and Location condition, or write a Python macro that does this programmatically.
- Save the repaired tracker and ensure it does not break other formulas.

## 3. Tooling to Make New Trackers and Correct Broken Formulas
**Current State**: The environment contains some `autofix_loop.py` triage engine, but we need tooling specifically for tracker generation and formula correction.
**Action**: 
- Develop a Python utility (`tracker_tooling.py`) that can:
  1. Instantiate new deployment trackers from a template.
  2. Correct specific broken formulas dynamically (e.g. `DupDeployed`) across an entire sheet.
  3. Abstract this logic so it can be called programmatically for future trackers.

## Next Steps
- Execute file move.
- Run Python script to read the existing formulas and apply the `COUNTIFS` fix.
- Create `tracker_tooling.py` for future operations.
