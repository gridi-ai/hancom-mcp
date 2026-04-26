# B-13 — 변환 후 paragraph ID 정규화

## 문제

`hwp2hwpx.jar` 가 만든 HWPX `Contents/section{N}.xml` 안에:

- `<hp:p id="0">` 가 다수 등장 (중복)
- `<hp:p id="2147483648">` (= 2³¹) 같은 비정상 큰 값

HWPX OWPML 스펙은 단락 ID 가 unique 해야 하므로 한컴 뷰어가 손상으로 판정한다.

## 검증된 사실

- B-12 (보일러플레이트 보충), B-15 (lineseg 제거) 만으로는 변환 직후 손상이 잡히지 않는다.
- `secPr` (section properties) 단락은 보일러플레이트 기준 `id="0"` 으로 들어와야 한다 (B-13a 통합).
- `cellAddr` 같은 비-단락 참조는 paragraph id 와 의미가 다르므로 건드리면 안 된다.

## 해결 전략

`convert_hwp_to_hwpx` 가 `_run_jar` 호출 직후, 그 외 후처리(fill patch, cleanup)
들어가기 전에 신규 모듈 `id_normalizer.normalize_paragraph_ids(hwpx_path)`
를 호출한다.

### 알고리즘 (섹션별)

1. `Contents/section{N}.xml` 을 lxml 로 파싱.
2. `<hp:p>` 를 트리 순서로 순회.
3. paragraph 내부에 `<hp:secPr>` 가 있으면 `id="0"` 으로 강제.
4. 그 외 paragraph 는 1, 2, 3, … 순차 unique 값으로 재부여.
5. 표 내부 paragraph 도 같은 카운터를 공유하므로 충돌이 없다.
6. `<hp:cellAddr>` 같은 비-paragraph 요소는 건드리지 않는다 (loop 가 `<hp:p>` 만 본다).

## 수용 기준

- **단위**:
  - `tests/test_id_normalize.py`
    - `test_renumbers_duplicate_ids_per_section` — 중복 0 다수, 비정상 2³¹ 값 → unique 1..N
    - `test_preserves_secpr_paragraph_id_zero` — secPr 단락은 id=0 유지
    - `test_normalizes_table_inner_paragraphs` — `<hp:tbl>` 안 paragraph 도 재부여
    - `test_returns_total_renumbered_count`
    - `test_no_section_files_is_noop` — 섹션 없는 zip 은 그대로
- **통합**:
  - `convert_hwp_to_hwpx` 가 `_run_jar` 직후 normalizer 를 호출함을 mock 으로 검증
- **회귀**: 기존 21 개 통과

## 인터페이스 변경

- 신규 모듈: `src/hancom_writer/id_normalizer.py`
- `convert_hwp_to_hwpx` 가 내부적으로 호출. 외부 시그니처 무변경.
- 새 옵션 `normalize_ids: bool = True` 추가 (기본 True). 강제 비활성화 시
  legacy 동작 유지.

## 리스크

- HWPX 안에서 paragraph ID 를 참조하는 외부 요소가 있다면 깨질 수 있음.
  스펙상 paragraph ID 는 paragraph 자체 식별용이며, 외부 참조는 `cellAddr`
  (행/열 주소) 처럼 구분된 의미를 갖는다. 안전.
- `<hp:secPr>` 가 없는 (= 비정상) section 에서는 모두 1..N 만 부여 — 손상
  유발하지 않음.
