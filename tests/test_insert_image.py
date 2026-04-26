"""B-01: insert_image MVP — domain model, editor API, and writer emission."""

from __future__ import annotations

import struct
import sys
import zipfile
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import editor, writer
from hancom_writer.models import HwpxDocument, Section
from hancom_writer.templates import DEFAULT_HEADER_XML


# ---------------------------------------------------------------------------
# Helpers — manufacture tiny on-disk PNG/JPEG fixtures so tests don't depend
# on shipped sample assets.
# ---------------------------------------------------------------------------


def _png_bytes() -> bytes:
    """A minimal valid 1x1 PNG (8 bytes signature + IHDR + IDAT + IEND)."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(
        ">I", zlib.crc32(ihdr)
    )
    raw = b"\x00\x00"  # filter byte + 1 grayscale pixel
    idat_data = zlib.compress(raw)
    idat = b"IDAT" + idat_data
    idat_chunk = struct.pack(">I", len(idat_data)) + idat + struct.pack(
        ">I", zlib.crc32(idat)
    )
    iend = b"IEND"
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend))
    return sig + ihdr_chunk + idat_chunk + iend_chunk


def _write_png(tmp_path: Path, name: str = "logo.png") -> Path:
    p = tmp_path / name
    p.write_bytes(_png_bytes())
    return p


def _fresh_doc() -> HwpxDocument:
    """A doc that goes through _build_new_zip (no mimetype in raw_zip)."""
    doc = HwpxDocument(title="t")
    doc.sections.append(Section(index=0))
    # Pre-populated header marker so _build_new_zip uses our default header
    # (matches the create_document(template="default") shape from B-06).
    doc.raw_zip = {"Contents/header.xml": DEFAULT_HEADER_XML.encode("utf-8")}
    return doc


# ---------------------------------------------------------------------------
# Editor API
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_insert_image_creates_paragraph_with_image(tmp_path: Path) -> None:
    doc = _fresh_doc()
    img_path = _write_png(tmp_path)

    para = editor.insert_image(doc, str(img_path), width_mm=40.0, height_mm=20.0)

    assert para.image is not None
    assert para.image.media_type == "image/png"
    assert para.image.width_mm == 40.0
    assert para.image.height_mm == 20.0
    assert para.image.bin_data_id == 1
    assert para.image.href.startswith("BinData/image1.")
    # Paragraph attached to the section.
    assert doc.sections[0].paragraphs[-1] is para
    # Image bytes are stashed on the doc so save_hwpx can write them.
    assert doc.raw_zip[para.image.href] == img_path.read_bytes()


@pytest.mark.unit
def test_insert_image_rejects_missing_file(tmp_path: Path) -> None:
    doc = _fresh_doc()
    with pytest.raises(FileNotFoundError):
        editor.insert_image(
            doc, str(tmp_path / "nope.png"), width_mm=10, height_mm=10
        )


@pytest.mark.unit
def test_insert_image_rejects_unsupported_extension(tmp_path: Path) -> None:
    doc = _fresh_doc()
    bogus = tmp_path / "bad.gif"
    bogus.write_bytes(b"GIF89a")
    with pytest.raises(ValueError):
        editor.insert_image(doc, str(bogus), width_mm=10, height_mm=10)


@pytest.mark.unit
def test_insert_image_assigns_unique_bin_data_ids(tmp_path: Path) -> None:
    doc = _fresh_doc()
    a = _write_png(tmp_path, "a.png")
    b = _write_png(tmp_path, "b.png")
    p1 = editor.insert_image(doc, str(a), width_mm=10, height_mm=10)
    p2 = editor.insert_image(doc, str(b), width_mm=10, height_mm=10)
    assert p1.image and p2.image
    assert p1.image.bin_data_id == 1
    assert p2.image.bin_data_id == 2
    assert p1.image.href != p2.image.href


# ---------------------------------------------------------------------------
# Writer integration — save and re-inspect the .hwpx zip
# ---------------------------------------------------------------------------


def _save(tmp_path: Path, doc: HwpxDocument, name: str = "out.hwpx") -> Path:
    out = tmp_path / name
    writer.save_hwpx(doc, str(out))
    return out


@pytest.mark.unit
def test_save_writes_bindata_entry_to_zip(tmp_path: Path) -> None:
    doc = _fresh_doc()
    img_path = _write_png(tmp_path)
    para = editor.insert_image(doc, str(img_path), width_mm=40, height_mm=20)
    out = _save(tmp_path, doc)

    assert para.image is not None
    with zipfile.ZipFile(out) as z:
        assert para.image.href in z.namelist()
        assert z.read(para.image.href) == img_path.read_bytes()


@pytest.mark.unit
def test_save_registers_image_in_manifest(tmp_path: Path) -> None:
    doc = _fresh_doc()
    img_path = _write_png(tmp_path)
    editor.insert_image(doc, str(img_path), width_mm=40, height_mm=20)
    out = _save(tmp_path, doc)

    with zipfile.ZipFile(out) as z:
        manifest = z.read("META-INF/manifest.xml").decode("utf-8")
    assert 'full-path="BinData/image1.png"' in manifest
    assert 'media-type="image/png"' in manifest


@pytest.mark.unit
def test_save_registers_image_in_header_bin_data_list(tmp_path: Path) -> None:
    doc = _fresh_doc()
    img_path = _write_png(tmp_path)
    editor.insert_image(doc, str(img_path), width_mm=40, height_mm=20)
    out = _save(tmp_path, doc)

    with zipfile.ZipFile(out) as z:
        header = z.read("Contents/header.xml").decode("utf-8")
    assert "<hh:binDataList" in header
    assert 'href="BinData/image1.png"' in header


@pytest.mark.unit
def test_save_emits_pic_element_in_section_xml(tmp_path: Path) -> None:
    doc = _fresh_doc()
    img_path = _write_png(tmp_path)
    editor.insert_image(doc, str(img_path), width_mm=40, height_mm=20)
    out = _save(tmp_path, doc)

    with zipfile.ZipFile(out) as z:
        section = z.read("Contents/section0.xml").decode("utf-8")
    # The image paragraph must carry a <hp:pic> element referencing binData id 1.
    assert "<hp:pic" in section
    assert 'binDataIDRef="1"' in section
