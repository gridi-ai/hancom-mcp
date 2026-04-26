"""B-04: delete_paragraph / delete_table / clear_section."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import editor, hwpx_core as core, styles


@pytest.fixture
def populated_doc():
    doc = core.create_hwpx(title="seed")
    editor.insert_text(doc, "첫째 단락", style="본문")
    editor.insert_text(doc, "둘째 단락", style="본문")
    editor.insert_text(doc, "셋째 단락", style="본문")
    editor.insert_table(doc, [["a", "b"], ["c", "d"]])
    editor.insert_table(doc, [["x"], ["y"]])
    return doc


@pytest.mark.unit
def test_delete_paragraph_removes_only_target(populated_doc) -> None:
    target = populated_doc.sections[0].paragraphs[1]
    target_id = target.id
    other_ids = [p.id for p in populated_doc.sections[0].paragraphs if p.id != target_id]

    removed = editor.delete_paragraph(populated_doc, target_id)

    remaining_ids = [p.id for p in populated_doc.sections[0].paragraphs]
    assert removed.id == target_id
    assert remaining_ids == other_ids
    assert len(remaining_ids) == 2


@pytest.mark.unit
def test_delete_paragraph_unknown_id_raises(populated_doc) -> None:
    with pytest.raises(LookupError):
        editor.delete_paragraph(populated_doc, paragraph_id=999_999)


@pytest.mark.unit
def test_delete_table_removes_only_target(populated_doc) -> None:
    first_table = populated_doc.sections[0].tables[0]
    second_table_id = populated_doc.sections[0].tables[1].id

    removed = editor.delete_table(populated_doc, table_id=first_table.id)

    remaining_ids = [t.id for t in populated_doc.sections[0].tables]
    assert removed.id == first_table.id
    assert remaining_ids == [second_table_id]


@pytest.mark.unit
def test_delete_table_unknown_id_raises(populated_doc) -> None:
    with pytest.raises(LookupError):
        editor.delete_table(populated_doc, table_id=999_999)


@pytest.mark.unit
def test_clear_section_removes_all_content(populated_doc) -> None:
    style_count_before = len(styles.list_styles(populated_doc))

    removed = editor.clear_section(populated_doc, section_index=0)

    section = populated_doc.sections[0]
    assert section.paragraphs == []
    assert section.tables == []
    assert removed == 5  # 3 paragraphs + 2 tables
    # Styles must be preserved by default.
    assert len(styles.list_styles(populated_doc)) == style_count_before


@pytest.mark.unit
def test_clear_section_on_empty_section_is_noop() -> None:
    doc = core.create_hwpx(title="empty")
    removed = editor.clear_section(doc, section_index=0)
    assert removed == 0
    assert doc.sections[0].paragraphs == []


@pytest.mark.unit
def test_clear_section_invalid_index_raises() -> None:
    doc = core.create_hwpx(title="x")
    with pytest.raises(IndexError):
        editor.clear_section(doc, section_index=5)
