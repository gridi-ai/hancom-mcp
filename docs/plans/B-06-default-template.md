# B-06: `create_document(template=...)` — 표준 스타일 탑재

## 요구사항 재진술

`create_document` 호출 직후 `list_styles` 가 빈 배열을 반환한다. 그래서
`insert_text(style="개요 1")` 같은 한컴 표준 스타일 호출이 즉시 실패한다.
새 문서가 한컴 표준 스타일 카탈로그(22개)를 기본 탑재하도록 한다.

## 수용 기준

- AC1. `create_hwpx()` 호출 직후 `list_styles(doc)` 가 22개 표준 스타일을 반환한다.
- AC2. 표준 스타일에는 `바탕글, 본문, 개요 1..개요 10, 머리말, 각주, 미주, 메모,
  차례 제목, 차례 1..3, 캡션, 쪽 번호` 가 모두 포함된다.
- AC3. `create_hwpx(template="empty")` 는 기존과 동일하게 최소 1개 스타일만 가진다.
- AC4. `create_hwpx(template="default")` 가 기본값과 동일하다.
- AC5. `insert_text(style="개요 1")` 가 새 문서에서 성공한다.
- AC6. 저장 후 한컴 뷰어가 정상적으로 열 수 있는 HWPX 파일이 생성된다 (smoke test).
- AC7. 기존 `test_hwpx.py` 회귀 없음.

## 인터페이스 설계

```python
# src/hancom_writer/hwpx_core.py
def create_hwpx(
    title: str = "Untitled",
    paragraphs: list[dict] | None = None,
    template: str = "default",   # NEW: "default" | "empty"
) -> HwpxDocument: ...
```

```python
# src/hancom_writer/server.py — MCP tool
@mcp.tool()
def create_document(
    title: str = "Untitled",
    doc_id: str | None = None,
    template: str = "default",   # NEW
) -> str: ...
```

## 구현 전략

1. `templates.py` 에 `DEFAULT_HEADER_XML` 신설 — 22개 표준 스타일과 매칭되는
   `paraProperties`, `charProperties` 를 포함한다. 기존 `HEADER_XML` 은
   `EMPTY_HEADER_XML` 로 보존(이름 변경)하고 1-style 미니멀 모드용으로 둔다.
2. `create_hwpx` 가 `template` 에 따라 헤더 바이트를 `doc.raw_zip` 에 미리 주입.
3. 서버 도구 `create_document` 에 `template` 파라미터 추가.
4. 회귀 방지: 기존 `test_hwpx.py` 는 `template="empty"` 로 호출하도록 명시적 분기.

## 영향 범위

- `src/hancom_writer/templates.py` — 헤더 XML 추가
- `src/hancom_writer/hwpx_core.py` — `create_hwpx` 시그니처 변경
- `src/hancom_writer/server.py` — `create_document` 도구 시그니처 변경
- `tests/test_default_template.py` — 신규 (RED→GREEN)

## 리스크

- HEADER_XML 의 `paraPr/charPr` 인덱스 충돌 시 한컴 뷰어 에러. 실제 HWPX
  샘플(`gridi 최종`)에서 추출한 정합성 있는 트리를 사용해 회피.
- 향후 `define_style` 이 동일 이름 추가 시도 시 conflict — `define_style`
  쪽에서 이미 `_normalize` 로 중복 검사하므로 안전.

## 검증 절차

```bash
pytest tests/test_default_template.py -v
pytest tests/ -v               # 회귀 테스트
```
