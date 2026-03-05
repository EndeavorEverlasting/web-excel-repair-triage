"""tests/test_insight_ingest.py

External XML insight ingestion copies artifacts into Outputs/ and deduplicates.
"""

from __future__ import annotations

from pathlib import Path

from triage.insight_ingest import ingest_xml_insights, parse_recovery_log


def test_parse_recovery_log_extracts_source_and_records():
    xml = """<?xml version='1.0'?>
    <recoveryLog>
      <summary>Errors were detected in file 'C:\\X\\Deprecated\\Book1.xlsx'</summary>
      <repairedRecords>
        <repairedRecord>Repaired Records: /xl/worksheets/sheet1.xml</repairedRecord>
      </repairedRecords>
    </recoveryLog>
    """
    d = parse_recovery_log(xml)
    assert d["kind"] == "excel_recovery_log"
    assert d["source_workbook_path"].endswith("Book1.xlsx")
    assert d["repaired_records"]


def test_ingest_xml_insights_copies_and_dedupes(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    ext = tmp_path / "external"
    ext.mkdir()
    xml_path = ext / "error123.xml"
    xml_path.write_text(
        "<recoveryLog><summary>Errors were detected in file 'C:/X/Deprecated/A.xlsx'</summary></recoveryLog>",
        encoding="utf-8",
    )

    r1 = ingest_xml_insights([ext], max_files=50)
    assert r1.copied == 1
    assert Path(r1.report_path).exists()
    assert any(i.dest_path for i in r1.insights)

    r2 = ingest_xml_insights([ext], max_files=50)
    assert r2.copied == 0
    assert r2.skipped_duplicates >= 1
