"""Compatibility shim — re-exports from the refactored modules.

Prefer importing directly from `hancom_writer.models`, `.reader`, `.writer`,
`.editor`, `.cleanup`, `.conversion`, or `.viewer`.
"""

from __future__ import annotations

from .editor import insert_table, insert_text, replace_text
from .models import HwpxDocument, Paragraph, Section, Table, TableCell
from .reader import read_hwpx
from .writer import save_hwpx


def create_hwpx(
    title: str = "Untitled",
    paragraphs: list[dict] | None = None,
) -> HwpxDocument:
    """Create a blank HwpxDocument with a single section."""
    doc = HwpxDocument(title=title)
    section = Section(index=0)
    if paragraphs:
        for i, p in enumerate(paragraphs, start=1):
            section.paragraphs.append(
                Paragraph(id=i, text=p.get("text", ""), bold=p.get("bold", False))
            )
    doc.sections.append(section)
    return doc


__all__ = [
    "HwpxDocument",
    "Paragraph",
    "Section",
    "Table",
    "TableCell",
    "create_hwpx",
    "insert_table",
    "insert_text",
    "read_hwpx",
    "replace_text",
    "save_hwpx",
]
