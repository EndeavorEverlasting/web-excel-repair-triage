from __future__ import annotations

from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_ooxml_base as ooxml


MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
X14AC_NS = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"
X15_NS = "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main"
XR_NS = "http://schemas.microsoft.com/office/spreadsheetml/2014/revision"
XR2_NS = "http://schemas.microsoft.com/office/spreadsheetml/2015/revision2"
XR3_NS = "http://schemas.microsoft.com/office/spreadsheetml/2016/revision3"
XR6_NS = "http://schemas.microsoft.com/office/spreadsheetml/2016/revision6"
XR10_NS = "http://schemas.microsoft.com/office/spreadsheetml/2016/revision10"


def test_v39_declares_unused_excel_prefixes_referenced_by_mc_ignorable() -> None:
    # Only xr is structurally used. x14ac/xr2/xr3 must still be declared because
    # Excel references them semantically through mc:Ignorable.
    worksheet = ET.Element(
        f"{{{ooxml.MAIN_NS}}}worksheet",
        {
            f"{{{MC_NS}}}Ignorable": "x14ac xr xr2 xr3",
            f"{{{XR_NS}}}uid": "{00000000-0001-0000-0100-000000000000}",
        },
    )

    serialized = ooxml._xml(worksheet).decode("utf-8")

    assert 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"' in serialized
    assert f'xmlns:mc="{MC_NS}"' in serialized
    assert f'xmlns:x14ac="{X14AC_NS}"' in serialized
    assert f'xmlns:xr="{XR_NS}"' in serialized
    assert f'xmlns:xr2="{XR2_NS}"' in serialized
    assert f'xmlns:xr3="{XR3_NS}"' in serialized
    assert 'mc:Ignorable="x14ac xr xr2 xr3"' in serialized
    assert "ns0:" not in serialized


def test_v39_declares_unused_workbook_revision_prefixes() -> None:
    # xr is used, while x15/xr6/xr10/xr2 are represented only by Ignorable.
    workbook = ET.Element(
        f"{{{ooxml.MAIN_NS}}}workbook",
        {
            f"{{{MC_NS}}}Ignorable": "x15 xr xr6 xr10 xr2",
            f"{{{XR_NS}}}uid": "{00000000-0000-0000-0000-000000000000}",
        },
    )

    serialized = ooxml._xml(workbook).decode("utf-8")

    for prefix, uri in {
        "x15": X15_NS,
        "xr": XR_NS,
        "xr6": XR6_NS,
        "xr10": XR10_NS,
        "xr2": XR2_NS,
    }.items():
        assert f'xmlns:{prefix}="{uri}"' in serialized
    assert 'mc:Ignorable="x15 xr xr6 xr10 xr2"' in serialized
    assert "ns0:" not in serialized


def test_v39_uses_default_namespaces_for_package_roots() -> None:
    content_types = ET.Element(f"{{{ooxml.CONTENT_TYPES_NS}}}Types")
    relationships = ET.Element(f"{{{ooxml.PKG_REL_NS}}}Relationships")

    content_types_xml = ooxml._xml(content_types).decode("utf-8")
    relationships_xml = ooxml._xml(relationships).decode("utf-8")

    assert f'<Types xmlns="{ooxml.CONTENT_TYPES_NS}"' in content_types_xml
    assert f'<Relationships xmlns="{ooxml.PKG_REL_NS}"' in relationships_xml
    assert "ns0:" not in content_types_xml
    assert "ns0:" not in relationships_xml
