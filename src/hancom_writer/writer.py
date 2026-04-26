"""Serialize HwpxDocument back to .hwpx files."""

from __future__ import annotations

import copy
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

from . import templates as T
from . import xml_io
from .models import HwpxDocument, Section, ns

MIMETYPE_DATE = (2026, 1, 1, 0, 0, 0)


def save_hwpx(doc: HwpxDocument, file_path: str) -> str:
    """Save a document to .hwpx, preserving original formatting when possible."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # A doc loaded from disk has the full zip (mimetype etc.). A doc created
    # via create_hwpx may have only a pre-populated header.xml (template
    # marker) — that still needs the full template-based build.
    if "mimetype" in doc.raw_zip:
        payload = _build_patched_zip(doc)
    else:
        payload = _build_new_zip(doc)

    path.write_bytes(payload)
    return str(path.resolve())


# ---------------------------------------------------------------------------
# Patched save (existing doc -> keep original XML, only patch text)
# ---------------------------------------------------------------------------


def _build_patched_zip(doc: HwpxDocument) -> bytes:
    patched = dict(doc.raw_zip)

    for section in doc.sections:
        section_path = f"Contents/section{section.index}.xml"
        if section_path not in patched:
            continue
        root = xml_io.parse(patched[section_path])
        _patch_section(root, section)
        patched[section_path] = xml_io.serialize(root)

    _ensure_standard_boilerplate(patched, doc)
    return _pack_zip(patched)


def _ensure_standard_boilerplate(
    entries: dict[str, bytes], doc: HwpxDocument
) -> None:
    """Fill in entries that hwp2hwpx omits but Hancom Viewer expects (B-12).

    Hancom output ships ``Preview/PrvText.txt``, ``Scripts/headerScripts``,
    ``Scripts/sourceScripts`` and ``META-INF/container.rdf``; ``hwp2hwpx``
    skips them, which makes Hancom Viewer flag the round-tripped file as
    corrupted. Existing entries are preserved.
    """
    if "Preview/PrvText.txt" not in entries:
        entries["Preview/PrvText.txt"] = doc.get_all_text()[:500].encode("utf-8")
    if "Scripts/headerScripts" not in entries:
        entries["Scripts/headerScripts"] = T.HEADER_SCRIPTS
    if "Scripts/sourceScripts" not in entries:
        entries["Scripts/sourceScripts"] = T.SOURCE_SCRIPTS
    if "META-INF/container.rdf" not in entries:
        entries["META-INF/container.rdf"] = T.CONTAINER_RDF.encode("utf-8")


def _patch_section(root, section: Section) -> None:
    para_map = {str(p.id): p for p in section.paragraphs}
    table_id_set = {t.id for t in section.tables}
    cell_text_map = {
        (t.id, r_idx, c_idx): cell.para_texts
        for t in section.tables
        for r_idx, row in enumerate(t.rows)
        for c_idx, cell in enumerate(row)
    }

    # First: drop top-level paragraphs/tables that no longer exist in the
    # domain model (B-04). Section-properties paragraph (with <hp:secPr>) is
    # always retained.
    sec_pr_qname = ns("hp", "secPr")
    tbl_qname = ns("hp", "tbl")
    p_qname = ns("hp", "p")
    to_remove: list = []
    for el in list(root):
        if el.tag != p_qname:
            continue
        is_sec_props = any(e.tag == sec_pr_qname for e in el.iter(sec_pr_qname))
        if is_sec_props:
            continue
        nested_tbl = next(iter(el.iter(tbl_qname)), None)
        if nested_tbl is not None:
            tbl_id = int(nested_tbl.get("id", "0"))
            if tbl_id not in table_id_set:
                to_remove.append(el)
            continue
        if el.get("id", "0") not in para_map:
            to_remove.append(el)
    for el in to_remove:
        root.remove(el)

    # Then: patch text/style of retained paragraphs.
    table_para_ids: set[str] = set()
    for tbl_el in root.iter(ns("hp", "tbl")):
        for inner_p in tbl_el.iter(ns("hp", "p")):
            table_para_ids.add(inner_p.get("id", ""))

    for p_el in root.iter(ns("hp", "p")):
        pid = p_el.get("id", "0")
        if pid in table_para_ids or pid not in para_map:
            continue
        para = para_map[pid]
        _set_paragraph_text(p_el, para.text)
        _apply_paragraph_style(p_el, para)

    for tbl_el in root.iter(ns("hp", "tbl")):
        tbl_id = int(tbl_el.get("id", "0"))
        for r_idx, tr_el in enumerate(tbl_el.findall(ns("hp", "tr"))):
            for c_idx, tc_el in enumerate(tr_el.findall(ns("hp", "tc"))):
                _patch_cell(tc_el, (tbl_id, r_idx, c_idx), cell_text_map)

    _strip_linesegarray(root)


def _strip_linesegarray(root) -> None:
    """Drop every <hp:linesegarray> so Hancom Viewer recomputes layout (B-15).

    HWPX paragraphs cache their per-line layout (textpos / textheight / vertSize)
    inside <hp:linesegarray>. Once the underlying text length changes, that
    cache disagrees with the runs and Hancom Viewer flags the file as corrupted
    (verified by the G2 case: two hp:t edits in one paragraph, total length
    delta −71). Removing the cache forces Hancom Viewer to relayout from the
    runs, which is exactly what fixes the K2b verification case.
    """
    lineseg_qname = ns("hp", "linesegarray")
    for lsa in list(root.iter(lineseg_qname)):
        parent = lsa.getparent()
        if parent is not None:
            parent.remove(lsa)


def _set_paragraph_text(p_el: ET.Element, new_text: str) -> None:
    """Put new_text in the first <hp:t>, blank out the rest, preserving runs."""
    runs = p_el.findall(ns("hp", "run"))
    if not runs:
        return
    first = True
    for run in runs:
        t_el = run.find(ns("hp", "t"))
        if t_el is None:
            continue
        t_el.text = new_text if first else ""
        first = False


# ---------------------------------------------------------------------------
# Style application
# ---------------------------------------------------------------------------


def _apply_paragraph_style(p_el, para) -> None:
    """Write `para`'s style fields back to the XML paragraph verbatim.

    The editor keeps `style_id`, `para_pr_id`, and `char_pr_id` in sync when
    a style is applied via the public API, so the writer just mirrors those
    values. Callers who only change text see no attribute churn on unrelated
    paragraphs.
    """
    p_el.set("styleIDRef", str(para.style_id))
    p_el.set("paraPrIDRef", str(para.para_pr_id))
    if para.char_pr_id:
        for run in p_el.findall(ns("hp", "run")):
            run.set("charPrIDRef", str(para.char_pr_id))


def _patch_cell(
    tc_el: ET.Element,
    key: tuple[int, int, int],
    cell_text_map: dict[tuple[int, int, int], list[str]],
) -> None:
    new_para_texts = cell_text_map.get(key)
    if new_para_texts is None:
        return

    sub_list = tc_el.find(ns("hp", "subList"))
    if sub_list is None:
        return
    cell_paras = list(sub_list.findall(ns("hp", "p")))
    if not cell_paras:
        return

    template_p = cell_paras[0]
    for i, p_el in enumerate(cell_paras):
        text = new_para_texts[i] if i < len(new_para_texts) else ""
        _set_paragraph_text(p_el, text)

    # Clone template paragraph for overflow content. Strip any nested
    # structural objects (tables, pictures, ...) from the clone template so
    # each new paragraph carries only text runs — otherwise every overflow
    # clone would duplicate the nested object on save.
    if len(new_para_texts) > len(cell_paras):
        clone_template = _prepare_clone_template(template_p)
        for i in range(len(cell_paras), len(new_para_texts)):
            new_p = copy.deepcopy(clone_template)
            _set_paragraph_text(new_p, new_para_texts[i])
            sub_list.append(new_p)


_OBJECT_RUN_TAGS = (
    "tbl", "pic", "ole", "eq", "line", "rect", "ellipse", "arc",
    "polygon", "curve", "container", "textart", "compose",
)


def _prepare_clone_template(template_p):
    """Return a copy of template_p with any object-bearing runs removed."""
    clean = copy.deepcopy(template_p)
    for run in list(clean.findall(ns("hp", "run"))):
        if any(run.find(ns("hp", tag)) is not None for tag in _OBJECT_RUN_TAGS):
            clean.remove(run)
    return clean


# ---------------------------------------------------------------------------
# New save (freshly created doc -> build from templates)
# ---------------------------------------------------------------------------


def _build_new_zip(doc: HwpxDocument) -> bytes:
    entries: dict[str, bytes] = {}
    entries["mimetype"] = T.MIMETYPE.encode("utf-8")
    entries["version.xml"] = T.VERSION_XML.encode("utf-8")
    entries["settings.xml"] = T.SETTINGS_XML.encode("utf-8")
    entries["META-INF/container.xml"] = T.CONTAINER_XML.encode("utf-8")
    entries["META-INF/container.rdf"] = T.CONTAINER_RDF.encode("utf-8")
    entries["META-INF/manifest.xml"] = T.MANIFEST_XML.encode("utf-8")
    entries["Contents/content.hpf"] = T.content_hpf(
        title=doc.title, section_count=len(doc.sections)
    ).encode("utf-8")
    # Prefer the template-aware header that create_hwpx pre-populates.
    entries["Contents/header.xml"] = doc.raw_zip.get(
        "Contents/header.xml", T.HEADER_XML.encode("utf-8")
    )
    entries["Scripts/headerScripts"] = T.HEADER_SCRIPTS
    entries["Scripts/sourceScripts"] = T.SOURCE_SCRIPTS

    for section in doc.sections:
        entries[f"Contents/section{section.index}.xml"] = _render_section(section).encode("utf-8")

    entries["Preview/PrvText.txt"] = doc.get_all_text()[:500].encode("utf-8")
    return _pack_zip(entries)


def _render_section(section: Section) -> str:
    paras = [{"text": p.text, "bold": p.bold} for p in section.paragraphs]
    section_content = T.section_xml(paras)

    if not section.tables:
        return section_content

    table_parts: list[str] = []
    para_id_counter = len(section.paragraphs) + 100
    for table in section.tables:
        rows = [[cell.text for cell in row] for row in table.rows]
        table_parts.append(
            T.table_paragraph_xml(
                para_id=para_id_counter, table_id=table.id, rows=rows
            )
        )
        para_id_counter += 1 + sum(len(r) for r in table.rows)

    return section_content.replace("</hs:sec>", "".join(table_parts) + "</hs:sec>")


# ---------------------------------------------------------------------------
# Shared: pack into ZIP bytes with correct mimetype handling
# ---------------------------------------------------------------------------


def _pack_zip(entries: dict[str, bytes]) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype MUST be first and uncompressed per HWPX spec
        if "mimetype" in entries:
            zf.writestr(
                zipfile.ZipInfo("mimetype", date_time=MIMETYPE_DATE),
                entries["mimetype"],
                compress_type=zipfile.ZIP_STORED,
            )
        for name, data in entries.items():
            if name == "mimetype":
                continue
            zf.writestr(name, data)
    return buf.getvalue()
