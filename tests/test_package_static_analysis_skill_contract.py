from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/package-static-analysis/SKILL.md"
DOC = ROOT / "docs/PACKAGE_STATIC_ANALYSIS_ADOPTION.md"
WORKFLOW = ROOT / ".github/workflows/package-static-analysis-skill.yml"


def read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_skill_uses_sysadminsuite_as_canonical_authority() -> None:
    text = read(SKILL)
    for fragment in (
        "EndeavorEverlasting/SysAdminSuite",
        "harness/api/package-static-analysis-skill.json",
        "schemas/harness/package-static-analysis-result.schema.json",
        "tools/package-analysis/analyze_package.py",
        "scripts/Invoke-SasPackageStaticAnalysis.ps1",
    ):
        assert fragment in text
    assert "must not fork the analyzer" in text.lower()


def test_static_only_and_private_data_boundaries_are_explicit() -> None:
    combined = read(SKILL) + "\n" + read(DOC)
    required = (
        "static-only",
        "never commit private installers",
        "never follow shortcuts",
        "never mark a package safe",
        "authorized VM/runtime lane",
        "endpoint",
        "proof ceiling",
    )
    lowered = combined.lower()
    for fragment in required:
        assert fragment.lower() in lowered
    for forbidden in ("msiexec /i", "start-process", "subprocess.run", "invoke-webrequest", "pip install pefile"):
        assert forbidden not in lowered


def test_adoption_doc_names_offline_venv_and_evidence_contract() -> None:
    text = read(DOC)
    assert "-CreateVenv" in text
    assert "-OfflineWheelhouse" in text
    assert "--no-index --find-links" in text
    assert "package_analysis.json" in text
    assert "sas-package-static-analysis/v1" in text
    assert "every execution, extraction, network, mutation, trust, and runtime proof flag is false" in text


def test_workflow_runs_this_contract() -> None:
    text = read(WORKFLOW)
    assert "ubuntu-latest" in text
    assert "python -m pytest tests/test_package_static_analysis_skill_contract.py" in text


def test_documents_do_not_contain_client_package_values() -> None:
    combined = read(SKILL) + "\n" + read(DOC)
    forbidden = ("nt2kwb", "nslijhs", "northwell", "defaultpassword", "bearer ", "api_key")
    lowered = combined.lower()
    for value in forbidden:
        assert value not in lowered
