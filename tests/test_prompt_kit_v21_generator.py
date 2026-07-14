import hashlib
import os
from pathlib import Path
from triage.prompt_kit_v21_generator import generate_v21
from triage.prompt_kit_contract import validate_prompt_kit_contract
from triage.prompt_kit_v21_repair_regressions import validate_repair_regressions

V20_BUNDLE_PATH = Path(os.environ.get("AI_PROMPT_KIT_V20_BUNDLE", "C:/Users/Cheex/Downloads/AI_Harness_Prompt_Kit_v20_bundle.zip"))
V21_EXPECTED_HASH = "47cfe3ca37f5ebba4ac056ee001d2dad69bd4dee81d7b7be0f7cf83affe4ba9b"


def test_generator_deterministic_output(tmp_path):
    # Ensure V20 source bundle exists in downloads
    assert V20_BUNDLE_PATH.exists(), f"Source V20 bundle not found at {V20_BUNDLE_PATH}"

    # Run generator
    generate_v21(V20_BUNDLE_PATH, tmp_path)

    # Verify generated workbook exists and matches exact SHA-256
    v21_xlsx = tmp_path / "AI_Harness_Prompt_Kit_v21.xlsx"
    assert v21_xlsx.exists()

    with open(v21_xlsx, "rb") as f:
        v21_hash = hashlib.sha256(f.read()).hexdigest()
    assert v21_hash == V21_EXPECTED_HASH

    # Verify generated bundle exists
    v21_bundle = tmp_path / "AI_Harness_Prompt_Kit_v21_bundle.zip"
    assert v21_bundle.exists()

    # Run contract check on generated workbook
    contract_report = validate_prompt_kit_contract(v21_xlsx, "v21")
    assert contract_report.contract_valid, contract_report.to_dict()

    # Run repair regression check on generated workbook
    repair_report = validate_repair_regressions(v21_xlsx)
    assert repair_report["valid"], repair_report["errors"]
