# B-04: `delete_paragraph` / `delete_table` / `clear_section`

## 요구사항 재진술

복사된 템플릿 HWPX 의 기존 콘텐츠(단락·표)를 지울 수 없다. 그래서 새
사업계획서를 작성하면 항상 기존 콘텐츠 뒤에 append되어, 단독으로 쓸 수
없는 누더기 문서가 만들어진다.

## 수용 기준

- AC1. `delete_paragraph(doc, paragraph_id, section_index=None)` — 지정 단락
  제거. 미발견 시 `LookupError`. `section_index=None` 이면 모든 섹션 검색.
- AC2. `delete_table(doc, table_id, section_index=None)` — 지정 표 제거.
  미발견 시 `LookupError`.
- AC3. `clear_section(doc, section_index=0, keep_styles=True)` — 섹션의
  모든 단락·표 제거. `keep_styles=True` 면 `Contents/header.xml` 과 페이지
  설정 유지.
- AC4. 빈 섹션에서 `clear_section` 호출 시 no-op.
- AC5. `delete_paragraph` 후 다른 단락 ID 는 변경되지 않는다 (재번호 X).
- AC6. 회귀: 기존 테스트 모두 통과.
- AC7. MCP 서버 도구 `delete_paragraph` / `delete_table` / `clear_section`
  세 개를 노출.

## 인터페이스

```python
# src/hancom_writer/editor.py
def delete_paragraph(
    doc: HwpxDocument,
    paragraph_id: int,
    section_index: int | None = None,
) -> Paragraph: ...

def delete_table(
    doc: HwpxDocument,
    table_id: int,
    section_index: int | None = None,
) -> Table: ...

def clear_section(
    doc: HwpxDocument,
    section_index: int = 0,
    keep_styles: bool = True,
) -> int: ...  # returns count of removed (paragraphs + tables)
```

```python
# src/hancom_writer/server.py — 3 new MCP tools wrapping the editor functions
```

## 구현 전략

1. `editor.py` 에 세 함수 추가. 단순 리스트 필터링.
2. `clear_section` 의 `keep_styles=False` 는 향후 페이지 설정도 초기화하는
   여지를 남김 (지금은 콘텐츠만 비움).
3. `Contents/section{idx}.xml` 의 raw XML 패치는 다음 `save_document` 호출
   시 `_patch_section` 이 단락 ID 매핑 기반으로 자연스럽게 처리됨 — 단,
   현재 `_patch_section` 은 단락 텍스트만 패치하고 단락/표 자체를 제거하지
   않음. 따라서 추가 후처리: 매칭되지 않는 단락/표 element를 raw XML 에서
   제거하는 로직을 `_patch_section` 에 추가.

## 영향 범위

- `src/hancom_writer/editor.py` — 함수 3개 추가
- `src/hancom_writer/writer.py` — `_patch_section` 에서 도메인 모델에 없는
  단락/표 element 제거
- `src/hancom_writer/server.py` — MCP 도구 3개 등록
- `tests/test_delete_clear.py` — 신규

## 리스크

- `_patch_section` 의 elem 제거 시 표 내부 단락 ID 가 단락 ID 와 충돌 → 표
  내부 단락은 보존하도록 분기 필요.
- 기존 테스트가 단락/표 그대로 보존되는 경로를 검증한다면 회귀 가능 →
  실행 후 확인.
