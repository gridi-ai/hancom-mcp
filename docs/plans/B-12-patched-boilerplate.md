# B-12: patched 저장 시 누락된 표준 엔트리 자동 보충

## 요구사항 재진술

`hwp2hwpx.jar` 가 만든 HWPX 는 한컴 뷰어가 기대하는 표준 엔트리
(`Preview/PrvText.txt`, `Scripts/headerScripts`, `Scripts/sourceScripts`,
`META-INF/container.rdf`) 를 일부 빠뜨린다. 우리 `_build_patched_zip` 은
`raw_zip` 을 그대로 보존하므로 이 결손이 재패킹된 HWPX 에도 그대로
유지되어 한컴 뷰어가 "문서 손상" 으로 판정한다.

## 수용 기준

- AC1. `save_document` 의 patched 경로가 ZIP 출력 시 다음 4개 엔트리가
  raw_zip 에 없으면 보일러플레이트로 자동 보충한다.
  - `Preview/PrvText.txt` — `doc.get_all_text()[:500]` UTF-8
  - `Scripts/headerScripts` — `templates.HEADER_SCRIPTS` 그대로
  - `Scripts/sourceScripts` — `templates.SOURCE_SCRIPTS` 그대로
  - `META-INF/container.rdf` — `templates.CONTAINER_RDF` 그대로
- AC2. raw_zip 에 이미 있는 엔트리는 보존 (덮어쓰지 않음).
- AC3. `META-INF/container.xml` 의 rootfile 참조가 ZIP 에 누락된 엔트리를
  가리키면 보충 후 일치한다.
- AC4. 회귀: 14개 기존 테스트 통과.
- AC5. 통합 테스트: 4개 엔트리 누락된 raw_zip 으로 시뮬레이션 →
  `save_hwpx` → 결과 ZIP 에 4 엔트리 모두 존재 확인.

## 인터페이스

`writer._build_patched_zip` 내부에서 처리. 외부 API 변경 없음.

```python
# src/hancom_writer/writer.py
def _build_patched_zip(doc: HwpxDocument) -> bytes:
    patched = dict(doc.raw_zip)
    # ... existing section patch ...
    _ensure_standard_boilerplate(patched, doc)
    return _pack_zip(patched)

def _ensure_standard_boilerplate(
    entries: dict[str, bytes],
    doc: HwpxDocument,
) -> None:
    """Fill in entries that hwp2hwpx omits but Hancom Viewer expects."""
    if 'Preview/PrvText.txt' not in entries:
        entries['Preview/PrvText.txt'] = doc.get_all_text()[:500].encode('utf-8')
    if 'Scripts/headerScripts' not in entries:
        entries['Scripts/headerScripts'] = T.HEADER_SCRIPTS
    if 'Scripts/sourceScripts' not in entries:
        entries['Scripts/sourceScripts'] = T.SOURCE_SCRIPTS
    if 'META-INF/container.rdf' not in entries:
        entries['META-INF/container.rdf'] = T.CONTAINER_RDF.encode('utf-8')
```

## 구현 전략

1. `templates.py` 에 `HEADER_SCRIPTS`, `SOURCE_SCRIPTS`, `CONTAINER_RDF` 가
   이미 존재 — 신규 추가 없이 import 만 사용.
2. `_build_patched_zip` 에 한 줄 헬퍼 호출 추가.
3. 테스트는 fake `HwpxDocument` 의 `raw_zip` 에 mimetype + minimal entries
   넣고 `save_hwpx` 호출, 결과 ZIP 에 4 엔트리 존재 확인.

## 영향 범위

- `src/hancom_writer/writer.py` — `_ensure_standard_boilerplate` 추가, 호출
- `tests/test_patched_boilerplate.py` — 신규 (RED→GREEN)

## 리스크

- `_pack_zip` 의 mimetype STORED + 나머지 DEFLATED 동작은 그대로 유지.
- raw_zip 가 mimetype 을 가진 경우 (`if "mimetype" in doc.raw_zip:` 분기)
  에서만 patched 경로 진입 — 새로 만든 doc 에는 영향 없음.
