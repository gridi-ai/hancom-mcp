# B-01 — `insert_image` (MVP)

## 문제

사업계획서·보고서에 로고·도식 삽입 불가. HWPX `<hp:pic>` 요소를 만들어
넣으려면 파일 BinData 등록 + manifest 등록 + header.xml 의 binData 목록 +
section XML 의 `<hp:pic>` 까지 4 군데를 일관되게 갱신해야 한다.

## MVP 범위

한 PR 분량을 정하기 위해 다음 범위로 자른다:

- **지원 포맷**: PNG / JPEG (확장자 기준 media-type 결정)
- **앵커**: `treat-as-char` 만 (인라인 — 텍스트와 함께 흐름)
- **단위**: `width_mm`, `height_mm` 명시 필수 (자동 추출 X)
- **저장 경로**: `_build_new_zip` (`create_document` → `insert_image` →
  `save_document`) 만 우선 지원. 변환된 HWPX 패치 저장 (`_build_patched_zip`)
  에서의 이미지 삽입은 별도 백로그(B-01b 또는 B-03 표 후편집 묶음과
  함께)로.
- **렌더링**: `<hp:pic>` syntactically-valid HWPX 출력만 보장. 한컴 뷰어
  실제 렌더링 검증은 사용자 수동 확인 단계.

## 인터페이스

신규 도메인 모델:

```python
@dataclass
class InlineImage:
    bin_data_id: int       # 1-based, matches binDataList in header.xml
    media_type: str        # "image/png" | "image/jpeg"
    href: str              # e.g. "BinData/image1.png"
    width_mm: float
    height_mm: float
```

`Paragraph` 에 `image: InlineImage | None = None` 추가.

신규 에디터 API:

```python
def insert_image(
    doc: HwpxDocument,
    image_path: str,
    width_mm: float,
    height_mm: float,
    section_index: int = 0,
) -> Paragraph
```

새 단락을 만들어 이미지를 인라인으로 부착한다. 반환은 생성된 `Paragraph`.

신규 MCP tool: `insert_image(doc_id, image_path, width_mm, height_mm, section_index=0)`.

## 저장 경로 변경

`_build_new_zip` 가 다음을 추가한다:

1. `entries[image.href] = src bytes` — raw_zip 에 이미 들어있음(`insert_image`
   가 stash). pass-through.
2. `META-INF/manifest.xml` — 등록된 모든 이미지를 `<odf:file-entry>` 로
   기재. 기존은 빈 manifest 였음.
3. `Contents/header.xml` — `<hh:refList>` 안에 `<hh:binDataList>` 블록 추가.
4. `Contents/section{N}.xml` — 이미지 단락에 `<hp:pic>` 요소 렌더링
   (treat-as-char anchor).

## 수용 기준

### 단위
- `test_insert_image_creates_paragraph_with_image`
- `test_insert_image_rejects_missing_file`
- `test_insert_image_rejects_unsupported_extension`
- `test_insert_image_assigns_unique_bin_data_ids`

### 통합 (save → reopen zip)
- `test_save_writes_bindata_entry_to_zip`
- `test_save_registers_image_in_manifest`
- `test_save_registers_image_in_header_bin_data_list`
- `test_save_emits_pic_element_in_section_xml`

### 회귀
- 기존 30개 통과

## 리스크

- HWPX `<hp:pic>` 스펙은 매우 풍부 (effect, lineShape, drawText, …). 우리는
  최소 뼈대만 출력 — 한컴 뷰어가 누락 속성을 손상으로 판정할 가능성 있음.
  → 사용자 수동 검증 단계에서 확인. 손상 시 binDataList 우선, `<hp:pic>`
  속성 보강 순으로 follow-up.
- `_build_patched_zip` 경로(변환된 HWPX 에 이미지 추가) 는 본 MVP 범위
  밖. 사업계획서 자동화에서 빈 템플릿에 이미지를 넣는 케이스가 우선이라
  타당.
