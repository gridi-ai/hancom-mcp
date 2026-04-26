# Contributing to hancom-mcp

이 문서는 `hancom-mcp` 에 기여하려는 분(혹은 자동화 에이전트)이 따라야 하는 워크플로우를 정리합니다.

## 작업 단위 — 백로그

모든 변경은 [`docs/BACKLOG.md`](docs/BACKLOG.md) 의 항목 1개에 대응합니다. 백로그에 없는 큰 변경은 먼저 이슈를 열어 합의하세요.

## 표준 사이클

```text
1.  백로그에서 항목 채택
2.  /ecc:plan
       └─ docs/plans/<id>-<slug>.md  생성
          ├─ 목표
          ├─ 수용 기준 (Acceptance Criteria)
          ├─ 영향 범위
          ├─ 인터페이스 설계
          └─ 리스크
3.  git checkout -b feat/<id>-<slug> main
4.  /ecc:tdd
       ├─ RED:    실패하는 테스트 작성
       ├─ GREEN:  최소 구현으로 통과
       └─ REFACTOR: 정리, 커버리지 80%+
5.  /ecc:review-pr
       ├─ 셀프 리뷰
       ├─ 린터/타입체크/테스트 모두 통과
       └─ PR 본문에 plans/<id>-<slug>.md 링크
6.  Squash merge → main
7.  CHANGELOG.md [Unreleased] 섹션 갱신
8.  백로그 항목 ✅ 표시
```

## 브랜치 네이밍

| prefix | 용도 |
|---|---|
| `feat/` | 새 기능 |
| `fix/` | 버그 수정 |
| `refactor/` | 동작 보존 리팩터링 |
| `docs/` | 문서만 |
| `chore/` | 빌드/메타파일 |
| `perf/` | 성능 |

형식: `<prefix>/<백로그-id>-<짧은-슬러그>` 예: `feat/B-01-insert-image`

## 커밋 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/ko/v1.0.0/) 따름.

```
feat(editor): add insert_image tool

이미지 파일 경로와 width/height/anchor를 받아 HWPX 단락에
ole 또는 picture 엘리먼트를 삽입한다.

Refs: B-01
```

## 코드 스타일

- Python 3.11+, 타입 힌트 필수
- `ruff format` + `ruff check` 통과
- 함수 50줄 / 파일 800줄 / 중첩 4단계 이하
- 변경 가능한 전역 상태 금지, 새 객체 반환 우선
- 한국어 주석 OK, 단 docstring 1줄 요약은 영어 권장 (도구 카탈로그 자동화)

## 테스트

- TDD 강제. `pytest` 기반.
- 커버리지 ≥ 80% (실측: `pytest --cov=hancom_writer`)
- 통합 테스트가 `samples/` (gitignore) 의 실제 문서를 의존하면 안 됨. `tests/fixtures/` 에 합법적으로 공개 가능한 최소 HWPX를 넣고 사용.

## 보안

- 절대 시크릿/토큰을 커밋하지 마세요
- `samples/`, `private/`, `local/` 은 영구 gitignore
- 의존성 추가 시 라이선스 호환 확인 (Apache-2.0 / BSD / MIT 우선, GPL 계열 금지)
- 보안 취약점은 공개 이슈 대신 메인테이너에 비공개로 보고

## 의존성 추가 규칙

| 종류 | 위치 | 라이선스 |
|---|---|---|
| Python 런타임 | `pyproject.toml` `[project] dependencies` | MIT/BSD/Apache-2.0 |
| 개발 도구 | `pyproject.toml` `[dependency-groups] dev` | 자유 |
| 번들 JAR | `lib/` + `NOTICE` 갱신 | 명시적으로 재배포 허용 |

## 라이선스 동의

PR 을 제출하면 본인의 기여물이 [MIT License](LICENSE) 로 배포됨에 동의하는 것으로 간주합니다. 회사·기관 IP 가 섞인 코드라면 PR 전에 권한을 확보하세요.
