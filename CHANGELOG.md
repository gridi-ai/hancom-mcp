# Changelog

이 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고,
[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)을 준수합니다.

## [Unreleased]

### Added
- 프로젝트를 `gridi-ai/hancom-mcp` 공식 저장소로 이전.
- MIT LICENSE.
- 번들 Java 라이브러리(Apache 2.0)에 대한 `NOTICE` 및 `licenses/Apache-2.0.txt`.
- `docs/BACKLOG.md` — rhwp 비교 분석 기반 우선순위 백로그(B-01~B-11, O-01~O-04).
- `CONTRIBUTING.md` — `/ecc:plan → /ecc:tdd → /ecc:review-pr` 워크플로우.
- **B-06**: `create_document(template="default")` — 한컴 표준 22개 스타일 카탈로그
  (`바탕글, 본문, 개요 1..10, 머리말, 각주, 미주, 메모, 차례 제목,
  차례 1..3, 캡션, 쪽 번호`)를 새 문서에 자동 탑재.
  - `template="empty"` 옵션으로 기존 최소 헤더 동작도 보존.
  - `tests/test_default_template.py` — 5개 신규 단위 테스트.
- `tests/conftest.py` — `unit` / `integration` pytest 마크 등록.

### Changed
- 한국어 상세 README로 전면 개편.
- `writer.save_hwpx` 의 patched/new 분기 기준을 `raw_zip 의 mimetype 존재
  여부`로 변경 (이전: raw_zip 비어있음 여부). `create_hwpx` 가 헤더 템플릿을
  미리 주입해도 정상 동작.

### Security
- `samples/` 디렉토리(실제 사업계획서·회의록 포함)를 `.gitignore`로 격리.

---

## [0.1.0] - 2026-03-26

### Added
- HWPX 문서 읽기·쓰기 코어 (`hwpx_core`, `reader`, `writer`).
- HWP → HWPX 변환 (`conversion.py`, hwp2hwpx.jar 래퍼).
- `hwp_patcher` — fillBrush 손실을 hwplib에서 보정하는 후처리 파이프라인.
- `cleanup` — 안내문 제거, 색상 통일, 점선 테두리 제거.
- `styles` — 단락/문자 스타일 조회·정의·적용.
- MCP 서버 (`server.py`) — 16개 tool 노출:
  `convert_hwp_to_hwpx`, `cleanup_document`, `create_document`, `open_document`,
  `save_document`, `list_documents`, `get_text`, `get_structure`, `find_text`,
  `get_table_data`, `insert_text`, `list_styles`, `define_style`,
  `set_paragraph_style`, `replace_text`, `insert_table`.
- 번들 JAR: `hwp2hwpx.jar`, `hwplib.jar`, `hwpxlib.jar`,
  `hwpfilldump.jar`, `hwptabledump.jar`.
- 한컴 뷰어 자동 리로드(`viewer.py`).

[Unreleased]: https://github.com/gridi-ai/hancom-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gridi-ai/hancom-mcp/releases/tag/v0.1.0
