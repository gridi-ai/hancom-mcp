"""HWPX XML templates for generating valid HWPX documents.

Templates are based on actual Hancom Office output for maximum compatibility.
"""

MIMETYPE = "application/hwp+zip"

# Full namespace declarations matching real Hancom Office output
ALL_NS = (
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
    'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
    'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
    'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
    'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
    'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:opf="http://www.idpf.org/2007/opf/" '
    'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
    'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
    'xmlns:epub="http://www.idpf.org/2007/ops" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'
)

NAMESPACES = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "hv": "http://www.hancom.co.kr/hwpml/2011/version",
    "opf": "http://www.idpf.org/2007/opf/",
    "ocf": "urn:oasis:names:tc:opendocument:xmlns:container",
    "odf": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "pkg": "http://www.hancom.co.kr/hwpml/2016/meta/pkg#",
}

VERSION_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' \
    '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version"' \
    ' tagetApplication="WORDPROCESSOR"' \
    ' major="5" minor="1" micro="1" buildNumber="0" os="1"' \
    ' xmlVersion="1.5"' \
    ' application="Hancom Office Hangul"' \
    ' appVersion="12, 0, 0, 1 WIN32LEWindows_10"/>'

SETTINGS_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' \
    '<ha:HWPApplicationSetting' \
    ' xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app"' \
    ' xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">' \
    '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/>' \
    '</ha:HWPApplicationSetting>'

CONTAINER_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' \
    '<ocf:container' \
    ' xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container"' \
    ' xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf">' \
    '<ocf:rootfiles>' \
    '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>' \
    '<ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/>' \
    '<ocf:rootfile full-path="META-INF/container.rdf" media-type="application/rdf+xml"/>' \
    '</ocf:rootfiles>' \
    '</ocf:container>'

CONTAINER_RDF = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' \
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">' \
    '<rdf:Description rdf:about="">' \
    '<ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/header.xml"/>' \
    '</rdf:Description>' \
    '<rdf:Description rdf:about="Contents/header.xml">' \
    '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#HeaderFile"/>' \
    '</rdf:Description>' \
    '<rdf:Description rdf:about="">' \
    '<ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/section0.xml"/>' \
    '</rdf:Description>' \
    '<rdf:Description rdf:about="Contents/section0.xml">' \
    '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>' \
    '</rdf:Description>' \
    '<rdf:Description rdf:about="">' \
    '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#Document"/>' \
    '</rdf:Description>' \
    '</rdf:RDF>'

MANIFEST_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' \
    '<odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>'

# Script files (UTF-16LE encoded, matching Hancom Office output)
HEADER_SCRIPTS = 'var Documents = XHwpDocuments;\nvar Document = Documents.Active_XHwpDocument;\n'.encode('utf-16-le')
SOURCE_SCRIPTS = 'function OnDocument_New()\n{\n}\nfunction OnDocument_Open()\n{\n}\n'.encode('utf-16-le')


def content_hpf(title: str = "Untitled", section_count: int = 1) -> str:
    items = [
        '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>',
    ]
    spine_refs = [
        '<opf:itemref idref="header" linear="yes"/>',
    ]
    for i in range(section_count):
        items.append(
            f'<opf:item id="section{i}" href="Contents/section{i}.xml" media-type="application/xml"/>'
        )
        spine_refs.append(f'<opf:itemref idref="section{i}" linear="yes"/>')

    items.append('<opf:item id="headersc" href="Scripts/headerScripts" media-type="application/x-javascript ;charset=utf-16"/>')
    items.append('<opf:item id="sourcesc" href="Scripts/sourceScripts" media-type="application/x-javascript ;charset=utf-16"/>')
    items.append('<opf:item id="settings" href="settings.xml" media-type="application/xml"/>')

    spine_refs.append('<opf:itemref idref="headersc" linear="yes"/>')
    spine_refs.append('<opf:itemref idref="sourcesc" linear="yes"/>')

    title_escaped = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
        f'<opf:package {ALL_NS} version="" unique-identifier="" id="">'
        '<opf:metadata>'
        f'<opf:title>{title_escaped}</opf:title>'
        '<opf:language>ko</opf:language>'
        '<opf:meta name="creator" content="text"/>'
        '<opf:meta name="subject" content="text"/>'
        '<opf:meta name="description" content="text"/>'
        '</opf:metadata>'
        '<opf:manifest>'
        + ''.join(items) +
        '</opf:manifest>'
        '<opf:spine>'
        + ''.join(spine_refs) +
        '</opf:spine>'
        '</opf:package>'
    )


