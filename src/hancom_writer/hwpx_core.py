"""Compatibility shim — re-exports from the refactored modules.

Prefer importing directly from `hancom_writer.models`, `.reader`, `.writer`,
`.editor`, `.cleanup`, `.conversion`, or `.viewer`.
"""

from __future__ import annotations

from . import templates
from .editor import insert_table, insert_text, replace_text
from .models import HwpxDocument, Paragraph, Section, Table, TableCell
from .reader import read_hwpx
from .writer import save_hwpx

_TEMPLATE_HEADERS: dict[str, str] = {
    "default": templates.DEFAULT_HEADER_XML,
    "empty": templates.EMPTY_HEADER_XML,
}


def create_hwpx(
    title: str = "Untitled",
    paragraphs: list[dict] | None = None,
    template: str = "default",
) -> HwpxDocument:
    """Create a blank HwpxDocument with a single section.

    Args:
        title: document title.
        paragraphs: optional seed paragraphs as `{"text": str, "bold": bool}`.
        template: ``"default"`` (22 standard Hancom styles) or ``"empty"``
            (single ``본문`` style only). Raises ``ValueError`` for unknown values.
    """
    if template not in _TEMPLATE_HEADERS:
        raise ValueError(
            f"Unknown template {template!r}. Choose from: "
            f"{sorted(_TEMPLATE_HEADERS)}"
        )

    doc = HwpxDocument(title=title)
    section = Section(index=0)
    if paragraphs:
        for i, p in enumerate(paragraphs, start=1):
            section.paragraphs.append(
                Paragraph(id=i, text=p.get("text", ""), bold=p.get("bold", False))
            )
    doc.sections.append(section)

    # Pre-populate header.xml so style queries work before save.
    doc.raw_zip["Contents/header.xml"] = _TEMPLATE_HEADERS[template].encode("utf-8")
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
