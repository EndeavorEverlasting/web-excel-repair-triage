"""triage/storage_policy.py
-------------------------
Storage budgeting helpers for Outputs/ and other derived-artifact areas.

Design goals
------------
- Default budget should adapt to the user's available disk space.
- Be conservative for users with small disks, but generous enough for normal use.
- Enforcement should be *safe by default*: prefer skipping new artifact copies
  over deleting existing artifacts automatically.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from triage.path_policy import repo_root


GiB = 1024**3


def disk_free_bytes(path: str | Path | None = None) -> int:
    p = Path(path) if path is not None else repo_root()
    if not p.is_absolute():
        p = (repo_root() / p).resolve(strict=False)
    return int(shutil.disk_usage(str(p)).free)


def compute_default_budget_bytes(free_bytes: int) -> int:
    """Compute a sensible default budget for derived artifacts.

    Heuristic:
    - If plenty of space: use a small % of free space.
    - Cap the budget so Outputs/ doesn't grow unbounded.
    """
    free_bytes = int(max(0, free_bytes))
    if free_bytes >= 50 * GiB:
        # Big disk: 5% of free, up to 10GiB
        return int(min(10 * GiB, free_bytes * 0.05))
    if free_bytes >= 10 * GiB:
        # Medium disk: 10% of free, up to 5GiB
        return int(min(5 * GiB, free_bytes * 0.10))
    # Small disk: 10% of free, up to 1GiB
    return int(min(1 * GiB, free_bytes * 0.10))


def default_outputs_budget_bytes(path: str | Path | None = None) -> int:
    return compute_default_budget_bytes(disk_free_bytes(path))


def dir_size_bytes(path: str | Path) -> int:
    p = Path(path)
    if not p.is_absolute():
        p = repo_root() / p
    p = p.resolve(strict=False)
    if not p.exists():
        return 0
    total = 0
    for f in p.rglob("*"):
        try:
            if f.is_file():
                total += int(f.stat().st_size)
        except Exception:
            continue
    return int(total)


@dataclass(frozen=True)
class BudgetStatus:
    root: str
    used_bytes: int
    budget_bytes: int

    @property
    def remaining_bytes(self) -> int:
        return max(0, int(self.budget_bytes) - int(self.used_bytes))

    @property
    def over_budget(self) -> bool:
        return int(self.used_bytes) > int(self.budget_bytes)


def budget_status(root: str | Path, budget_bytes: int) -> BudgetStatus:
    r = Path(root)
    if not r.is_absolute():
        r = (repo_root() / r).resolve(strict=False)
    used = dir_size_bytes(r)
    return BudgetStatus(root=str(r), used_bytes=int(used), budget_bytes=int(budget_bytes))