# --- Standard Hancom style catalogue (B-06) -------------------------------
# 22 styles that ship in stock Hancom Office HWPX files. Listed in id order
# so list_styles output matches the expected catalogue.
_STANDARD_STYLES: tuple[tuple[int, str, str, str], ...] = (
    (0, "바탕글", "Normal", "PARA"),
    (1, "본문", "Body", "PARA"),
    (2, "개요 1", "Outline 1", "PARA"),
    (3, "개요 2", "Outline 2", "PARA"),
    (4, "개요 3", "Outline 3", "PARA"),
    (5, "개요 4", "Outline 4", "PARA"),
    (6, "개요 5", "Outline 5", "PARA"),
    (7, "개요 6", "Outline 6", "PARA"),
    (8, "개요 7", "Outline 7", "PARA"),
    (9, "개요 8", "Outline 8", "PARA"),
    (10, "개요 9", "Outline 9", "PARA"),
    (11, "개요 10", "Outline 10", "PARA"),
    (12, "쪽 번호", "Page Number", "CHAR"),
    (13, "머리말", "Header", "PARA"),
    (14, "각주", "Footnote", "PARA"),
    (15, "미주", "Endnote", "PARA"),
    (16, "메모", "Memo", "PARA"),
    (17, "차례 제목", "TOC Heading", "PARA"),
    (18, "차례 1", "TOC 1", "PARA"),
    (19, "차례 2", "TOC 2", "PARA"),
    (20, "차례 3", "TOC 3", "PARA"),
    (21, "캡션", "Caption", "CHAR"),
)


def _build_styles_xml() -> str:
    """Render the <hh:styles> block for the default catalogue."""
    items = []
    for sid, name, eng, stype in _STANDARD_STYLES:
        items.append(
            f'<hh:style id="{sid}" type="{stype}" name="{name}" engName="{eng}"'
            f' paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="{sid}"'
            f' langID="1042" lockForm="0"/>'
        )
    return f'<hh:styles itemCnt="{len(items)}">' + "".join(items) + "</hh:styles>"


