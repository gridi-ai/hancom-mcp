"""Normalize paragraph IDs in HWPX section XML after hwp2hwpx conversion (B-13).

``hwp2hwpx`` emits HWPX with duplicate paragraph IDs (e.g. ``id="0"`` repeated
across the section) and out-of-range values such as ``id="2147483648"`` (2³¹).
HWPX OWPML requires unique paragraph IDs per section, so Hancom Viewer flags
those files as corrupted.

This module rewrites every ``<hp:p id="...">`` in every
``Contents/section*.xml`` so IDs are unique within the section. The
section-properties paragraph (the one carrying ``<hp:secPr>``) keeps
``id="0"`` per Hancom convention (B-13a).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from . import xml_io
from .models import ns
from .writer import _pack_zip


def normalize_paragraph_ids(hwpx_path: str) -> int:
    """Renumber every ``<hp:p>`` in every section XML inside the .hwpx zip.

    Returns the total number of paragraphs visited (including the secPr
    paragraph that is reset to id=0). Returns 0 — and leaves the file
    untouched — when the zip contains no section XML.
    """
    path = Path(hwpx_path)
    with zipfile.ZipFile(path, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    total = 0
    rewrote_any = False
    for name in list(entries):
        if not _is_section_xml(name):
            continue
        new_bytes, count = _renumber_section(entries[name])
        if count > 0:
            entries[name] = new_bytes
            total += count
            rewrote_any = True

    if rewrote_any:
        path.write_bytes(_pack_zip(entries))
    return total


def _is_section_xml(name: str) -> bool:
    return name.startswith("Contents/section") and name.endswith(".xml")


def _renumber_section(xml_bytes: bytes) -> tuple[bytes, int]:
    root = xml_io.parse(xml_bytes)
    p_qname = ns("hp", "p")
    sec_pr_qname = ns("hp", "secPr")
    next_id = 1
    count = 0
    for p_el in root.iter(p_qname):
        if p_el.find(sec_pr_qname) is not None:
            # Section-properties paragraph keeps id=0 (B-13a). Hancom's own
            # boilerplate uses id=0 here and rejects renumbering of this slot.
            p_el.set("id", "0")
        else:
            p_el.set("id", str(next_id))
            next_id += 1
        count += 1
    if count == 0:
        return xml_bytes, 0
    return xml_io.serialize(root), count
