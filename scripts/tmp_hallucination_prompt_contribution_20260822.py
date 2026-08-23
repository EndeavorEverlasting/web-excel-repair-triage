#!/usr/bin/env python3
"""Temporary bootstrap for the hallucination Prompt Kit contribution.

The durable contribution is produced by the repository helper and committed separately.
This file is removed before integration.
"""
from __future__ import annotations

import subprocess

SOURCE_COMMIT = "6eb0d5e82216314596eaa324d3d33aca0318efc5"
SOURCE_PATH = "scripts/tmp_hallucination_prompt_contribution_20260822.py"

text = subprocess.check_output(
    ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True
)
start = text.index('    p83_section = """')
end = text.index(
    '    for keyword in ("faithfulness hallucination", "ignored provided context"):',
    start,
)
replacement = '''    if "CHECK SOURCE FAITHFULNESS" not in p83["copyContent"]:
        old_mission = "Act as the next responsible agent, not a passive reviewer. Recover what the previous agent said it changed, compare those claims with current source-of-truth evidence, preserve the parts that are actually correct, repair what is wrong, finish what is incomplete, and expand the implementation only when current evidence exposes a safe useful in-scope improvement. Continue through validation and integration instead of stopping at commentary."
        new_mission = "Act as the next responsible agent, not a passive reviewer. Compare the prior agent's claims with current source-of-truth evidence; preserve correct work, repair errors, finish omissions, and make only evidence-earned in-scope improvements. Continue through validation and integration instead of stopping at commentary."
        old_claims = "2. TREAT CLAIMS AS HYPOTHESES\\nBuild a compact claim-to-evidence view for every material assertion such as `implemented`, `fixed`, `tested`, `clean`, `pushed`, `merged`, `deployed`, or `complete`. Classify each as VERIFIED, STALE, PARTIAL, CONTRADICTED, or UNPROVEN using current evidence. Another agent's green test/live run is historical evidence. Re-derive impacted regression controls; for runtime claims, run the canonical path yourself when safe or keep them UNPROVEN with the exact gate."
        new_claims = "2. TREAT CLAIMS AS HYPOTHESES / CHECK SOURCE FAITHFULNESS\\nBuild a compact claim-to-evidence view for material assertions and classify each as VERIFIED, STALE, PARTIAL, CONTRADICTED, or UNPROVEN. For a wrong claim, compare it with authoritative information available to that agent: missing truth is a factuality gap; present-but-ignored truth is a faithfulness hallucination. For faithfulness, re-anchor/compact the authoritative context before fetching more; for factuality, retrieve the missing source. Re-derive regression controls; run safe runtime proof yourself or keep it UNPROVEN."
        if p83["copyContent"].count(old_mission) != 1 or p83["copyContent"].count(old_claims) != 1:
            raise RuntimeError("P83 compaction anchor mismatch")
        p83["copyContent"] = p83["copyContent"].replace(old_mission, new_mission, 1).replace(old_claims, new_claims, 1)
'''
text = text[:start] + replacement + text[end:]
exec(compile(text, SOURCE_PATH, "exec"), globals(), globals())