def _header_xml(styles_block: str) -> str:
    """Compose the header.xml around a given <hh:styles> block.

    The font/border/charPr/paraPr blocks are identical across templates.
    Only the styles section varies.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
        f'<hh:head {ALL_NS} version="1.5" secCnt="1">'
        '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
        '<hh:refList>'
        '<hh:fontfaces itemCnt="7">'
        '<hh:fontface lang="HANGUL" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="LATIN" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="HANJA" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="JAPANESE" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="OTHER" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="SYMBOL" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '<hh:fontface lang="USER" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
        '</hh:fontfaces>'
        '<hh:borderFills itemCnt="2">'
        '<hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
        '<hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>'
        '<hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>'
        '<hh:topBorder type="NONE" width="0.1 mm" color="#000000"/>'
        '<hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>'
        '<hc:fillBrush><hc:winBrush faceColor="none" hatchColor="#FFFFFF" alpha="0"/></hc:fillBrush>'
        '</hh:borderFill>'
        '<hh:borderFill id="2" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
        '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hc:fillBrush><hc:winBrush faceColor="none" hatchColor="#FFFFFF" alpha="0"/></hc:fillBrush>'
        '</hh:borderFill>'
        '</hh:borderFills>'
        '<hh:charProperties itemCnt="2">'
        '<hh:charPr id="0" height="1000" textColor="#000000" shadeColor="none" useFontSpace="0" useKerning="0">'
        '<hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:strikeout shape="NONE" color="#000000"/>'
        '<hh:outline type="NONE"/>'
        '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
        '</hh:charPr>'
        '<hh:charPr id="1" height="1000" textColor="#000000" shadeColor="none" useFontSpace="0" useKerning="0">'
        '<hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        '<hh:bold/>'
        '<hh:strikeout shape="NONE" color="#000000"/>'
        '<hh:outline type="NONE"/>'
        '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
        '</hh:charPr>'
        '</hh:charProperties>'
        '<hh:tabProperties itemCnt="1">'
        '<hh:tabPr id="0" autoTabLeft="1" autoTabRight="1"/>'
        '</hh:tabProperties>'
        '<hh:paraProperties itemCnt="1">'
        '<hh:paraPr id="0" tabPrIDRef="0">'
        '<hh:align horizontal="JUSTIFY" vertical="BASELINE"/>'
        '<hh:heading type="NONE" idRef="0" level="0"/>'
        '<hh:margin>'
        '<hc:intent value="0" unit="HWPUNIT"/>'
        '<hc:left value="0" unit="HWPUNIT"/>'
        '<hc:right value="0" unit="HWPUNIT"/>'
        '<hc:prev value="0" unit="HWPUNIT"/>'
        '<hc:next value="0" unit="HWPUNIT"/>'
        '</hh:margin>'
        '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>'
        '</hh:paraPr>'
        '</hh:paraProperties>'
        '<hh:numberings itemCnt="0"/>'
        '<hh:bullets itemCnt="0"/>'
        f'{styles_block}'
        '</hh:refList>'
        '<hh:compatibleDocument targetProgram="HWP201X">'
        '<hh:layoutCompatibility/>'
        '</hh:compatibleDocument>'
        '</hh:head>'
    )


# Default header carrying the full 22-style catalogue (B-06).
DEFAULT_HEADER_XML = _header_xml(_build_styles_xml())

# Empty header — minimal 1-style catalogue, kept for callers that explicitly
# want a bare document.
EMPTY_HEADER_XML = _header_xml(
    '<hh:styles itemCnt="1">'
    '<hh:style id="0" type="PARA" name="본문" engName="Body"'
    ' paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0"'
    ' langID="1042" lockForm="0"/>'
    '</hh:styles>'
)

# Backward-compat alias for any caller that still imports the old name.
HEADER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    f'<hh:head {ALL_NS} version="1.5" secCnt="1">'
    '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
    '<hh:refList>'
    # fontfaces - 7 language categories as required by Hancom
    '<hh:fontfaces itemCnt="7">'
    '<hh:fontface lang="HANGUL" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="LATIN" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="HANJA" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="JAPANESE" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="OTHER" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="SYMBOL" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '<hh:fontface lang="USER" fontCnt="1"><hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"/></hh:fontface>'
    '</hh:fontfaces>'
    # borderFills
    '<hh:borderFills itemCnt="2">'
    '<hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>'
    '<hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>'
    '<hh:topBorder type="NONE" width="0.1 mm" color="#000000"/>'
    '<hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>'
    '<hc:fillBrush><hc:winBrush faceColor="none" hatchColor="#FFFFFF" alpha="0"/></hc:fillBrush>'
    '</hh:borderFill>'
    '<hh:borderFill id="2" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hc:fillBrush><hc:winBrush faceColor="none" hatchColor="#FFFFFF" alpha="0"/></hc:fillBrush>'
    '</hh:borderFill>'
    '</hh:borderFills>'
    # charProperties
    '<hh:charProperties itemCnt="2">'
    '<hh:charPr id="0" height="1000" textColor="#000000" shadeColor="none" useFontSpace="0" useKerning="0">'
    '<hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:strikeout shape="NONE" color="#000000"/>'
    '<hh:outline type="NONE"/>'
    '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
    '</hh:charPr>'
    '<hh:charPr id="1" height="1000" textColor="#000000" shadeColor="none" useFontSpace="0" useKerning="0">'
    '<hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:bold/>'
    '<hh:strikeout shape="NONE" color="#000000"/>'
    '<hh:outline type="NONE"/>'
    '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
    '</hh:charPr>'
    '</hh:charProperties>'
    # tabProperties
    '<hh:tabProperties itemCnt="1">'
    '<hh:tabPr id="0" autoTabLeft="1" autoTabRight="1"/>'
    '</hh:tabProperties>'
    # paraProperties
    '<hh:paraProperties itemCnt="1">'
    '<hh:paraPr id="0" tabPrIDRef="0">'
    '<hh:align horizontal="JUSTIFY" vertical="BASELINE"/>'
    '<hh:heading type="NONE" idRef="0" level="0"/>'
    '<hh:margin>'
    '<hc:intent value="0" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
    '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>'
    '</hh:paraPr>'
    '</hh:paraProperties>'
    # numberings
    '<hh:numberings itemCnt="0"/>'
    '<hh:bullets itemCnt="0"/>'
    # styles
    '<hh:styles itemCnt="1">'
    '<hh:style id="0" type="PARA" name="본문" engName="Body"'
    ' paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0"'
    ' langID="1042" lockForm="0"/>'
    '</hh:styles>'
    '</hh:refList>'
    '<hh:compatibleDocument targetProgram="HWP201X">'
    '<hh:layoutCompatibility/>'
    '</hh:compatibleDocument>'
    '</hh:head>'
)


def section_xml(paragraphs: list[dict] | None = None) -> str:
    """Generate section XML.

    paragraphs: list of {"text": str, "bold": bool} dicts.
    If None, creates an empty section with just the section properties paragraph.
    """
    # Section properties paragraph (page setup - A4) - matching real Hancom output
    sec_pr = (
        '<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        '<hp:run charPrIDRef="0">'
        '<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="0" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">'
        '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>'
        '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
        '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
        '<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>'
        '<hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">'
        '<hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>'
        '</hp:pagePr>'
        '<hp:footNotePr>'
        '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
        '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>'
        '<hp:numbering type="CONTINUOUS" newNum="1"/>'
        '<hp:placement place="EACH_COLUMN" beneathText="0"/>'
        '</hp:footNotePr>'
        '<hp:endNotePr>'
        '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
        '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
        '<hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>'
        '<hp:numbering type="CONTINUOUS" newNum="1"/>'
        '<hp:placement place="END_OF_DOCUMENT" beneathText="0"/>'
        '</hp:endNotePr>'
        '<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0">'
        '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
        '</hp:pageBorderFill>'
        '</hp:secPr>'
        '<hp:t/>'
        '</hp:run>'
        '</hp:p>'
    )

    para_xml_parts = [sec_pr]
    if paragraphs:
        for i, p in enumerate(paragraphs, start=1):
            text = p.get("text", "")
            char_pr = "1" if p.get("bold") else "0"
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            para_xml_parts.append(
                f'<hp:p id="{i}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                f'<hp:run charPrIDRef="{char_pr}">'
                f'<hp:t>{text}</hp:t>'
                f'</hp:run>'
                f'</hp:p>'
            )

    body = ''.join(para_xml_parts)
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec {ALL_NS}>{body}</hs:sec>'


def table_paragraph_xml(
    para_id: int,
    table_id: int,
    rows: list[list[str]],
    col_widths: list[int] | None = None,
) -> str:
    """Generate a paragraph containing a table."""
    if not rows:
        return ""

    num_cols = len(rows[0])
    num_rows = len(rows)
    total_width = 42520  # A4 body width in HWPUNIT

    if col_widths is None:
        col_widths = [total_width // num_cols] * num_cols
        col_widths[-1] = total_width - sum(col_widths[:-1])

    row_height = 1800

    tr_parts = []
    cell_para_id = para_id + 1
    for r_idx, row in enumerate(rows):
        tc_parts = []
        for c_idx, cell_text in enumerate(row):
            cell_text_escaped = cell_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            tc_parts.append(
                f'<hp:tc header="0" hasMargin="1" protect="0" borderFillIDRef="2">'
                f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER">'
                f'<hp:p id="{cell_para_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                f'<hp:run charPrIDRef="0">'
                f'<hp:t>{cell_text_escaped}</hp:t>'
                f'</hp:run>'
                f'</hp:p>'
                f'</hp:subList>'
                f'<hp:cellAddr colAddr="{c_idx}" rowAddr="{r_idx}"/>'
                f'<hp:cellSpan colSpan="1" rowSpan="1"/>'
                f'<hp:cellSz width="{col_widths[c_idx]}" height="{row_height}"/>'
                f'<hp:cellMargin left="180" right="180" top="90" bottom="90"/>'
                f'</hp:tc>'
            )
            cell_para_id += 1
        tr_parts.append('<hp:tr>' + ''.join(tc_parts) + '</hp:tr>')

    table_height = row_height * num_rows

    return (
        f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0">'
        f'<hp:tbl id="{table_id}" numberingType="TABLE"'
        f' textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES"'
        f' rowCnt="{num_rows}" colCnt="{num_cols}" cellSpacing="0"'
        f' borderFillIDRef="2">'
        f'<hp:sz width="{total_width}" widthRelTo="ABSOLUTE"'
        f' height="{table_height}" heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1"'
        f' allowOverlap="0" vertRelTo="PARA" horzRelTo="COLUMN"'
        f' vertAlign="TOP" horzAlign="LEFT"'
        f' vertOffset="0" horzOffset="0"/>'
        + ''.join(tr_parts) +
        f'</hp:tbl>'
        f'</hp:run>'
        f'</hp:p>'
    )
