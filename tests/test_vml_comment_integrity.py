from __future__ import annotations

import zipfile
from pathlib import Path

from triage.vml_comment_integrity import repair_vml_comment_collisions, scan_vml_comment_integrity


VML_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing"
COMMENTS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"


def _rels(vml_target: str, comments_target: str) -> str:
    return (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{VML_REL}" Target="{vml_target}"/>'
        f'<Relationship Id="rId2" Type="{COMMENTS_REL}" Target="{comments_target}"/>'
        '</Relationships>'
    )


def _vml(data: int, *shape_ids: int) -> str:
    shapes = "".join(
        f'<v:shape id="_x0000_s{shape_id}" type="#_x0000_t202">'
        '<x:ClientData ObjectType="Note"><x:Row>1</x:Row><x:Column>1</x:Column></x:ClientData>'
        '</v:shape>'
        for shape_id in shape_ids
    )
    return (
        '<xml xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:x="urn:schemas-microsoft-com:office:excel">'
        f'<o:shapelayout v:ext="edit"><o:idmap v:ext="edit" data="{data}"/></o:shapelayout>'
        f'{shapes}</xml>'
    )


def _make_xlsx(path: Path, *, collision: bool) -> None:
    second_data = 1 if collision else 4
    second_shapes = (1026, 1027) if collision else (4097, 4098)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "xl/worksheets/_rels/sheet1.xml.rels",
            _rels("../drawings/vmlDrawing1.vml", "../comments1.xml"),
        )
        z.writestr(
            "xl/worksheets/_rels/sheet2.xml.rels",
            _rels("../drawings/vmlDrawing2.vml", "../comments2.xml"),
        )
        z.writestr("xl/drawings/vmlDrawing1.vml", _vml(1, 1026, 1027, 1028))
        z.writestr("xl/drawings/vmlDrawing2.vml", _vml(second_data, *second_shapes))
        z.writestr("xl/comments1.xml", "<comments/>")
        z.writestr("xl/comments2.xml", "<comments/>")


def test_collision_pair_is_stopship_signal(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    _make_xlsx(candidate, collision=True)

    report = scan_vml_comment_integrity(candidate)

    assert not report.pass_all
    kinds = [finding.kind for finding in report.findings]
    assert kinds.count("duplicate_vml_shape_id") == 2
    assert kinds.count("duplicate_vml_idmap_data") == 1
    assert {finding.value for finding in report.findings if finding.kind == "duplicate_vml_shape_id"} == {
        "_x0000_s1026",
        "_x0000_s1027",
    }


def test_reindexed_pair_passes(tmp_path: Path) -> None:
    repaired = tmp_path / "repaired.xlsx"
    _make_xlsx(repaired, collision=False)

    report = scan_vml_comment_integrity(repaired)

    assert report.pass_all
    assert report.findings == []


def test_absolute_relationship_targets_are_resolved_for_inventory(tmp_path: Path) -> None:
    candidate = tmp_path / "absolute-targets.xlsx"
    with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "xl/worksheets/_rels/sheet1.xml.rels",
            _rels("/xl/drawings/commentsDrawing1.vml", "/xl/comments/comment1.xml"),
        )
        z.writestr("xl/drawings/commentsDrawing1.vml", _vml(1, 1026))
        z.writestr("xl/comments/comment1.xml", "<comments/>")

    report = scan_vml_comment_integrity(candidate)

    assert report.pass_all
    vml_note = next(note for note in report.relationship_notes if note["relationship"] == "vmlDrawing")
    assert vml_note["absolute_target"] is True
    assert vml_note["resolved"] == "xl/drawings/commentsDrawing1.vml"
    assert vml_note["exists"] is True


def test_bounded_repair_reindexes_later_colliding_vml_part(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _make_xlsx(candidate, collision=True)

    result = repair_vml_comment_collisions(candidate, repaired)
    post = scan_vml_comment_integrity(repaired)

    assert result["post_pass"] is True
    assert len(result["reindexed_parts"]) == 1
    assert post.pass_all
    assert post.vml_parts[0].shape_ids == ("_x0000_s1026", "_x0000_s1027", "_x0000_s1028")
    assert post.vml_parts[1].shape_ids[0] != "_x0000_s1026"
    assert post.vml_parts[1].idmap_data != ("1",)
