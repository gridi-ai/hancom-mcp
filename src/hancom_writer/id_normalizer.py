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

    Returns the number of paragraphs whose ``id`` attribute was actually
    rewritten. Returns 0 — and leaves the zip bytes untouched (no timestamp
    churn, no checksum invalidation) — when every section already has the
    canonical numbering.
    """
    path = Path(hwpx_path)
    with zipfile.ZipFile(path, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    changed = 0
    rewrote_any = False
    for name in list(entries):
        if not _is_section_xml(name):
            continue
        new_bytes, section_changed = _renumber_section(entries[name])
        if section_changed > 0:
            entries[name] = new_bytes
            changed += section_changed
            rewrote_any = True

    if rewrote_any:
        path.write_bytes(_pack_zip(entries))
    return changed


def _is_section_xml(name: str) -> bool:
    return name.startswith("Contents/section") and name.endswith(".xml")


def _renumber_section(xml_bytes: bytes) -> tuple[bytes, int]:
    root = xml_io.parse(xml_bytes)
    p_qname = ns("hp", "p")
    sec_pr_qname = ns("hp", "secPr")
    next_id = 1
    changed = 0
    for p_el in root.iter(p_qname):
        # <hp:secPr> appears as a direct child of its paragraph in OWPML, but
        # use iter() to match _patch_section's invariant exactly so a future
        # nested secPr doesn't silently misclassify the paragraph.
        is_sec_pr_p = next(iter(p_el.iter(sec_pr_qname)), None) is not None
        new_id = "0" if is_sec_pr_p else str(next_id)
        if not is_sec_pr_p:
            next_id += 1
        if p_el.get("id") != new_id:
            p_el.set("id", new_id)
            changed += 1
    if changed == 0:
        return xml_bytes, 0
    return xml_io.serialize(root), changed
