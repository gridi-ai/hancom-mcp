# Backlog

`rhwp` (https://github.com/edwardkim/rhwp) 와의 기능 비교 분석을 기준으로 도출한 우선순위 백로그입니다. 각 항목은 별도 브랜치 + PR 로 처리됩니다 ([CONTRIBUTING.md](../CONTRIBUTING.md) 참고).

## 범례
- 🔴 CRITICAL — 사업계획서/보고서 워크플로우에서 자주 막힘
- 🟠 HIGH — AI 자동화 레버리지가 큼
- 🟡 MEDIUM — 문서 품질·검증
- 🟢 LOW — 고급/시각화

## v0.2.x — 결손 도구 보완

### B-01 🔴 `insert_image` — 이미지 삽입 도구
- **문제**: 사업계획서·보고서에 로고·도식 삽입 불가.
- **수용 기준**:
  - PNG/JPEG 파일 경로, width/height(mm), anchor(treat-as-char/top-and-bottom) 인자 수용
  - HWPX `Contents/section0.xml` 에 `<hp:pic>` 또는 `<hp:ole>` 추가
  - BinData 경로 자동 등록(`META-INF/manifest.xml`, `Contents/header.xml`)
  - 통합 테스트: 삽입 후 한컴 뷰어에서 정상 표시
- **참고**: rhwp `Image with effects (grayscale/B&W)`

### B-02 🔴 `set_run_style` — 문자 단위 서식 (CharShape)
- **문제**: 단락 내 일부 어구만 굵게/색상/크기 변경 불가. `set_paragraph_style` 은 단락 전체에만 작용.
- **수용 기준**:
  - `paragraph_id`, `start_offset`, `end_offset`, `char_shape={bold,italic,underline,color,size,font_name}` 인자
  - HWPX `<hp:run>` 분할 후 `<hp:charPr>` 적용
  - 멀티 run 단락의 offset 정확성 테스트
- **참고**: rhwp hwpctl `CharShape` Action

### B-03 🔴 표 후편집 도구 묶음
- **문제**: 표 생성 후 셀 병합/행 추가/열 삭제 불가.
- **수용 기준**:
  - `merge_cells(table_id, r1, c1, r2, c2)`
  - `add_table_row(table_id, after_row=-1, cells=[...])`
  - `add_table_column(table_id, after_col=-1, default="")`
  - `delete_table_row(table_id, row)`, `delete_table_column(table_id, col)`
  - `set_cell_style(table_id, row, col, {bg_color, border, valign, ...})`
- **참고**: rhwp Table editing, Cell merging

### B-04 🔴 `delete_*` / `clear_section` — 콘텐츠 제거 도구
- **문제**: 템플릿 HWPX 의 기존 콘텐츠를 못 지워서 새 문서 작성 시 항상 append.
- **수용 기준**:
  - `delete_paragraph(paragraph_id)`
  - `delete_table(table_id)`
  - `clear_section(section_index, keep_styles=True)` — 콘텐츠만 비우고 스타일 카탈로그/페이지 설정은 보존
  - 빈 doc 에서도 호출 가능(no-op)
- **참고**: 사용자 직접 요청

### B-05 🟠 페이지 나누기 + 머리말/꼬리말
- **문제**: 다페이지 문서를 만들 수 없음.
- **수용 기준**:
  - `insert_page_break()` — `<hp:t>` 에 `<hp:ctrl>` PageBreak 삽입
  - `set_header(text, scope=both|odd|even, style=...)`
  - `set_footer(text, scope=both|odd|even, style=...)`
  - 한컴 뷰어에서 페이지가 실제로 분리됨을 확인
- **참고**: rhwp `Header/footer (odd/even page separation)`

### B-06 🔴 `create_document(template=...)` — 표준 스타일 탑재
- **문제**: 빈 문서에 한글 표준 스타일(개요1~10, 본문, 머리말, 캡션 등)이 없어 `insert_text(style="개요 1")` 가 즉시 실패.
- **수용 기준**:
  - 내장 기본 스타일 카탈로그(JSON/XML) 작성
  - `create_document(template="default"|"empty")` 옵션 추가
  - `default` 템플릿이 한컴 표준 25개 스타일 포함
- **참고**: 이전 세션 검증 결과

## v0.3.x — hwpctl 호환 레이어

### B-07 🟠 Field API
- **문제**: `{고객명}` 같은 필드 자리표시자 + 데이터 바인딩이 없음.
- **수용 기준**:
  - `define_field(name, paragraph_id, offset)`
  - `list_fields()`
  - `set_field_value(name, value)`
  - 템플릿 HWPX 에서 정의된 필드 자동 인식
- **참고**: rhwp `Field API: GetFieldList, PutFieldText, GetFieldText`

### B-08 🟠 hwpctl Actions 호환 레이어
- **문제**: 한컴 웹기안기와 인터페이스 통일 가능성.
- **수용 기준**:
  - `hwpctl_action(name, params)` 단일 진입점
  - 30 Actions 중 사업계획서 워크플로우 핵심 10개 우선 (TableCreate, InsertText, CharShape, ParagraphShape, FontShape, TableCellBlockSetShape, BookmarkPut, FieldPut, PageBreak, FontInfo)
- **참고**: rhwp hwpctl 호환 레이어

## v0.4.x — rhwp 코어 통합

### B-09 🟢 `@rhwp/core` WASM 백엔드 통합 PoC
- **문제**: 자체 XML 패칭은 한컴 호환성 한계가 있음.
- **수용 기준**:
  - `wasmtime-py` 또는 `wasmer-python` 으로 `@rhwp/core` WASM 로드
  - `editor.py`, `writer.py` 의 일부 경로를 rhwp 호출로 대체하는 어댑터
  - 기존 회귀 테스트 통과
- **참고**: 사용자 지시 — "rhwp 백엔드 흡수"

## 운영 백로그

### O-01 🟡 `tests/fixtures/` 생성 + samples 의존 제거
- 합법 공개 가능한 최소 HWPX 시드 작성. `replicate_gridi_final.py` 를 fixture 기반으로 리팩터링.

### O-02 🟡 CI 파이프라인
- `gh actions`: lint(`ruff`) + test(`pytest --cov`) + Java 셋업
- 커버리지 80% 미만 시 PR block

### O-03 🟡 `docs/TOOLS.md` — 도구별 상세 레퍼런스
- 각 MCP tool 의 시그니처/예제/에러 케이스 문서화

### O-04 🟢 PyPI 배포
- `hatchling` 기반 빌드, GitHub Releases 트리거 자동 배포
