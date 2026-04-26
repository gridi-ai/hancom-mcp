# Loop Queue — Autonomous Backlog Execution

이 파일은 `/loop` 자율 실행이 다음에 처리할 백로그 항목을 추적합니다.
각 반복마다 큐의 첫 `pending` 항목을 처리하고, 완료 시 ✅ 로 표시합니다.

## 처리 순서

1. ✅ B-06 — 표준 스타일 자동 탑재 (PR #1, 머지 완료 2026-04-26)
2. ✅ B-04 — `delete_paragraph` / `delete_table` / `clear_section` (PR #2 머지)
3. ✅ B-12 — patched 저장 표준 엔트리 자동 보충 (PR #3 머지)
4. ⏳ B-13 — 변환 후 paragraph ID 정규화 (CRITICAL: hwp2hwpx ID 충돌)
5. ⏳ B-14 — XML 직렬화 namespace 보존 (CRITICAL: ET 가 13개 prefix 제거)
6. ⏳ B-01 — `insert_image`
7. ⏳ B-02 — `set_run_style` (CharShape)
8. ⏳ B-03 — 표 후편집 도구 묶음 (merge_cells, add_row 등)
9. ⏳ B-05 — page break + header/footer
10. ⏳ B-07 — Field API
11. ⏳ B-08 — hwpctl 30 Actions 호환층
12. ⏳ B-10 — viewer 를 한컴 → rhwp 전환
13. ⏳ B-11 — rhwp fork 후 WS 라이브 프리뷰 + upstream PR
14. ⏳ B-09 — `@rhwp/core` WASM 백엔드 통합 PoC

## 종료 조건

- 모든 항목이 ✅ 가 되면 루프 종료.
- 한 항목이 3회 연속 실패하면 일시 정지하고 보고 후 종료.
- main 에 push 권한이 없거나 PR 머지 불가 시 즉시 정지.

## 이번 반복에서 할 일

각 반복은 **정확히 한 항목** 만 처리해야 합니다.

1. 큐 첫 `pending` 항목 ID 식별 (예: `B-04`)
2. `git checkout main && git pull --ff-only`
3. `git checkout -b feat/<ID>-<slug> main`
4. `docs/plans/<ID>-<slug>.md` 작성 (요구사항·수용 기준·인터페이스·리스크)
5. RED — 실패 테스트 작성, `pytest` 로 실패 확인
6. GREEN — 최소 구현, `pytest` 통과
7. REFACTOR — 정리, 회귀 검사
8. CHANGELOG `[Unreleased]` 갱신
9. `git commit -m "feat(<ID>): ..."` (Conventional Commits)
10. `git push -u origin feat/<ID>-<slug>`
11. `gh pr create` (요약·테스트 플랜·plan 링크 포함)
12. `gh pr merge --squash --delete-branch`
13. 큐의 해당 항목을 ✅ 로 갱신
14. 컨텍스트 사용량/잔여 항목 보고 후 종료

## 안전 장치

- 절대 `git push --force`, `--no-verify`, `git reset --hard origin` 사용 금지.
- 푸시 직전 `git ls-files | xargs grep -lEi '(api[_-]?key|secret|password|/Users/)'`
  로 민감정보 잔존 여부 재확인.
- 브랜치 작업 중 충돌 발생 시 정지 후 보고.
