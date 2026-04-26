# hancom-mcp

> **HWP/HWPX 문서를 LLM이 직접 읽고 쓸 수 있게 해주는 MCP 서버**
> — 한글(.hwp / .hwpx) 문서를 Claude·다른 LLM 에이전트에서 자연어로 조작합니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)

한컴 오피스(아래아한글)의 HWP·HWPX 파일을 LLM 친화적인 [Model Context Protocol](https://modelcontextprotocol.io) 도구로 추상화한 서버입니다. Claude Desktop·Claude Code·Cursor 등 MCP를 지원하는 클라이언트에서 자연어로 문서 변환·조회·작성·수정·검색을 할 수 있습니다.

## 왜 만들었나요

공공기관·대학·국내 기업이 의존하는 한글 문서 포맷은 LLM 도구 생태계에서 거의 1급 시민이 아닙니다. 사업계획서·보고서·회의록을 자동으로 작성·수정하려면 결국 사람이 한글 뷰어를 켜고 손으로 옮겨야 했습니다. `hancom-mcp` 는 이 간극을 메우는 것이 목표입니다.

## 주요 기능

### 변환
- **HWP → HWPX** 자동 변환 (`hwp2hwpx.jar` + 자체 fillBrush 보정 패치)
- 변환 후 안내문 텍스트(`※`, `☞`, `◈`) 제거, 색상 통일, 점선 테두리 정리 옵션

### 읽기
- HWPX 문서를 메모리에 로드하여 섹션·단락·표 구조를 그대로 노출
- 표 셀 단위 텍스트 추출
- 단락/표 ID 기반 정밀 조회

### 쓰기
- 텍스트 단락 삽입 (스타일 지정 가능)
- 표 삽입 (헤더 + 행 단위)
- 텍스트 검색 후 일괄 치환
- 단락 스타일 적용

### 스타일
- 문서에 정의된 스타일 카탈로그 조회 (개요 1~10, 본문, 머리말, 캡션 등)
- 새 스타일 정의 (폰트 크기, 색상, 음영, 정렬, 줄간격, 들여쓰기, 굵게/기울임/밑줄)
- 단락에 스타일 적용/변경

### 한컴 뷰어 통합
- 저장 시 한컴 뷰어가 열려 있으면 자동 리로드 트리거 (macOS 기준)

전체 도구 목록은 [`docs/TOOLS.md`](docs/TOOLS.md) 참고.

## 빠른 시작

### 사전 요구사항
- **Python 3.11 이상**
- **Java 17 이상** (HWP→HWPX 변환에 필요. JRE/JDK 모두 가능)
  - macOS: `brew install openjdk@21`
  - Ubuntu: `sudo apt install openjdk-21-jre`
- (선택) **한컴 오피스 / 한글 뷰어** — 저장 시 자동 리로드를 원할 경우

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/gridi-ai/hancom-mcp.git
cd hancom-mcp

# 2. 가상환경 생성 및 의존성 설치
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .

# 3. Java 설치 확인
java -version
```

### Claude Desktop 등록 (macOS)

`~/Library/Application Support/Claude/claude_desktop_config.json` 에 다음을 추가:

```json
{
  "mcpServers": {
    "hancom-mcp": {
      "command": "/절대경로/hancom-mcp/.venv/bin/python",
      "args": ["-m", "hancom_writer.server"],
      "cwd": "/절대경로/hancom-mcp"
    }
  }
}
```

> Claude Desktop을 재시작하면 도구 목록에 16개의 `hancom-mcp__*` 도구가 노출됩니다.

### Claude Code 등록

```bash
claude mcp add hancom-mcp \
  /절대경로/hancom-mcp/.venv/bin/python \
  -m hancom_writer.server \
  --cwd /절대경로/hancom-mcp
```

### 첫 사용 예시 (자연어)

> "이 hwp 파일을 hwpx로 변환해서 열어줘:
> /Users/me/Downloads/사업계획서.hwp"

> "방금 연 문서에서 '매출 1억원'을 '매출 2억원'으로 바꿔줘"

> "본문 스타일로 '결론: 본 사업은 2027년 흑자전환을 목표로 한다.' 추가해줘"

> "팀 구성 표를 4행 4열로 새로 추가해줘. 헤더는 역할/이름/담당/경력"

## 도구 카탈로그 (16종)

| 분류 | 도구 | 설명 |
|---|---|---|
| 변환 | `convert_hwp_to_hwpx` | HWP 바이너리를 HWPX로 변환, 옵션으로 정리 작업 |
| 변환 | `cleanup_document` | 안내문/색상/점선 일괄 정리 |
| 문서 | `create_document` | 빈 HWPX 생성 |
| 문서 | `open_document` | 기존 HWPX 로드 |
| 문서 | `save_document` | 메모리 변경분을 디스크에 저장 + 뷰어 리로드 |
| 문서 | `list_documents` | 메모리에 열려있는 문서 목록 |
| 조회 | `get_text` | 전체 텍스트 추출 |
| 조회 | `get_structure` | 섹션/단락/표 구조 트리 |
| 조회 | `find_text` | 단순 검색 |
| 조회 | `get_table_data` | 표 셀 단위 2D 배열 |
| 편집 | `insert_text` | 단락 추가, 스타일 지정 가능 |
| 편집 | `insert_table` | 헤더+행으로 표 추가 |
| 편집 | `replace_text` | 일괄 치환 |
| 스타일 | `list_styles` | 정의된 스타일 카탈로그 |
| 스타일 | `define_style` | 새 스타일 정의 |
| 스타일 | `set_paragraph_style` | 기존 단락 스타일 변경 |

각 도구의 파라미터·반환값은 [`docs/TOOLS.md`](docs/TOOLS.md) 에 자세히 정리되어 있습니다.

## 로드맵

`hancom-mcp` 는 단계적 성숙을 추구합니다. 구체 항목은 [`docs/BACKLOG.md`](docs/BACKLOG.md) 참고.

| 단계 | 목표 |
|---|---|
| **v0.2.x** | 사업계획서/보고서 워크플로우의 핵심 결손 도구 보완 (이미지, 셀 병합, 페이지 나누기, 머리말/꼬리말, CharShape) |
| **v0.3.x** | hwpctl 호환 레이어 — Field API, ParameterSet, 30 Actions 흡수 |
| **v0.4.x** | [`@rhwp/core`](https://github.com/edwardkim/rhwp) WASM을 백엔드로 통합, 자체 XML 패칭 의존도 축소 |
| **v1.0.0** | 공공·민간에 재배포 가능한 안정 버전 |

## 기여 방법

이 프로젝트는 **백로그 기반 + 브랜치당 PR + squash 머지** 워크플로우로 운영됩니다.

```text
백로그 항목 채택
   ↓
/ecc:plan      ← 설계서 + 수용 기준 작성
   ↓
git checkout -b feat/<백로그-id>-<짧은-슬러그> main
   ↓
/ecc:tdd       ← RED-GREEN-REFACTOR로 구현
   ↓
/ecc:review-pr ← PR 생성, 셀프 리뷰 + 자동 검사
   ↓
squash merge → main
   ↓
CHANGELOG 갱신
```

자세한 규칙은 [`CONTRIBUTING.md`](CONTRIBUTING.md) 참고.

## 라이선스

이 프로젝트는 [MIT License](LICENSE) 입니다.

`lib/` 에 번들된 다음 라이브러리는 **Apache License 2.0** 입니다 (저작권자: Park Sungkyon, [@neolord0](https://github.com/neolord0)). 자세한 출처·권리표시는 [`NOTICE`](NOTICE) 와 [`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt) 를 참고하세요.

- [hwp2hwpx](https://github.com/neolord0/hwp2hwpx)
- [hwplib](https://github.com/neolord0/hwplib)
- [hwpxlib](https://github.com/neolord0/hwpxlib)

## 영감

오픈소스 한컴 에디터 [`rhwp`](https://github.com/edwardkim/rhwp) (Rust + WASM, MIT License) 의 기능 비교를 통해 백로그를 도출했습니다. `rhwp` 의 코드는 본 저장소에 포함되어 있지 않습니다.

## 문의·이슈

- 버그·기능 요청: [GitHub Issues](https://github.com/gridi-ai/hancom-mcp/issues)
- 보안 이슈: 공개 이슈로 올리지 말고 메인테이너에게 비공개로 알려주세요.
