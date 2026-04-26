"""Create a sample HWPX file for testing with Hancom Office."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import hwpx_core as core

# Create a sample document
doc = core.create_hwpx(title="한컴 라이터 PoC 테스트")

core.insert_text(doc, "한컴 라이터 MCP PoC")
core.insert_text(doc, "이 문서는 AI가 HWPX 형식으로 직접 생성한 문서입니다.")
core.insert_text(doc, "")
core.insert_text(doc, "주요 기능:")
core.insert_text(doc, "1. HWPX 문서 생성 및 읽기")
core.insert_text(doc, "2. 텍스트 삽입, 검색, 치환")
core.insert_text(doc, "3. 표 삽입")
core.insert_text(doc, "4. MCP 프로토콜을 통한 AI 도구 연동")
core.insert_text(doc, "")

# Insert a table
core.insert_table(
    doc,
    rows=[
        ["기능", "상태", "비고"],
        ["문서 생성", "완료", "HWPX XML 직접 생성"],
        ["문서 읽기", "완료", "ZIP/XML 파싱"],
        ["텍스트 삽입", "완료", "단락 단위"],
        ["텍스트 치환", "완료", "전체 문서 대상"],
        ["표 삽입", "완료", "N×M 지원"],
        ["이미지 삽입", "미구현", "Phase 2"],
        ["스타일 적용", "미구현", "Phase 2"],
    ],
)

core.insert_text(doc, "")
core.insert_text(doc, "이 파일을 한컴오피스에서 열어 정상적으로 표시되는지 확인하세요.")

out_path = Path(__file__).parent.parent / "samples" / "sample.hwpx"
saved = core.save_hwpx(doc, str(out_path))
print(f"Sample created: {saved}")
