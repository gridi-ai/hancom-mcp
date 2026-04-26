"""Mutating operations on HwpxDocument (insert, replace)."""

from __future__ import annotations

from . import styles
from .models import HwpxDocument, Paragraph, Table, TableCell


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


def _require_section(doc: HwpxDocument, index: int):
    if index >= len(doc.sections):
        raise IndexError(f"Section {index} does not exist")
    return doc.sections[index]
