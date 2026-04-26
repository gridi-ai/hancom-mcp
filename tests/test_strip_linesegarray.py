"""B-15: patched-save strips <hp:linesegarray> so Hancom recomputes layout."""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import templates as T
from hancom_writer import writer
from hancom_writer.models import HwpxDocument, Paragraph, Section


HP_NS = T.NAMESPACES["hp"]
LINESEG_TAG = f"{{{HP_NS}}}linesegarray"


SECTION_XML_WITH_LINESEG = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
    ' xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
    '<hp:p id="1" paraPrIDRef="0" styleIDRef="0">'
    '<hp:run charPrIDRef="0"><hp:t>원문 텍스트</hp:t></hp:run>'
    '<hp:linesegarray>'
    '<hp:lineseg textpos="0" vertpos="0" vertSize="1000" textheight="1000"'
    ' baseline="850" spacing="600" horzpos="0" horzSize="42000"'
    ' flags="393216"/>'
    '</hp:linesegarray>'
    '</hp:p>'
    '<hp:p id="2" paraPrIDRef="0" styleIDRef="0">'
    '<hp:run charPrIDRef="0"><hp:t>두번째 단락</hp:t></hp:run>'
    '<hp:linesegarray>'
    '<hp:lineseg textpos="0" vertpos="1200" vertSize="1000" textheight="1000"'
    ' baseline="850" spacing="600" horzpos="0" horzSize="42000"'
    ' flags="393216"/>'
    '</hp:linesegarray>'
    '</hp:p>'
    '</hs:sec>'
)


def _patched_doc_with_lineseg() -> HwpxDocument:
    doc = HwpxDocument(title="t")
    section = Section(index=0)
    section.paragraphs.append(Paragraph(id=1, text="바뀐 텍스트"))
    section.paragraphs.append(Paragraph(id=2, text="두번째 단락"))
    doc.sections.append(section)
    doc.raw_zip = {
        "mimetype": T.MIMETYPE.encode("utf-8"),
        "META-INF/container.xml": T.CONTAINER_XML.encode("utf-8"),
        "Contents/content.hpf": T.content_hpf(title="t").encode("utf-8"),
        "Contents/header.xml": T.DEFAULT_HEADER_XML.encode("utf-8"),
        "Contents/section0.xml": SECTION_XML_WITH_LINESEG.encode("utf-8"),
    }
    return doc


@pytest.mark.unit
def test_patched_save_strips_linesegarray_from_all_paragraphs() -> None:
    doc = _patched_doc_with_lineseg()
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        section = z.read("Contents/section0.xml")
    assert b"linesegarray" not in section, (
        "Hancom-corruption-trigger: <hp:linesegarray> must be removed so "
        "Hancom Viewer recomputes layout instead of trusting stale cache."
    )


@pytest.mark.unit
def test_patched_save_preserves_text_runs_when_stripping_linesegarray() -> None:
    doc = _patched_doc_with_lineseg()
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        section = z.read("Contents/section0.xml").decode("utf-8")
    # The new paragraph text must survive even though the layout cache is gone.
    assert "바뀐 텍스트" in section
    assert "두번째 단락" in section
    # Runs themselves must remain — only the layout cache is removed.
    assert "<hp:run" in section
    assert "<hp:t>" in section


@pytest.mark.unit
def test_new_save_does_not_emit_linesegarray() -> None:
    """Freshly built docs (B-06 path) must also omit lineseg layout cache."""
    doc = HwpxDocument(title="t")
    section = Section(index=0)
    section.paragraphs.append(Paragraph(id=1, text="hello"))
    doc.sections.append(section)

    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        section_bytes = z.read("Contents/section0.xml")
    assert b"linesegarray" not in section_bytes
