"""Post-conversion cleanups that improve HWPX output quality.

These operate directly on the raw_zip XML (header.xml + section*.xml) so they
work both on freshly converted documents and on any loaded HwpxDocument.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET

from . import xml_io
from .models import HwpxDocument, ns

BLACK = "#000000"
DEFAULT_INSTRUCTION_MARKERS = ("※", "☞", "◈")


@dataclass(frozen=True)
class CleanupReport:
    instruction_runs_removed: int = 0
    instruction_paragraphs_removed: int = 0
    colors_normalized: int = 0
    dotted_borders_cleared: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "instruction_runs_removed": self.instruction_runs_removed,
            "instruction_paragraphs_removed": self.instruction_paragraphs_removed,
            "colors_normalized": self.colors_normalized,
            "dotted_borders_cleared": self.dotted_borders_cleared,
        }


def apply_cleanup(
    doc: HwpxDocument,
    *,
    strip_instructions: bool = False,
    normalize_colors: bool = False,
    remove_dotted_borders: bool = False,
    instruction_markers: tuple[str, ...] = DEFAULT_INSTRUCTION_MARKERS,
) -> CleanupReport:
    """Apply selected cleanups to doc in place (mutates doc.raw_zip).

    Re-parses sections afterwards so the in-memory model stays in sync.
    """
    if not doc.raw_zip:
        raise ValueError("Cleanup requires a document loaded from disk (raw_zip empty)")

    instruction_runs = 0
    empty_paras = 0
    colors = 0
    borders = 0

    if normalize_colors or remove_dotted_borders:
        header_path = "Contents/header.xml"
        if header_path in doc.raw_zip:
            header_root = xml_io.parse(doc.raw_zip[header_path])
            if normalize_colors:
                colors += _normalize_header_colors(header_root)
            if remove_dotted_borders:
                borders += _remove_dotted_borders(header_root)
            doc.raw_zip[header_path] = xml_io.serialize(header_root)

    if strip_instructions or normalize_colors:
        for name in list(doc.raw_zip):
            if not (name.startswith("Contents/section") and name.endswith(".xml")):
                continue
            root = xml_io.parse(doc.raw_zip[name])
            if strip_instructions:
                instruction_runs += _strip_instruction_runs(root, instruction_markers)
                empty_paras += _collapse_empty_body_paragraphs(root)
            if normalize_colors:
                colors += _normalize_inline_colors(root)
            doc.raw_zip[name] = xml_io.serialize(root)

    _reload_sections(doc)
    return CleanupReport(
        instruction_runs_removed=instruction_runs,
        instruction_paragraphs_removed=empty_paras,
        colors_normalized=colors,
        dotted_borders_cleared=borders,
    )


# ---------------------------------------------------------------------------
# Strip instruction text (blue ※ runs inside paragraphs)
# ---------------------------------------------------------------------------


def _strip_instruction_runs(root: ET.Element, markers: tuple[str, ...]) -> int:
    """Blank the text of any <hp:t> whose content starts with an instruction marker."""
    count = 0
    for t_el in root.iter(ns("hp", "t")):
        text = t_el.text or ""
        stripped = text.lstrip()
        if any(stripped.startswith(m) for m in markers):
            t_el.text = ""
            count += 1
    return count


def _collapse_empty_body_paragraphs(root: ET.Element) -> int:
    """Remove top-level <hp:p> elements that have runs but no remaining text.

    Skips:
      - section-property paragraphs (contain <hp:secPr>)
      - paragraphs inside table cells (structurally required)
      - paragraphs containing anchors/objects (ctrl, pic, tbl, eq, line, ...)
    """
    body = root if root.tag == ns("hs", "sec") else root.find(ns("hs", "sec"))
    if body is None:
        body = root

    table_para_ids: set[int] = set()
    for tbl in root.iter(ns("hp", "tbl")):
        for inner in tbl.iter(ns("hp", "p")):
            table_para_ids.add(id(inner))

    removed = 0
    for parent in root.iter():
        for p_el in list(parent.findall(ns("hp", "p"))):
            if id(p_el) in table_para_ids:
                continue
            if not _is_removable_empty(p_el):
                continue
            parent.remove(p_el)
            removed += 1
    return removed


_NON_TEXT_OBJECT_TAGS = (
    "ctrl", "tbl", "pic", "ole", "eq", "line", "rect", "ellipse",
    "arc", "polygon", "curve", "container", "textart", "footNote",
    "endNote", "compose", "pageNum",
)


def _is_removable_empty(p_el: ET.Element) -> bool:
    runs = p_el.findall(ns("hp", "run"))
    if not runs:
        return False
    for run in runs:
        if run.find(ns("hp", "secPr")) is not None:
            return False
        for tag in _NON_TEXT_OBJECT_TAGS:
            if run.find(ns("hp", tag)) is not None:
                return False
        for t in run.findall(ns("hp", "t")):
            if t.text:
                return False
    return True


# ---------------------------------------------------------------------------
# Normalize all text colors to black
# ---------------------------------------------------------------------------


_DECORATION_CHILD_TAGS = ("underline", "strikeout")


def _normalize_header_colors(header_root: ET.Element) -> int:
    """Force every <hh:charPr> (and its underline/strikeout) to use black."""
    count = 0
    for cp in header_root.iter(ns("hh", "charPr")):
        if cp.get("textColor") not in (None, BLACK):
            cp.set("textColor", BLACK)
            count += 1
        for tag in _DECORATION_CHILD_TAGS:
            child = cp.find(ns("hh", tag))
            if child is not None and child.get("color") not in (None, BLACK):
                child.set("color", BLACK)
                count += 1
    return count


def _normalize_inline_colors(root: ET.Element) -> int:
    """Catch stray textColor attributes anywhere in the section tree."""
    count = 0
    for el in root.iter():
        if el.get("textColor") not in (None, BLACK):
            el.set("textColor", BLACK)
            count += 1
    return count


# ---------------------------------------------------------------------------
# Remove dotted borders (type="DOT" -> "NONE")
# ---------------------------------------------------------------------------


_BORDER_TAGS = ("leftBorder", "rightBorder", "topBorder", "bottomBorder")


def _remove_dotted_borders(header_root: ET.Element) -> int:
    count = 0
    for fill in header_root.iter(ns("hh", "borderFill")):
        for tag in _BORDER_TAGS:
            border = fill.find(ns("hh", tag))
            if border is not None and border.get("type") == "DOT":
                border.set("type", "NONE")
                count += 1
    return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_sections(doc: HwpxDocument) -> None:
    """Rebuild doc.sections from the (possibly mutated) raw_zip."""
    from .reader import _parse_section  # avoid circular import at top

    doc.sections.clear()
    idx = 0
    while True:
        path = f"Contents/section{idx}.xml"
        if path not in doc.raw_zip:
            break
        doc.sections.append(_parse_section(idx, doc.raw_zip[path]))
        idx += 1
