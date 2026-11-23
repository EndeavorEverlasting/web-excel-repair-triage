"""Minimal synthetic fixtures. No corporate spreadsheets or real ticket data."""
from __future__ import annotations

import zipfile

from triage.web_excel_feature_preservation import compare_features


ROOT = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
DRAW = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
ART = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def _fixture(path, *, filters=True, freeze=True, validations=True, picture=True):
    workbook = f'<workbook xmlns="{ROOT}" xmlns:r="{REL}"><sheets><sheet name="Tickets" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="{REL}/worksheet"/></Relationships>'
    autofilter = '<autoFilter ref="A1:B8"/>' if filters else ''
    pane = '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews>' if freeze else ''
    dv = '<dataValidations count="1"><dataValidation type="list" sqref="A2:A100"><formula1>"Open,Done"</formula1></dataValidation></dataValidations>' if validations else ''
    draw = '<drawing r:id="rId2"/>' if picture else ''
    worksheet = f'<worksheet xmlns="{ROOT}" xmlns:r="{REL}">{pane}<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Status</t></is></c></row></sheetData>{autofilter}{dv}{draw}</worksheet>'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/_rels/workbook.xml.rels', rels)
        z.writestr('xl/worksheets/sheet1.xml', worksheet)
        if picture:
            z.writestr('xl/worksheets/_rels/sheet1.xml.rels', f'<Relationships xmlns="{PKG}"><Relationship Id="rId2" Type="{REL}/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            z.writestr('xl/drawings/drawing1.xml', f'<xdr:wsDr xmlns:xdr="{DRAW}" xmlns:a="{ART}" xmlns:r="{REL}"><xdr:oneCellAnchor><xdr:from><xdr:col>9</xdr:col><xdr:row>1</xdr:row></xdr:from><xdr:ext cx="500" cy="400"/><xdr:pic><xdr:blipFill><a:blip r:embed="rId3"/></xdr:blipFill></xdr:pic></xdr:oneCellAnchor></xdr:wsDr>')
            z.writestr('xl/drawings/_rels/drawing1.xml.rels', f'<Relationships xmlns="{PKG}"><Relationship Id="rId3" Type="{REL}/image" Target="../media/image1.png"/></Relationships>')
            z.writestr('xl/media/image1.png', b'fake-png-content-for-synthetic-test')


def test_preserves_all_user_features(tmp_path):
    a, b = tmp_path / 'baseline.xlsx', tmp_path / 'preserved.xlsx'
    _fixture(a)
    _fixture(b)
    assert compare_features(a, b)['pass'] is True


def test_catches_lost_filters_and_frozen_panes(tmp_path):
    a, b = tmp_path / 'baseline.xlsx', tmp_path / 'regressed.xlsx'
    _fixture(a)
    _fixture(b, filters=False, freeze=False)
    result = compare_features(a, b)
    assert result['pass'] is False
    assert {x['code'] for x in result['issues']} == {'filters_changed', 'panes_changed'}


def test_catches_missing_dropdowns_and_guidance_picture(tmp_path):
    a, b = tmp_path / 'baseline.xlsx', tmp_path / 'regressed.xlsx'
    _fixture(a)
    _fixture(b, validations=False, picture=False)
    codes = {x['code'] for x in compare_features(a, b)['issues']}
    assert codes == {'validations_changed', 'images_changed'}
