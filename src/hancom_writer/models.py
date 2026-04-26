"""HWPX domain models and XML namespace helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from . import templates as T

# Register namespaces so ET preserves prefixes on write
for _prefix, _uri in T.NAMESPACES.items():
    ET.register_namespace(_prefix, _uri)


def ns(prefix: str, tag: str) -> str:
    """Return a Clark-notation tag, e.g. ns('hp', 't') -> '{...}t'."""
    return f"{{{T.NAMESPACES[prefix]}}}{tag}"


@dataclass
class InlineImage:
    """An inline image (treat-as-char anchor) attached to a paragraph (B-01).

    The bytes themselves live in ``HwpxDocument.raw_zip[href]`` so they round
    trip through writer pack/unpack without an extra storage layer.
    """

    bin_data_id: int  # 1-based; matches <hh:binData id="..."> in header.xml
    media_type: str  # "image/png" | "image/jpeg"
    href: str  # e.g. "BinData/image1.png"
    width_mm: float
    height_mm: float


@dataclass
class Paragraph:
    id: int
    text: str
    bold: bool = False
    char_pr_id: int = 0
    style_id: int = 0
    para_pr_id: int = 0
    image: InlineImage | None = None


@dataclass
class TableCell:
    text: str
    col: int = 0
    row: int = 0
    col_span: int = 1
    row_span: int = 1
    para_texts: list[str] = field(default_factory=list, repr=False)


@dataclass
class Table:
    id: int
    rows: list[list[TableCell]] = field(default_factory=list)


@dataclass
class Section:
    index: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)


@dataclass
class HwpxDocument:
    path: str | None = None
    title: str = "Untitled"
    sections: list[Section] = field(default_factory=list)
    raw_zip: dict[str, bytes] = field(default_factory=dict, repr=False)

    def get_all_text(self) -> str:
        lines: list[str] = []
        for section in self.sections:
            for para in section.paragraphs:
                lines.append(para.text)
            for table in section.tables:
                for row in table.rows:
                    for cell in row:
                        if cell.text:
                            lines.append(cell.text)
        return "\n".join(lines)

    def get_structure(self) -> dict:
        return {
            "title": self.title,
            "sections": [
                {
                    "index": s.index,
                    "paragraph_count": len(s.paragraphs),
                    "table_count": len(s.tables),
                    "paragraphs": [
                        {"id": p.id, "text": p.text[:100], "bold": p.bold}
                        for p in s.paragraphs
                    ],
                    "tables": [
                        {
                            "id": t.id,
                            "rows": len(t.rows),
                            "cols": len(t.rows[0]) if t.rows else 0,
                        }
                        for t in s.tables
                    ],
                }
                for s in self.sections
            ],
        }
