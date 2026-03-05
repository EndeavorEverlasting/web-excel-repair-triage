"""tests/test_storage_policy.py

Default budget computation should be deterministic given free space.
"""

from __future__ import annotations


from triage.storage_policy import GiB, compute_default_budget_bytes


def test_compute_default_budget_big_disk():
    # 100GiB free -> 5% = 5GiB (cap 10GiB)
    assert compute_default_budget_bytes(100 * GiB) == 5 * GiB


def test_compute_default_budget_medium_disk():
    # 20GiB free -> 10% = 2GiB (cap 5GiB)
    assert compute_default_budget_bytes(20 * GiB) == 2 * GiB


def test_compute_default_budget_small_disk():
    # 5GiB free -> 10% = 0.5GiB (cap 1GiB)
    assert compute_default_budget_bytes(5 * GiB) == int(0.5 * GiB)
