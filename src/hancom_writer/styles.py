"""HWPX paragraph/character style catalogue.

Styles live in `Contents/header.xml` under `<hh:styles>`. Each `<hh:style>`
references a paragraph property (`paraPrIDRef`) and a character property
(`charPrIDRef`) that together define how paragraphs using the style render.

Typical Hancom template ships styles like `바탕글`, `본문`, `개요 1`..`개요 10`,
`머리말`, `각주`, `차례 제목`, `차례 1`..`차례 3`, `쪽 번호`, `캡션`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from . import xml_io
from .models import HwpxDocument, ns

HEADER_PATH = "Contents/header.xml"
VALID_ALIGN = {"LEFT", "CENTER", "RIGHT", "JUSTIFY", "DISTRIBUTE", "DIVISION"}


@dataclass(frozen=True)
class Style:
    id: int
    name: str
    eng_name: str
    type: str  # "PARA" | "CHAR"
    para_pr_id: int
    char_pr_id: int

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "eng_name": self.eng_name,
            "type": self.type,
            "para_pr_id": self.para_pr_id,
            "char_pr_id": self.char_pr_id,
        }


def list_styles(doc: HwpxDocument) -> list[Style]:
    """Return all styles defined in the document header."""
    header_bytes = doc.raw_zip.get("Contents/header.xml")
    if not header_bytes:
        return []
    root = xml_io.parse(header_bytes)
    return [
        Style(
            id=int(el.get("id", "0")),
            name=el.get("name", "") or "",
            eng_name=el.get("engName", "") or "",
            type=el.get("type", "PARA") or "PARA",
            para_pr_id=int(el.get("paraPrIDRef", "0") or "0"),
            char_pr_id=int(el.get("charPrIDRef", "0") or "0"),
        )
        for el in root.iter(ns("hh", "style"))
    ]


def find_style(doc: HwpxDocument, key: int | str) -> Style | None:
    """Resolve a style by numeric id, Korean name, or English name.

    Name matching is lenient: whitespace-insensitive and case-insensitive,
    so "개요1" matches "개요 1" and "outline1" matches "Outline 1".
    """
    styles = list_styles(doc)
    if isinstance(key, int):
        for s in styles:
            if s.id == key:
                return s
        return None

    needle = _normalize(key)
    for s in styles:
        if _normalize(s.name) == needle or _normalize(s.eng_name) == needle:
            return s
    return None


def resolve_style(doc: HwpxDocument, key: int | str | Style) -> Style:
    """Resolve and raise if the key doesn't match any style."""
    if isinstance(key, Style):
        return key
    style = find_style(doc, key)
    if style is None:
        available = ", ".join(s.name for s in list_styles(doc) if s.name)
        raise LookupError(
            f"Style {key!r} not found. Available: {available}"
        )
    return style


def _normalize(s: str) -> str:
    return "".join(s.split()).lower()


# ---------------------------------------------------------------------------
# Define custom style
# ---------------------------------------------------------------------------


