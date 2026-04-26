"""MCP server for HWPX document manipulation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import cleanup, conversion, editor, styles, viewer
from .hwpx_core import create_hwpx
from .models import HwpxDocument
from .reader import read_hwpx
from .writer import save_hwpx

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "hancom-writer",
    instructions=(
        "HWPX(한글) 문서를 읽고 쓰는 MCP 서버. HWP->HWPX 변환, 문서 생성, "
        "텍스트 삽입/검색/치환, 표 삽입, 서식 정리(안내문 제거, 색상 통일, 점선 제거), "
        "파일 저장 기능을 제공합니다."
    ),
)

_documents: dict[str, HwpxDocument] = {}


def _get_doc(doc_id: str) -> HwpxDocument:
    if doc_id not in _documents:
        raise ValueError(
            f"Document '{doc_id}' is not open. Use open_document or create_document first."
        )
    return _documents[doc_id]


def _dump(payload: dict | list) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


@mcp.tool()
def convert_hwp_to_hwpx(
    hwp_path: str,
    hwpx_path: str | None = None,
    strip_instructions: bool = False,
    normalize_colors: bool = False,
    remove_dotted_borders: bool = False,
    patch_fills: bool = True,
) -> str:
    """HWP(바이너리) 파일을 HWPX로 변환하고, 선택적으로 후처리를 수행합니다.

    Args:
        hwp_path: .hwp 파일의 절대 경로
        hwpx_path: 출력 .hwpx 파일 경로 (미지정시 같은 위치에 .hwpx 확장자)
        strip_instructions: ※/☞/◈ 로 시작하는 안내 텍스트 런을 제거
        normalize_colors: 모든 글자 색을 #000000 으로 통일
        remove_dotted_borders: 점선(DOT) 테두리를 NONE 으로 변경
        patch_fills: 원본 HWP에서 읽은 borderFill 색상/그라디언트를 HWPX에
                     덧씌움 (hwp2hwpx가 fillBrush를 놓치는 케이스 보강)
    """
    result = conversion.convert_hwp_to_hwpx(
        hwp_path,
        hwpx_path,
        strip_instructions=strip_instructions,
        normalize_colors=normalize_colors,
        remove_dotted_borders=remove_dotted_borders,
        patch_fills=patch_fills,
    )
    return _dump(result.as_dict())


@mcp.tool()
def cleanup_document(
    doc_id: str,
    strip_instructions: bool = True,
    normalize_colors: bool = True,
    remove_dotted_borders: bool = True,
) -> str:
    """열려있는 문서에 서식 정리 규칙을 적용합니다 (메모리 내 업데이트).

    적용 후에는 save_document 로 저장해야 디스크에 반영됩니다.
    """
    doc = _get_doc(doc_id)
    report = cleanup.apply_cleanup(
        doc,
        strip_instructions=strip_instructions,
        normalize_colors=normalize_colors,
        remove_dotted_borders=remove_dotted_borders,
    )
    return _dump({"doc_id": doc_id, "status": "cleaned", **report.as_dict()})


# ---------------------------------------------------------------------------
# Document lifecycle
# ---------------------------------------------------------------------------


@mcp.tool()
def create_document(
    title: str = "Untitled",
    doc_id: str | None = None,
    template: str = "default",
) -> str:
    """새 HWPX 문서를 생성합니다.

    template:
        - "default" (기본값) — 한컴 표준 22개 스타일 카탈로그 탑재
          (바탕글, 본문, 개요1~10, 머리말, 각주, 미주, 메모,
          차례 제목, 차례1~3, 캡션, 쪽 번호).
          insert_text(style="개요 1") 등이 즉시 동작.
        - "empty" — 본문 1개 스타일만 가진 최소 문서.
    """
    if doc_id is None:
        doc_id = f"doc_{len(_documents)}"
    _documents[doc_id] = create_hwpx(title=title, template=template)
    return _dump(
        {"doc_id": doc_id, "title": title, "template": template, "status": "created"}
    )


@mcp.tool()
def open_document(file_path: str, doc_id: str | None = None) -> str:
    """기존 HWPX 파일을 열어 메모리에 로드합니다."""
    doc = read_hwpx(file_path)
    if doc_id is None:
        doc_id = Path(file_path).stem
    _documents[doc_id] = doc

    structure = doc.get_structure()
    structure["doc_id"] = doc_id
    structure["file_path"] = file_path
    return _dump(structure)


@mcp.tool()
def save_document(
    doc_id: str,
    file_path: str | None = None,
    auto_reload: bool = True,
) -> str:
    """문서를 HWPX 파일로 저장합니다. 한컴 뷰어가 열려있으면 자동 리로드합니다."""
    doc = _get_doc(doc_id)
    target = file_path or doc.path or f"{doc_id}.hwpx"

    saved_path = save_hwpx(doc, target)
    doc.path = saved_path

    reloaded = viewer.reload_viewer(saved_path) if auto_reload else False
    return _dump({"status": "saved", "file_path": saved_path, "viewer_reloaded": reloaded})


@mcp.tool()
def list_documents() -> str:
    """현재 열려있는 모든 문서를 나열합니다."""
    docs = [
        {
            "doc_id": doc_id,
            "title": doc.title,
            "path": doc.path,
            "sections": len(doc.sections),
            "total_paragraphs": sum(len(s.paragraphs) for s in doc.sections),
        }
        for doc_id, doc in _documents.items()
    ]
    return _dump(docs)


# ---------------------------------------------------------------------------
# Content inspection
# ---------------------------------------------------------------------------


@mcp.tool()
def get_text(doc_id: str, section_index: int | None = None) -> str:
    """문서의 텍스트를 추출합니다."""
    doc = _get_doc(doc_id)
    if section_index is None:
        return doc.get_all_text()
    if section_index >= len(doc.sections):
        raise IndexError(f"Section {section_index} does not exist")
    section = doc.sections[section_index]
    return "\n".join(p.text for p in section.paragraphs)


@mcp.tool()
def get_structure(doc_id: str) -> str:
    """문서의 구조를 반환합니다 (섹션, 단락, 표 목록)."""
    return _dump(_get_doc(doc_id).get_structure())


@mcp.tool()
def find_text(doc_id: str, query: str) -> str:
    """문서에서 텍스트를 검색합니다."""
    doc = _get_doc(doc_id)
    results: list[dict] = []

    for section in doc.sections:
        for para in section.paragraphs:
            if query not in para.text:
                continue
            start = 0
            while True:
                idx = para.text.find(query, start)
                if idx == -1:
                    break
                results.append(
                    {
                        "section": section.index,
                        "paragraph_id": para.id,
                        "offset": idx,
                        "context": para.text[max(0, idx - 20) : idx + len(query) + 20],
                    }
                )
                start = idx + 1

    return _dump({"query": query, "count": len(results), "results": results})


@mcp.tool()
def get_table_data(doc_id: str, section_index: int = 0, table_index: int = 0) -> str:
    """문서의 표 데이터를 추출합니다."""
    doc = _get_doc(doc_id)
    if section_index >= len(doc.sections):
        raise IndexError(f"Section {section_index} does not exist")
    section = doc.sections[section_index]
    if table_index >= len(section.tables):
        raise IndexError(f"Table {table_index} does not exist in section {section_index}")

    table = section.tables[table_index]
    data = [[cell.text for cell in row] for row in table.rows]
    return _dump(
        {
            "table_id": table.id,
            "rows": len(data),
            "cols": len(data[0]) if data else 0,
            "data": data,
        }
    )


# ---------------------------------------------------------------------------
# Content editing
# ---------------------------------------------------------------------------


@mcp.tool()
def insert_text(
    doc_id: str,
    text: str,
    section_index: int = 0,
    position: int = -1,
    style: str | None = None,
) -> str:
    """문서에 텍스트 단락을 삽입합니다. position=-1 이면 끝에 추가합니다.

    style: 스타일 이름/영문명/숫자 ID. 예) "개요 1", "개요1", "Outline 1", "머리말".
           list_styles 도구로 사용 가능한 스타일 확인 가능.
    """
    doc = _get_doc(doc_id)
    style_key: int | str | None = _coerce_style_key(style)
    editor.insert_text(doc, text, section_index, position, style=style_key)
    para = doc.sections[section_index].paragraphs[
        position if position >= 0 else -1
    ]
    return _dump(
        {
            "status": "inserted",
            "text": text[:100],
            "section": section_index,
            "paragraph_id": para.id,
            "style_id": para.style_id,
            "total_paragraphs": len(doc.sections[section_index].paragraphs),
        }
    )


@mcp.tool()
def list_styles(doc_id: str) -> str:
    """문서에 정의된 스타일 목록을 반환합니다 (개요 1, 머리말, 본문 등)."""
    doc = _get_doc(doc_id)
    return _dump([s.as_dict() for s in styles.list_styles(doc)])


@mcp.tool()
def define_style(
    doc_id: str,
    name: str,
    eng_name: str | None = None,
    base_style: str | None = None,
    font_size_pt: float | None = None,
    text_color: str | None = None,
    shade_color: str | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    alignment: str | None = None,
    line_spacing_percent: int | None = None,
    indent: int | None = None,
) -> str:
    """문서에 사용자 정의 스타일을 추가합니다.

    Args:
        name: 스타일 이름 (예: "강조 헤더")
        eng_name: 영문명 (미지정시 name 사용)
        base_style: 이 스타일이 상속할 기존 스타일(이름/ID). 미지정시 "바탕글"(id=0)
        font_size_pt: 글자 크기(포인트 단위). 예) 14
        text_color: 텍스트 색 "#RRGGBB"
        shade_color: 글자 배경색 "#RRGGBB" 또는 "none"
        bold / italic / underline: 개별 토글 (None 이면 base 유지)
        alignment: LEFT / CENTER / RIGHT / JUSTIFY / DISTRIBUTE
        line_spacing_percent: 줄 간격 %, 100=단일, 160=템플릿 기본
        indent: 들여쓰기 (HWPUNIT, 1HWPUNIT ≈ 0.0074mm)

    Returns:
        생성된 스타일 정보 (id, paraPr/charPr 참조 포함)
    """
    doc = _get_doc(doc_id)
    base = _coerce_style_key(base_style)
    style = styles.define_style(
        doc,
        name=name,
        eng_name=eng_name,
        base_style=base,
        font_size_pt=font_size_pt,
        text_color=text_color,
        shade_color=shade_color,
        bold=bold,
        italic=italic,
        underline=underline,
        alignment=alignment,
        line_spacing_percent=line_spacing_percent,
        indent=indent,
    )
    return _dump({"status": "defined", **style.as_dict()})


@mcp.tool()
def set_paragraph_style(
    doc_id: str,
    paragraph_id: int,
    style: str,
    section_index: int | None = None,
) -> str:
    """기존 단락에 스타일을 적용합니다.

    Args:
        paragraph_id: 대상 단락 id (open_document 구조에서 확인)
        style: 스타일 이름/영문명/숫자 ID. 예) "개요 2", "머리말"
        section_index: 특정 섹션으로 제한 (미지정시 전체 섹션 검색)
    """
    doc = _get_doc(doc_id)
    style_key = _coerce_style_key(style) or style
    para = editor.set_paragraph_style(
        doc, paragraph_id, style_key, section_index=section_index
    )
    return _dump(
        {
            "status": "styled",
            "paragraph_id": para.id,
            "style_id": para.style_id,
            "para_pr_id": para.para_pr_id,
            "char_pr_id": para.char_pr_id,
        }
    )


def _coerce_style_key(value: str | None) -> int | str | None:
    """Accept numeric strings as int IDs; otherwise pass through the name."""
    if value is None:
        return None
    stripped = value.strip()
    if stripped.isdigit():
        return int(stripped)
    return stripped


@mcp.tool()
def replace_text(doc_id: str, search: str, replace: str) -> str:
    """문서 전체에서 텍스트를 검색하여 치환합니다."""
    doc = _get_doc(doc_id)
    count = editor.replace_text(doc, search, replace)
    return _dump(
        {"status": "replaced", "search": search, "replace": replace, "count": count}
    )


@mcp.tool()
def insert_table(
    doc_id: str,
    headers: list[str],
    rows: list[list[str]],
    section_index: int = 0,
) -> str:
    """문서에 표를 삽입합니다."""
    doc = _get_doc(doc_id)
    all_rows = [headers] + rows
    editor.insert_table(doc, all_rows, section_index)
    return _dump(
        {
            "status": "table_inserted",
            "rows": len(all_rows),
            "cols": len(headers),
            "section": section_index,
        }
    )


# ---------------------------------------------------------------------------
# Content removal (B-04)
# ---------------------------------------------------------------------------


@mcp.tool()
def delete_paragraph(
    doc_id: str,
    paragraph_id: int,
    section_index: int | None = None,
) -> str:
    """단락 ID 로 단락을 삭제합니다. 미발견시 LookupError."""
    doc = _get_doc(doc_id)
    removed = editor.delete_paragraph(doc, paragraph_id, section_index=section_index)
    return _dump(
        {
            "status": "deleted",
            "paragraph_id": removed.id,
            "text_preview": removed.text[:60],
        }
    )


@mcp.tool()
def delete_table(
    doc_id: str,
    table_id: int,
    section_index: int | None = None,
) -> str:
    """표 ID 로 표를 삭제합니다. 미발견시 LookupError."""
    doc = _get_doc(doc_id)
    removed = editor.delete_table(doc, table_id, section_index=section_index)
    return _dump(
        {
            "status": "deleted",
            "table_id": removed.id,
            "rows": len(removed.rows),
            "cols": len(removed.rows[0]) if removed.rows else 0,
        }
    )


@mcp.tool()
def clear_section(
    doc_id: str,
    section_index: int = 0,
    keep_styles: bool = True,
) -> str:
    """섹션의 모든 단락·표를 삭제합니다. keep_styles 는 향후 헤더 초기화 옵션 자리표시자."""
    doc = _get_doc(doc_id)
    removed = editor.clear_section(
        doc, section_index=section_index, keep_styles=keep_styles
    )
    return _dump(
        {
            "status": "cleared",
            "section_index": section_index,
            "removed_count": removed,
        }
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
