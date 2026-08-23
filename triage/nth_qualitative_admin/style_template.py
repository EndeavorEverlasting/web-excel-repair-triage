"""Canonical style table for the June/August qualitative-admin NTH family."""
from __future__ import annotations

from xml.sax.saxutils import escape

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

_FONTS = [
    '<font><sz val="11"/><name val="Carlito"/></font>',
    '<font><b/><sz val="16"/><color rgb="FFFFFFFF"/><name val="Carlito"/></font>',
    '<font><i/><sz val="10"/><color rgb="FF4B5563"/><name val="Carlito"/></font>',
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Carlito"/></font>',
    '<font><b/><sz val="15"/><name val="Carlito"/></font>',
    '<font><b/><sz val="11"/><color rgb="FF1F2937"/><name val="Carlito"/></font>',
    '<font><b/><sz val="11"/><name val="Carlito"/></font>',
    '<font><b/><sz val="9"/><color rgb="FFFFFFFF"/><name val="Carlito"/></font>',
    '<font><b/><sz val="14"/><name val="Carlito"/></font>',
    '<font><b/><sz val="13"/><name val="Carlito"/></font>',
]
_FILL_COLORS = [None, "gray125", "FF173B5C", "FFF3F5F7", "FFDCEAF7", "FFDDEED9",
                "FFFFF1BF", "FF173B5C", "FFDCEAF7", "FFDDEED9", "FFFFF1BF",
                "FF173B5C", "FFDDEED9", "FFFFF1BF"]

_USED_XFS: dict[int, tuple[int,int,int,int,dict[str,str] | None]] = {
    4:(0,1,2,0,None), 10:(0,2,3,0,{"wrapText":"1"}), 12:(0,3,2,0,None),
    48:(0,5,4,2,None),49:(0,5,4,3,None),50:(0,5,4,4,None),
    51:(0,0,0,5,None),52:(200,0,0,6,None),53:(0,0,0,7,None),
    54:(0,6,5,8,None),55:(200,6,5,9,None),56:(0,6,5,10,None),
    68:(0,0,0,5,{"wrapText":"1"}),69:(0,0,0,6,{"wrapText":"1"}),70:(0,0,0,7,{"wrapText":"1"}),
    71:(0,0,0,8,{"wrapText":"1"}),72:(0,0,0,9,{"wrapText":"1"}),73:(0,0,0,10,{"wrapText":"1"}),
    82:(201,0,0,5,None),83:(0,0,0,6,None),84:(201,0,0,8,None),85:(0,0,0,9,None),
    86:(200,0,0,9,None),87:(0,0,0,10,None),
    94:(0,3,2,2,None),95:(0,3,2,3,None),96:(0,3,2,4,None),
    104:(201,0,0,5,{"wrapText":"1"}),105:(200,0,0,6,{"wrapText":"1"}),
    106:(201,0,0,8,{"wrapText":"1"}),107:(200,0,0,9,{"wrapText":"1"}),
    112:(0,0,6,0,{"wrapText":"1"}),
    115:(0,7,7,0,{"horizontal":"center"}),118:(0,8,8,0,{"horizontal":"center","vertical":"center","wrapText":"1"}),
    129:(0,8,5,0,{"horizontal":"center","vertical":"center","wrapText":"1"}),
    132:(0,8,5,0,{"horizontal":"center","vertical":"center","wrapText":"0"}),
    134:(0,7,11,0,{"horizontal":"center"}),137:(0,8,12,0,{"horizontal":"center","vertical":"center","wrapText":"0"}),
    139:(0,8,13,0,{"horizontal":"center","vertical":"center","wrapText":"0"}),
}

def _fills_xml() -> str:
    items = []
    for idx, value in enumerate(_FILL_COLORS):
        if idx == 0:
            items.append('<fill><patternFill patternType="none"/></fill>')
        elif value == "gray125":
            items.append('<fill><patternFill patternType="gray125"/></fill>')
        else:
            items.append(f'<fill><patternFill patternType="solid"><fgColor rgb="{value}"/></patternFill></fill>')
    return f'<fills count="{len(items)}">' + "".join(items) + '</fills>'

def _xf_xml(index: int) -> str:
    numfmt, font, fill, border, alignment = _USED_XFS.get(index, (0,0,0,0,None))
    attrs = (
        f'numFmtId="{numfmt}" fontId="{font}" fillId="{fill}" borderId="{border}" xfId="0" '
        'applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1"'
    )
    if alignment:
        attrs += ' applyAlignment="1"'
        alignment_xml = '<alignment ' + " ".join(f'{key}="{escape(value)}"' for key,value in alignment.items()) + '/>'
        return f'<xf {attrs}>{alignment_xml}</xf>'
    return f'<xf {attrs}/>'

def canonical_styles_xml() -> bytes:
    xfs = "".join(_xf_xml(idx) for idx in range(140))
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{MAIN_NS}">'
        '<numFmts count="2"><numFmt numFmtId="200" formatCode="0.00"/>'
        '<numFmt numFmtId="201" formatCode="m/d/yyyy"/></numFmts>'
        f'<fonts count="{len(_FONTS)}">' + "".join(_FONTS) + '</fonts>'
        + _fills_xml()
        + '<borders count="20">' + '<border/>' * 20 + '</borders>'
        + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        + f'<cellXfs count="140">{xfs}</cellXfs>'
        + '<cellStyles count="1"><cellStyle name="Normal" xfId="0"/></cellStyles>'
        + '</styleSheet>'
    )
    return xml.encode("utf-8")
