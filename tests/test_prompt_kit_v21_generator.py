import hashlib
import os
from pathlib import Path

import pytest

from triage.prompt_kit_contract import validate_prompt_kit_contract
from triage.prompt_kit_v21_generator import generate_v21
from triage.prompt_kit_v21_repair_regressions import validate_repair_regressions

V20_BUNDLE_ENV = "AI_PROMPT_KIT_V20_BUNDLE"
V21_EXPECTED_HASH = "47cfe3ca37f5ebba4ac056ee001d2dad69bd4dee81d7b7be0f7cf83affe4ba9b"


def test_generator_deterministic_output(tmp_path):
    configured_path = os.environ.get(V20_BUNDLE_ENV)
    if not configured_path:
        pytest.skip(
            f"Set {V20_BUNDLE_ENV} to the private authoritative V20 bundle to run exact generation parity."
        )

    v20_bundle_path = Path(configured_path)
    if not v20_bundle_path.exists():
        pytest.fail(f"Configured source V20 bundle does not exist: {v20_bundle_path}")

    generate_v21(v20_bundle_path, tmp_path)

    v21_xlsx = tmp_path / "AI_Harness_Prompt_Kit_v21.xlsx"
    assert v21_xlsx.exists()
    assert hashlib.sha256(v21_xlsx.read_bytes()).hexdigest() == V21_EXPECTED_HASH

    v21_bundle = tmp_path / "AI_Harness_Prompt_Kit_v21_bundle.zip"
    assert v21_bundle.exists()

    contract_report = validate_prompt_kit_contract(v21_xlsx, "v21")
    assert contract_report.contract_valid, contract_report.to_dict()

    repair_report = validate_repair_regressions(v21_xlsx)
    assert repair_report["valid"], repair_report["errors"]
