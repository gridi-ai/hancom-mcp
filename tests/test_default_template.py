"""B-06: `create_hwpx(template=...)` should pre-load standard Hancom styles.

Tests follow Arrange-Act-Assert. Marked `unit` so they can run without Java.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import hwpx_core as core
from hancom_writer import editor, styles


REQUIRED_STANDARD_STYLES = {
    "바탕글",
    "본문",
    "개요 1",
    "개요 2",
    "개요 3",
    "개요 4",
    "개요 5",
    "개요 6",
    "개요 7",
    "개요 8",
    "개요 9",
    "개요 10",
    "머리말",
    "각주",
    "미주",
    "메모",
    "차례 제목",
    "차례 1",
    "차례 2",
    "차례 3",
    "캡션",
    "쪽 번호",
}


@pytest.mark.unit
def test_default_template_loads_standard_styles() -> None:
    # Arrange / Act
    doc = core.create_hwpx(title="기본 템플릿")

    # Assert
    catalogue = {s.name for s in styles.list_styles(doc)}
    missing = REQUIRED_STANDARD_STYLES - catalogue
    assert not missing, f"missing standard styles: {missing}"


@pytest.mark.unit
def test_default_template_is_implicit_default() -> None:
    explicit = core.create_hwpx(title="t1", template="default")
    implicit = core.create_hwpx(title="t1")

    explicit_names = {s.name for s in styles.list_styles(explicit)}
    implicit_names = {s.name for s in styles.list_styles(implicit)}
    assert explicit_names == implicit_names


@pytest.mark.unit
def test_empty_template_has_minimal_styles() -> None:
    doc = core.create_hwpx(title="empty", template="empty")

    catalogue = {s.name for s in styles.list_styles(doc)}
    # "Empty" mode keeps the legacy single-style header for back-compat.
    assert "본문" in catalogue
    assert len(catalogue) <= 1


@pytest.mark.unit
def test_insert_text_with_outline_style_succeeds_on_default_doc() -> None:
    # Arrange
    doc = core.create_hwpx(title="개요 사용")

    # Act
    editor.insert_text(doc, "1. 일반 현황", style="개요 1")

    # Assert
    paragraphs = doc.sections[0].paragraphs
    assert paragraphs[-1].text == "1. 일반 현황"
    outline1 = styles.find_style(doc, "개요 1")
    assert outline1 is not None
    assert paragraphs[-1].style_id == outline1.id


@pytest.mark.unit
def test_unknown_template_raises_value_error() -> None:
    with pytest.raises(ValueError, match="template"):
        core.create_hwpx(title="x", template="bogus")
