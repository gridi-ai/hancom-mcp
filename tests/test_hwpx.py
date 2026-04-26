"""Smoke tests for HWPX core functionality."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import hwpx_core as core


def test_create_and_save():
    """Create a document, add content, save, and re-read it."""
    # Create
    doc = core.create_hwpx(title="테스트 문서")
    assert doc.title == "테스트 문서"
    assert len(doc.sections) == 1

    # Insert text
    core.insert_text(doc, "안녕하세요, 한컴 라이터입니다.")
    core.insert_text(doc, "이것은 두 번째 단락입니다.")
    core.insert_text(doc, "세 번째 단락: 표 테스트 준비.")

    assert len(doc.sections[0].paragraphs) == 3
    assert "안녕하세요" in doc.get_all_text()

    # Insert table
    core.insert_table(
        doc,
        rows=[
            ["이름", "나이", "직업"],
            ["김철수", "30", "개발자"],
            ["이영희", "28", "디자이너"],
        ],
    )
    assert len(doc.sections[0].tables) == 1

    # Replace text
    count = core.replace_text(doc, "한컴 라이터", "Hancom Writer MCP")
    assert count == 1
    assert "Hancom Writer MCP" in doc.get_all_text()

    # Save
    with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
        out_path = f.name

    saved_path = core.save_hwpx(doc, out_path)
    print(f"✓ Saved to: {saved_path}")

    # Verify it's a valid ZIP
    import zipfile
    assert zipfile.is_zipfile(saved_path)

    with zipfile.ZipFile(saved_path, "r") as zf:
        names = zf.namelist()
        print(f"  ZIP entries: {names}")
        assert "mimetype" in names
        assert "Contents/section0.xml" in names
        assert "Contents/header.xml" in names

        # Check mimetype is first entry
        assert names[0] == "mimetype"
        assert zf.read("mimetype") == b"application/hwp+zip"

    # Re-read
    doc2 = core.read_hwpx(saved_path)
    assert doc2.title == "테스트 문서"
    assert len(doc2.sections) == 1
    assert len(doc2.sections[0].paragraphs) >= 3
    assert "Hancom Writer MCP" in doc2.get_all_text()
    print(f"✓ Re-read OK: {doc2.get_all_text()[:100]}...")

    # Check structure
    structure = doc2.get_structure()
    print(f"✓ Structure: {structure}")
    assert structure["title"] == "테스트 문서"

    # Verify tables were saved and re-read
    assert len(doc2.sections[0].tables) >= 1
    table = doc2.sections[0].tables[0]
    print(f"✓ Table: {len(table.rows)} rows")
    assert table.rows[0][0].text == "이름"
    assert table.rows[1][0].text == "김철수"

    # Cleanup
    Path(saved_path).unlink()
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_create_and_save()
