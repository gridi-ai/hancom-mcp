"""Parse HWPX files into in-memory documents."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import HwpxDocument, Paragraph, Section, Table, TableCell, ns


def read_hwpx(file_path: str) -> HwpxDocument:
    """Read an HWPX file from disk and parse its content."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".hwpx":
        raise ValueError(f"Not an HWPX file: {file_path}")

    raw_zip: dict[str, bytes] = {}
    with zipfile.ZipFile(file_path, "r") as zf:
        for name in zf.namelist():
            raw_zip[name] = zf.read(name)

    doc = HwpxDocument(path=file_path, raw_zip=raw_zip)
    doc.title = _read_title(raw_zip)

    section_idx = 0
    while True:
        section_path = f"Contents/section{section_idx}.xml"
        if section_path not in raw_zip:
            break
        doc.sections.append(_parse_section(section_idx, raw_zip[section_path]))
        section_idx += 1

    return doc


def _read_title(raw_zip: dict[str, bytes]) -> str:
    hpf = raw_zip.get("Contents/content.hpf")
    if not hpf:
        return "Untitled"
    root = ET.fromstring(hpf)
    title_el = root.find(f".//{ns('opf', 'title')}")
    if title_el is not None and title_el.text:
        return title_el.text
    return "Untitled"


def _parse_section(index: int, xml_bytes: bytes) -> Section:
    section = Section(index=index)
    root = ET.fromstring(xml_bytes)

    table_para_ids = _collect_table_paragraph_ids(root)

    for p_el in root.iter(ns("hp", "p")):
        para = _parse_paragraph(p_el, table_para_ids)
        if para is not None:
            section.paragraphs.append(para)

    for tbl_el in root.iter(ns("hp", "tbl")):
        section.tables.append(_parse_table(tbl_el))

    return section


def _collect_table_paragraph_ids(root: ET.Element) -> set[str]:
    """Collect IDs of paragraphs inside tables so they're skipped at top level."""
    ids: set[str] = set()
    for tbl_el in root.iter(ns("hp", "tbl")):
        for inner_p in tbl_el.iter(ns("hp", "p")):
            ids.add(inner_p.get("id", ""))
    return ids


def _parse_paragraph(p_el: ET.Element, table_para_ids: set[str]) -> Paragraph | None:
    pid = p_el.get("id", "0")
    if pid in table_para_ids:
        return None

    texts: list[str] = []
    bold = False
    for run_el in p_el.findall(ns("hp", "run")):
        if run_el.get("charPrIDRef", "0") == "1":
            bold = True
        for t_el in run_el.findall(ns("hp", "t")):
            if t_el.text:
                texts.append(t_el.text)

    sec_pr = p_el.find(f".//{ns('hp', 'secPr')}")
    if sec_pr is not None and not any(texts):
        return None

    text = "".join(texts)
    if not text:
        return None
    return Paragraph(
        id=int(pid),
        text=text,
        bold=bold,
        style_id=int(p_el.get("styleIDRef", "0") or "0"),
        para_pr_id=int(p_el.get("paraPrIDRef", "0") or "0"),
    )


def _parse_table(tbl_el: ET.Element) -> Table:
    table = Table(id=int(tbl_el.get("id", "0")))
    for tr_el in tbl_el.findall(ns("hp", "tr")):
        row: list[TableCell] = []
        for tc_el in tr_el.findall(ns("hp", "tc")):
            row.append(_parse_cell(tc_el))
        table.rows.append(row)
    return table


def _parse_cell(tc_el: ET.Element) -> TableCell:
    para_texts: list[str] = []
    sub_list = tc_el.find(ns("hp", "subList"))
    if sub_list is not None:
        for p_el in sub_list.findall(ns("hp", "p")):
            # Direct <hp:t> descendants of this paragraph's runs, but not inside
            # a nested <hp:tbl>
            chunks: list[str] = []
            for run in p_el.findall(ns("hp", "run")):
                if run.find(ns("hp", "tbl")) is not None:
                    continue
                for t in run.findall(ns("hp", "t")):
                    if t.text:
                        chunks.append(t.text)
            para_texts.append("".join(chunks))

    addr = tc_el.find(ns("hp", "cellAddr"))
    span = tc_el.find(ns("hp", "cellSpan"))
    combined = "\n".join(t for t in para_texts if t)

    return TableCell(
        text=combined,
        col=int(addr.get("colAddr", "0")) if addr is not None else 0,
        row=int(addr.get("rowAddr", "0")) if addr is not None else 0,
        col_span=int(span.get("colSpan", "1")) if span is not None else 1,
        row_span=int(span.get("rowSpan", "1")) if span is not None else 1,
        para_texts=para_texts,
    )
