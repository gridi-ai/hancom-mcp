"""Mutating operations on HwpxDocument (insert, replace)."""

from __future__ import annotations

from pathlib import Path

from . import styles
from .models import HwpxDocument, InlineImage, Paragraph, Table, TableCell

# Image extensions we know how to declare in HWPX manifest/header (B-01 MVP).
_IMAGE_MEDIA_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def insert_text(
    doc: HwpxDocument,
    text: str,
    section_index: int = 0,
    position: int = -1,
    style: int | str | styles.Style | None = None,
) -> HwpxDocument:
    """Insert a new paragraph. position == -1 appends to the end.

    `style` accepts a Style object, a numeric id, a Korean name (e.g. "개요 1"),
    or an English name (e.g. "Outline 1"). Leading/trailing whitespace and case
    are ignored.
    """
    section = _require_section(doc, section_index)
    next_id = max((p.id for p in section.paragraphs), default=0) + 1
    para = Paragraph(id=next_id, text=text)
    if style is not None:
        _apply_style(para, styles.resolve_style(doc, style))
    if position == -1:
        section.paragraphs.append(para)
    else:
        section.paragraphs.insert(position, para)
    return doc


def set_paragraph_style(
    doc: HwpxDocument,
    paragraph_id: int,
    style: int | str | styles.Style,
    section_index: int | None = None,
) -> Paragraph:
    """Apply a style to an existing paragraph, identified by id."""
    resolved = styles.resolve_style(doc, style)
    for idx, section in enumerate(doc.sections):
        if section_index is not None and idx != section_index:
            continue
        for para in section.paragraphs:
            if para.id == paragraph_id:
                _apply_style(para, resolved)
                return para
    raise LookupError(f"Paragraph id={paragraph_id} not found")


def _apply_style(para: Paragraph, style: styles.Style) -> None:
    para.style_id = style.id
    para.para_pr_id = style.para_pr_id
    para.char_pr_id = style.char_pr_id


def replace_text(doc: HwpxDocument, search: str, replace: str) -> int:
    """Replace all occurrences across paragraphs and table cells. Returns count."""
    count = 0
    for section in doc.sections:
        for para in section.paragraphs:
            if search in para.text:
                count += para.text.count(search)
                para.text = para.text.replace(search, replace)
        for table in section.tables:
            for row in table.rows:
                for cell in row:
                    count += _replace_in_cell(cell, search, replace)
    return count


def _replace_in_cell(cell: TableCell, search: str, replace: str) -> int:
    count = 0
    if cell.para_texts:
        for i, pt in enumerate(cell.para_texts):
            if search in pt:
                count += pt.count(search)
                cell.para_texts[i] = pt.replace(search, replace)
        cell.text = "\n".join(t for t in cell.para_texts if t)
    elif search in cell.text:
        count += cell.text.count(search)
        cell.text = cell.text.replace(search, replace)
    return count


def insert_image(
    doc: HwpxDocument,
    image_path: str,
    width_mm: float,
    height_mm: float,
    section_index: int = 0,
) -> Paragraph:
    """Append a new paragraph carrying an inline image (B-01 MVP).

    Supports PNG and JPEG; the anchor mode is treat-as-char (image flows
    inline with text). Bytes are read once and stashed on the document under
    ``BinData/imageN.<ext>``; the writer emits the corresponding manifest,
    header binDataList, and ``<hp:pic>`` markup at save time.

    MVP scope: only fresh documents (``create_document``). Inserting into a
    doc that was loaded from disk and already carries pre-existing
    ``BinData/`` entries raises ``RuntimeError`` because our id allocator
    does not yet read those entries — patched-save image insertion is
    tracked separately.
    """
    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    suffix = src.suffix.lower()
    media = _IMAGE_MEDIA_TYPES.get(suffix)
    if media is None:
        raise ValueError(
            f"Unsupported image extension {suffix!r}; "
            f"expected one of {sorted(_IMAGE_MEDIA_TYPES)}"
        )

    section = _require_section(doc, section_index)
    next_bin_id = (
        max(
            (
                p.image.bin_data_id
                for s in doc.sections
                for p in s.paragraphs
                if p.image is not None
            ),
            default=0,
        )
        + 1
    )
    href = f"BinData/image{next_bin_id}{suffix}"
    if href in doc.raw_zip:
        # Pre-existing BinData/* from a loaded HWPX would be silently
        # overwritten — refuse rather than corrupt the original asset.
        raise RuntimeError(
            f"BinData entry {href!r} already exists in doc.raw_zip; "
            "insert_image on documents loaded from disk is not yet supported."
        )
    doc.raw_zip[href] = src.read_bytes()

    image = InlineImage(
        bin_data_id=next_bin_id,
        media_type=media,
        href=href,
        width_mm=float(width_mm),
        height_mm=float(height_mm),
    )
    next_para_id = max((p.id for p in section.paragraphs), default=0) + 1
    para = Paragraph(id=next_para_id, text="", image=image)
    section.paragraphs.append(para)
    return para


def insert_table(
    doc: HwpxDocument, rows: list[list[str]], section_index: int = 0
) -> HwpxDocument:
    section = _require_section(doc, section_index)
    next_id = max((t.id for t in section.tables), default=5000) + 1
    table = Table(id=next_id)
    for r_idx, row in enumerate(rows):
        table.rows.append(
            [
                TableCell(
                    text=cell, col=c_idx, row=r_idx, para_texts=[cell] if cell else []
                )
                for c_idx, cell in enumerate(row)
            ]
        )
    section.tables.append(table)
    return doc


def delete_paragraph(
    doc: HwpxDocument,
    paragraph_id: int,
    section_index: int | None = None,
) -> Paragraph:
    """Remove a paragraph by id. Raises LookupError if absent."""
    for idx, section in enumerate(doc.sections):
        if section_index is not None and idx != section_index:
            continue
        for i, para in enumerate(section.paragraphs):
            if para.id == paragraph_id:
                return section.paragraphs.pop(i)
    raise LookupError(f"Paragraph id={paragraph_id} not found")


def delete_table(
    doc: HwpxDocument,
    table_id: int,
    section_index: int | None = None,
) -> Table:
    """Remove a table by id. Raises LookupError if absent."""
    for idx, section in enumerate(doc.sections):
        if section_index is not None and idx != section_index:
            continue
        for i, table in enumerate(section.tables):
            if table.id == table_id:
                return section.tables.pop(i)
    raise LookupError(f"Table id={table_id} not found")


def clear_section(
    doc: HwpxDocument,
    section_index: int = 0,
    keep_styles: bool = True,
) -> int:
    """Remove all paragraphs and tables in a section.

    Returns the count of removed items. ``keep_styles`` is a placeholder for a
    future option that would also reset header.xml; currently styles are
    always preserved (the ``Contents/header.xml`` payload in raw_zip is not
    touched here).
    """
    section = _require_section(doc, section_index)
    removed = len(section.paragraphs) + len(section.tables)
    section.paragraphs.clear()
    section.tables.clear()
    _ = keep_styles  # reserved for future expansion
    return removed


def _require_section(doc: HwpxDocument, index: int):
    if index >= len(doc.sections):
        raise IndexError(f"Section {index} does not exist")
    return doc.sections[index]
