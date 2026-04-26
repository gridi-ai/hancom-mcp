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

### B-12 🔴 patched 저장 시 누락된 표준 엔트리 자동 보충
- **문제**: `hwp2hwpx.jar` 가 만든 HWPX 는 `Preview/PrvText.txt`,
  `Scripts/headerScripts`, `Scripts/sourceScripts`, `META-INF/container.rdf`
  등 한컴 뷰어가 기대하는 엔트리를 일부 빠뜨린다. 우리 `_build_patched_zip`
  은 raw_zip 을 그대로 보존하므로 이 결손이 그대로 따라가서 한컴 뷰어가
  "문서 손상" 으로 판단한다.
- **재현**: 양식 hwp 변환 → `replace_text` 로 편집 → `save_document` →
  한컴 뷰어로 열기 → 손상 경고. ZIP 자체는 무결.
- **수용 기준**:
  - `_build_patched_zip` 이 표준 엔트리 5종(`Preview/PrvText.txt`,
    `Scripts/headerScripts`, `Scripts/sourceScripts`, `META-INF/container.rdf`,
    `META-INF/manifest.xml` 보강) 누락 시 templates.py 의 보일러플레이트로
    자동 채움.
  - `Preview/PrvText.txt` 는 `doc.get_all_text()[:500]` 로 동적 생성.
  - `container.xml` 의 rootfile 참조 중 ZIP 에 없는 엔트리는 참조 제거 또는
    누락 엔트리 보충 — 일관성 검증.
  - 양식 변환 → 편집 → 저장 → 한컴 뷰어 정상 오픈 통합 테스트.
- **참고**: 사용자 보고 (2026-04-26)

### B-13 🔴 변환 후 paragraph ID 정규화
- **문제**: `hwp2hwpx.jar` 가 만든 HWPX 의 `section{N}.xml` 안에 paragraph
  `id="0"` 가 다수 등장하고 `id="2147483648"` (=2^31) 같은 비정상 큰 값이
  섞임. HWPX 스펙은 단락 ID 가 unique 해야 하므로 한컴 뷰어가 이를
  손상으로 판정한다.
- **재현**: 양식 hwp 변환 직후 `section0.xml` 의 모든 `<hp:p>` ID 검사 →
  `id="0"` 2회 이상, 일부는 2^31 값.
- **수용 기준**:
  - `convert_hwp_to_hwpx` 가 반환 직전에 모든 섹션의 paragraph ID 를
    section-별로 1부터 순차 unique 값으로 재부여.
  - 표 내부 paragraph 도 충돌 없이 재부여.
  - `cellAddr` 같은 단락 외 참조에는 영향 없음을 확인.
  - 통합 테스트: 변환 → ID 검증 → 한컴 뷰어 정상 오픈.
- **참고**: 사용자 보고 (2026-04-26, B-12 보충 후에도 손상 지속). 큐 우선순위 B-12 다음.

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

### B-10 🟠 viewer를 한컴 → rhwp 로 전환
- **문제**: `viewer.py` 가 macOS 한컴 오피스 앱(설치 필요·유료·플랫폼 종속)에 의존.
  공개 배포본에서 누구나 결과를 보려면 OSS 뷰어가 필요.
- **수용 기준**:
  - `viewer.py` 가 [`@rhwp/editor`](https://www.npmjs.com/package/@rhwp/editor) 또는
    [edwardkim.github.io/rhwp](https://edwardkim.github.io/rhwp/) 데모를 백엔드로
    선택 가능 (`HANCOM_MCP_VIEWER` 환경변수).
  - `save_document(auto_reload=True)` 호출 시 rhwp 뷰어가 같은 HWPX 를 자동 갱신.
  - 한컴 미설치 환경에서 macOS/Windows/Linux 동일 동작.
- **참고**: 사용자 직접 요청

### B-11 🔴 rhwp 뷰어에 MCP 변경 실시간 반영 (live preview)
- **문제**: 매 `save_document` 후 수동 reload 가 아닌, 메모리 변경분을 즉시
  뷰어에 푸시하면 사업계획서 작성 흐름이 훨씬 빨라짐.
- **전략 (사용자 지시)**:
  1. `edwardkim/rhwp` 를 `gridi-ai/rhwp` 로 fork
  2. fork 에 `ws://localhost:<port>` 리스너를 추가하여 외부 변경 이벤트를 수신,
     `HwpDocument` 인스턴스를 즉시 재렌더링
  3. hancom-mcp 측에 WS broadcaster 추가 — `insert_text`/`insert_table` 등
     성공 직후 변경 페이로드 송출
  4. fork 안정화 후 upstream `edwardkim/rhwp` 에 PR 로 제안
- **수용 기준**:
  - hancom-mcp: `tools` 호출 직후 변경 이벤트가 WS 로 전송됨 (단위 테스트)
  - gridi-ai/rhwp fork: WS 클라이언트 모듈 + 데모 페이지에서 라이브 갱신
  - 100ms 이내 뷰어 반영 (저장 round-trip 없음)
  - upstream PR draft 가 `edwardkim/rhwp` 에 열림 (자동 머지 보장은 없음)
- **선행조사** (plan 단계):
  - rhwp 의 현재 reload 트리거 방식 (파일 watch? 매 클릭마다 재파싱?)
  - WS 인터페이스가 rhwp 디자인 원칙(Rust + WASM, no server runtime)과
    충돌하지 않는지 확인. 충돌 시 `BroadcastChannel` 또는 `SharedWorker`
    같은 브라우저 표준 대안 검토.

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
