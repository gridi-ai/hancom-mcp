# B-15 — patched 저장 시 `<hp:linesegarray>` 통째 제거

## 문제

HWPX `<hp:p>` 단락은 텍스트뿐 아니라 그 텍스트의 layout 결과
(`<hp:linesegarray>` — 줄별 textpos / textheight / vertSize 등) 를 함께
저장한다. 우리가 텍스트를 바꾸면 lineseg 가 어긋난다.

- **F1·F2·F3** (단일 `hp:t` 변경) → 한컴 뷰어 정상
- **G2** (같은 paragraph 안 2개 hp:t 변경, 합계 길이 −71) → 손상
- **I2·J1** (같은 paragraph 안 2개 변경, 합계 길이 보존) → 정상
- **K2b** (영어 chunk 다수 제거 + 모든 `<hp:linesegarray>` 통째 제거) → 정상

⇒ paragraph 합계 길이가 변하는 순간 lineseg 가 한컴 뷰어를 손상으로 유도한다.

## 근본 해결책

우리가 `_build_patched_zip` 으로 손댄 모든 section XML 에서 `<hp:linesegarray>`
요소를 통째 제거한다. 한컴 뷰어는 lineseg 가 없으면 첫 열 때 자체 layout
engine 으로 다시 계산한다 (K2b 검증 완료).

WASM 의존 없이 순수 Python 패치만으로 해결된다.

## 수용 기준

- `_build_patched_zip` 이 모든 섹션 XML 에서 `<hp:linesegarray>` 요소를
  제거한다 (텍스트 변경 여부와 무관하게 전체 일괄 — 부분 제거는
  paragraph 합계 길이 보존을 보장 못 한다).
- 기존 회귀 테스트 14 + B-12 5 = 19 개 모두 통과.
- 신규 테스트:
  - `test_patched_save_strips_linesegarray_from_all_paragraphs`
  - `test_patched_save_preserves_text_runs_when_stripping_linesegarray`
  - `test_new_save_does_not_emit_linesegarray` (`_build_new_zip` 경로
    회귀 — 새로 만든 doc 도 lineseg 가 없어야 한다)

## 인터페이스 변경

없음. `_build_patched_zip` 내부 동작만 변한다.

## 리스크

- `<hp:linesegarray>` 가 `<hp:p>` 외에 다른 위치에서도 등장한다면 의도치
  않게 제거될 수 있음. HWPX OWPML 스펙상 lineseg 는 paragraph 의 layout
  cache 이므로 paragraph 자식으로만 등장한다.
- 단일 hp:t 변경 케이스 (F1·F2·F3) 도 lineseg 가 사라지면 한컴 뷰어가
  layout 을 처음부터 계산해야 한다 → 첫 열기 약간 느려질 수 있음.
  사용자 검증 결과 K2b 가 정상이었으므로 실용적 영향은 무시 가능.
