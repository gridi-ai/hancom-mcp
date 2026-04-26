"""B-12: patched-save fills in missing Hancom-standard ZIP entries."""

from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import templates as T
from hancom_writer import writer
from hancom_writer.models import HwpxDocument, Section


REQUIRED_ENTRIES = (
    "Preview/PrvText.txt",
    "Scripts/headerScripts",
    "Scripts/sourceScripts",
    "META-INF/container.rdf",
)


def _minimal_patched_doc() -> HwpxDocument:
    """A loaded-style doc whose raw_zip lacks the boilerplate entries."""
    doc = HwpxDocument(title="t")
    doc.sections.append(Section(index=0))
    # Minimal entries that mark this as a "loaded" doc going through
    # _build_patched_zip (mimetype gates the patched branch).
    doc.raw_zip = {
        "mimetype": T.MIMETYPE.encode("utf-8"),
        "META-INF/container.xml": T.CONTAINER_XML.encode("utf-8"),
        "Contents/content.hpf": T.content_hpf(title="t").encode("utf-8"),
        "Contents/header.xml": T.DEFAULT_HEADER_XML.encode("utf-8"),
        "Contents/section0.xml": T.section_xml().encode("utf-8"),
    }
    return doc


@pytest.mark.unit
def test_patched_save_adds_missing_boilerplate() -> None:
    doc = _minimal_patched_doc()
    for name in REQUIRED_ENTRIES:
        assert name not in doc.raw_zip

    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
    for name in REQUIRED_ENTRIES:
        assert name in names, f"missing required entry: {name}"


@pytest.mark.unit
def test_patched_save_preserves_existing_boilerplate() -> None:
    doc = _minimal_patched_doc()
    custom_prv = b"custom preview"
    doc.raw_zip["Preview/PrvText.txt"] = custom_prv

    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        assert z.read("Preview/PrvText.txt") == custom_prv


@pytest.mark.unit
def test_prv_text_derived_from_doc_content() -> None:
    doc = _minimal_patched_doc()
    # Seed the section with some text so PrvText reflects the doc.
    from hancom_writer.models import Paragraph
    doc.sections[0].paragraphs.append(Paragraph(id=1, text="안녕하세요 도화농장"))

    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        prv = z.read("Preview/PrvText.txt").decode("utf-8")
    assert "도화농장" in prv


@pytest.mark.unit
def test_scripts_are_utf16_le_encoded_like_hancom() -> None:
    doc = _minimal_patched_doc()
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        header_js = z.read("Scripts/headerScripts")
        source_js = z.read("Scripts/sourceScripts")
    assert header_js == T.HEADER_SCRIPTS
    assert source_js == T.SOURCE_SCRIPTS


@pytest.mark.unit
def test_container_rdf_matches_template() -> None:
    doc = _minimal_patched_doc()
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out = f.name
    writer.save_hwpx(doc, out)

    with zipfile.ZipFile(out) as z:
        rdf = z.read("META-INF/container.rdf").decode("utf-8")
    assert "rdf:RDF" in rdf
    assert "Contents/header.xml" in rdf