def define_style(
    doc: HwpxDocument,
    *,
    name: str,
    eng_name: str | None = None,
    base_style: int | str | None = None,
    font_size_pt: float | None = None,
    text_color: str | None = None,
    shade_color: str | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    alignment: str | None = None,
    line_spacing_percent: int | None = None,
    indent: int | None = None,
) -> Style:
    """Register a new paragraph style in the document header.

    Any option left as None inherits from `base_style` (defaults to 바탕글/id 0).
    Font size is in points (14pt → height=1400 in HWPX units), colors are
    "#RRGGBB", alignment is one of LEFT/CENTER/RIGHT/JUSTIFY/DISTRIBUTE, line
    spacing is a percentage (100 = single spacing), indent is in HWPUNIT.
    """
    if not doc.raw_zip or HEADER_PATH not in doc.raw_zip:
        raise ValueError("define_style requires a document with Contents/header.xml")
    if alignment is not None and alignment.upper() not in VALID_ALIGN:
        raise ValueError(f"alignment must be one of {sorted(VALID_ALIGN)}")

    if find_style(doc, name) is not None:
        raise ValueError(f"Style {name!r} already exists")

    header_root = xml_io.parse(doc.raw_zip[HEADER_PATH])
    ref_list = header_root.find(ns("hh", "refList"))
    if ref_list is None:
        raise ValueError("header.xml is missing <hh:refList>")

    base = resolve_style(doc, base_style) if base_style is not None else find_style(doc, 0)
    if base is None:
        raise LookupError("no base style (id 0) available to clone from")

    char_pr_el, new_char_pr_id = _clone_and_register(
        ref_list, "charProperties", "charPr", base.char_pr_id
    )
    para_pr_el, new_para_pr_id = _clone_and_register(
        ref_list, "paraProperties", "paraPr", base.para_pr_id
    )

    _patch_char_pr(
        char_pr_el,
        font_size_pt=font_size_pt,
        text_color=text_color,
        shade_color=shade_color,
        bold=bold,
        italic=italic,
        underline=underline,
    )
    _patch_para_pr(
        para_pr_el,
        alignment=alignment,
        line_spacing_percent=line_spacing_percent,
        indent=indent,
    )

    new_style_id = _next_style_id(ref_list)
    style_el = _append_style_element(
        ref_list,
        sid=new_style_id,
        name=name,
        eng_name=eng_name or name,
        para_pr_id=new_para_pr_id,
        char_pr_id=new_char_pr_id,
    )

    doc.raw_zip[HEADER_PATH] = xml_io.serialize(header_root)
    return Style(
        id=new_style_id,
        name=name,
        eng_name=style_el.get("engName") or "",
        type="PARA",
        para_pr_id=new_para_pr_id,
        char_pr_id=new_char_pr_id,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _clone_and_register(ref_list, container_tag: str, item_tag: str, source_id: int):
    """Deep-copy an existing <hh:charPr|paraPr id=source_id/>, assign next id,
    append to container, and bump the container's itemCnt attribute."""
    container = ref_list.find(ns("hh", container_tag))
    if container is None:
        raise ValueError(f"<hh:{container_tag}> missing from header")

    items = container.findall(ns("hh", item_tag))
    template = next((el for el in items if int(el.get("id", "-1")) == source_id), None)
    if template is None:
        template = items[0] if items else None
    if template is None:
        raise LookupError(f"no template {item_tag} to clone from")

    new_id = max((int(el.get("id", "0")) for el in items), default=-1) + 1
    new_el = copy.deepcopy(template)
    new_el.set("id", str(new_id))
    container.append(new_el)
    container.set("itemCnt", str(len(items) + 1))
    return new_el, new_id


def _patch_char_pr(
    char_pr,
    *,
    font_size_pt: float | None,
    text_color: str | None,
    shade_color: str | None,
    bold: bool | None,
    italic: bool | None,
    underline: bool | None,
) -> None:
    if font_size_pt is not None:
        char_pr.set("height", str(int(round(font_size_pt * 100))))
    if text_color is not None:
        char_pr.set("textColor", text_color)
    if shade_color is not None:
        char_pr.set("shadeColor", shade_color)
    if bold is not None:
        _toggle_flag_child(char_pr, "bold", bold)
    if italic is not None:
        _toggle_flag_child(char_pr, "italic", italic)
    if underline is not None:
        ul = char_pr.find(ns("hh", "underline"))
        if ul is None:
            ul = _hh_sub(char_pr, "underline")
        ul.set("type", "BOTTOM" if underline else "NONE")
        ul.set("shape", ul.get("shape") or "SOLID")
        ul.set("color", ul.get("color") or "#000000")


def _patch_para_pr(
    para_pr,
    *,
    alignment: str | None,
    line_spacing_percent: int | None,
    indent: int | None,
) -> None:
    if alignment is not None:
        align = para_pr.find(ns("hh", "align"))
        if align is None:
            align = _hh_sub(para_pr, "align")
            align.set("vertical", "BASELINE")
        align.set("horizontal", alignment.upper())

    if line_spacing_percent is not None:
        ls = para_pr.find(ns("hh", "lineSpacing"))
        if ls is None:
            ls = _hh_sub(para_pr, "lineSpacing")
        ls.set("type", "PERCENT")
        ls.set("value", str(line_spacing_percent))
        ls.set("unit", "HWPUNIT")

    if indent is not None:
        # <hh:margin> can appear directly or inside <hp:switch>/<hp:case>
        # (HWPUnitChar variants). Patch every occurrence so both branches stay
        # in sync.
        for margin in para_pr.iter(ns("hh", "margin")):
            intent = margin.find(ns("hc", "intent"))
            if intent is not None:
                intent.set("value", str(indent))


def _toggle_flag_child(parent, tag: str, enabled: bool) -> None:
    existing = parent.find(ns("hh", tag))
    if enabled and existing is None:
        _hh_sub(parent, tag)
    elif not enabled and existing is not None:
        parent.remove(existing)


def _hh_sub(parent, tag: str):
    from lxml import etree as LET

    return LET.SubElement(parent, ns("hh", tag))


def _next_style_id(ref_list) -> int:
    styles_container = ref_list.find(ns("hh", "styles"))
    if styles_container is None:
        raise ValueError("<hh:styles> missing from header")
    existing = styles_container.findall(ns("hh", "style"))
    return max((int(s.get("id", "0")) for s in existing), default=-1) + 1


def _append_style_element(
    ref_list,
    *,
    sid: int,
    name: str,
    eng_name: str,
    para_pr_id: int,
    char_pr_id: int,
):
    from lxml import etree as LET

    styles_container = ref_list.find(ns("hh", "styles"))
    el = LET.SubElement(styles_container, ns("hh", "style"))
    el.set("id", str(sid))
    el.set("type", "PARA")
    el.set("name", name)
    el.set("engName", eng_name)
    el.set("paraPrIDRef", str(para_pr_id))
    el.set("charPrIDRef", str(char_pr_id))
    el.set("nextStyleIDRef", str(sid))
    el.set("langID", "1042")
    el.set("lockForm", "0")
    styles_container.set(
        "itemCnt", str(len(styles_container.findall(ns("hh", "style"))))
    )
    return el
