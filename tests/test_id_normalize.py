"""B-13: paragraph ID normalization after hwp2hwpx conversion."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hancom_writer import conversion, id_normalizer
from hancom_writer import templates as T


def _zip_with_section(tmp_path: Path, section_xml: bytes) -> Path:
    """Build a minimal .hwpx zip containing one section payload."""
    out = tmp_path / "doc.hwpx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            zipfile.ZipInfo("mimetype"),
            T.MIMETYPE.encode("utf-8"),
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("Contents/section0.xml", section_xml)
    return out


SECTION_DUPLICATE_IDS = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
    b' xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:run charPrIDRef="0"><hp:t>first</hp:t></hp:run></hp:p>'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:run charPrIDRef="0"><hp:t>second (dup)</hp:t></hp:run></hp:p>'
    b'<hp:p id="2147483648" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:run charPrIDRef="0"><hp:t>third (huge)</hp:t></hp:run></hp:p>'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:secPr/>'
    b'<hp:run charPrIDRef="0"><hp:t>secPr</hp:t></hp:run></hp:p>'
    b'</hs:sec>'
)


SECTION_WITH_TABLE_PARAGRAPHS = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
    b' xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:run charPrIDRef="0">'
    b'<hp:tbl id="11" rowCnt="1" colCnt="1">'
    b'<hp:tr><hp:tc><hp:subList>'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:run charPrIDRef="0"><hp:t>cell text</hp:t></hp:run></hp:p>'
    b'</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/></hp:tc></hp:tr>'
    b'</hp:tbl>'
    b'</hp:run></hp:p>'
    b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0">'
    b'<hp:secPr/></hp:p>'
    b'</hs:sec>'
)


def _para_ids(section_bytes: bytes) -> list[str]:
    from lxml import etree as LET

    HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    root = LET.fromstring(section_bytes)
    return [p.get("id") for p in root.iter(f"{{{HP}}}p")]


@pytest.mark.unit
def test_renumbers_duplicate_ids_per_section(tmp_path: Path) -> None:
    hwpx = _zip_with_section(tmp_path, SECTION_DUPLICATE_IDS)
    id_normalizer.normalize_paragraph_ids(str(hwpx))

    with zipfile.ZipFile(hwpx) as z:
        section = z.read("Contents/section0.xml")
    ids = _para_ids(section)
    # secPr paragraph stays at 0; others get unique 1..N. Order in document
    # is: first, dup, huge, secPr.
    assert ids == ["1", "2", "3", "0"]
    # No duplicates among non-secPr ids.
    non_zero = [i for i in ids if i != "0"]
    assert len(non_zero) == len(set(non_zero))


@pytest.mark.unit
def test_preserves_secpr_paragraph_id_zero(tmp_path: Path) -> None:
    hwpx = _zip_with_section(tmp_path, SECTION_DUPLICATE_IDS)
    id_normalizer.normalize_paragraph_ids(str(hwpx))

    with zipfile.ZipFile(hwpx) as z:
        section = z.read("Contents/section0.xml").decode("utf-8")
    # The paragraph that contains <hp:secPr/> must keep id="0".
    assert 'id="0"' in section
    assert "secPr" in section


@pytest.mark.unit
def test_normalizes_table_inner_paragraphs(tmp_path: Path) -> None:
    hwpx = _zip_with_section(tmp_path, SECTION_WITH_TABLE_PARAGRAPHS)
    id_normalizer.normalize_paragraph_ids(str(hwpx))

    with zipfile.ZipFile(hwpx) as z:
        section = z.read("Contents/section0.xml")
    ids = _para_ids(section)
    # 3 paragraphs total: top-level wrapper, cell paragraph, secPr.
    # secPr stays 0, the other two get unique non-zero ids.
    non_zero = [i for i in ids if i != "0"]
    assert len(non_zero) == 2
    assert len(set(non_zero)) == 2
    # cellAddr (a non-paragraph element with an "addr" attribute) is untouched.
    assert b'cellAddr colAddr="0" rowAddr="0"' in section


@pytest.mark.unit
def test_returns_count_of_actually_changed_ids(tmp_path: Path) -> None:
    hwpx = _zip_with_section(tmp_path, SECTION_DUPLICATE_IDS)
    count = id_normalizer.normalize_paragraph_ids(str(hwpx))
    # Section has 4 paragraphs whose original ids are 0,0,2147483648,0.
    # After renumber: 1,2,3,0. The secPr paragraph keeps id=0 unchanged,
    # so only the first three actually change.
    assert count == 3


@pytest.mark.unit
def test_already_normalized_section_does_not_rewrite_zip(
    tmp_path: Path,
) -> None:
    """Idempotent: re-running on a clean file must not touch the bytes."""
    hwpx = _zip_with_section(tmp_path, SECTION_DUPLICATE_IDS)
    id_normalizer.normalize_paragraph_ids(str(hwpx))
    snapshot = hwpx.read_bytes()

    count = id_normalizer.normalize_paragraph_ids(str(hwpx))
    assert count == 0
    assert hwpx.read_bytes() == snapshot


@pytest.mark.unit
def test_no_section_files_is_noop(tmp_path: Path) -> None:
    out = tmp_path / "empty.hwpx"
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr(
            zipfile.ZipInfo("mimetype"),
            T.MIMETYPE.encode("utf-8"),
            compress_type=zipfile.ZIP_STORED,
        )
    before = out.read_bytes()
    count = id_normalizer.normalize_paragraph_ids(str(out))
    assert count == 0
    # Zip is unchanged when there is nothing to renumber.
    assert out.read_bytes() == before


@pytest.mark.integration
def test_convert_invokes_normalizer(tmp_path: Path) -> None:
    """convert_hwp_to_hwpx must call the normalizer right after _run_jar."""
    fake_hwp = tmp_path / "in.hwp"
    fake_hwp.write_bytes(b"\x00")  # path needs to exist; jar is mocked
    fake_hwpx = tmp_path / "out.hwpx"

    def fake_run_jar(source: Path, target: Path, *, timeout: int) -> None:
        # Simulate hwp2hwpx producing a section with duplicate IDs.
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                zipfile.ZipInfo("mimetype"),
                T.MIMETYPE.encode("utf-8"),
                compress_type=zipfile.ZIP_STORED,
            )
            zf.writestr("Contents/section0.xml", SECTION_DUPLICATE_IDS)

    with mock.patch.object(conversion, "_run_jar", side_effect=fake_run_jar):
        conversion.convert_hwp_to_hwpx(
            str(fake_hwp), str(fake_hwpx), patch_fills=False
        )

    with zipfile.ZipFile(fake_hwpx) as z:
        section = z.read("Contents/section0.xml")
    ids = _para_ids(section)
    assert ids == ["1", "2", "3", "0"]


@pytest.mark.integration
def test_convert_runs_normalizer_before_fill_patch(tmp_path: Path) -> None:
    """Order matters: normalize_ids must precede patch_hwpx_from_hwp so the
    fill-patch step sees canonical IDs and never mutates an XML the
    normalizer is about to rewrite."""
    fake_hwp = tmp_path / "in.hwp"
    fake_hwp.write_bytes(b"\x00")
    fake_hwpx = tmp_path / "out.hwpx"

    call_order: list[str] = []

    def fake_run_jar(source: Path, target: Path, *, timeout: int) -> None:
        call_order.append("run_jar")
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                zipfile.ZipInfo("mimetype"),
                T.MIMETYPE.encode("utf-8"),
                compress_type=zipfile.ZIP_STORED,
            )
            zf.writestr("Contents/section0.xml", SECTION_DUPLICATE_IDS)

    def fake_normalize(path: str) -> int:
        call_order.append("normalize")
        return 0

    def fake_patch(hwp: str, hwpx: str):
        call_order.append("patch")

        class R:
            def as_dict(self):
                return {}

        return R()

    with mock.patch.object(conversion, "_run_jar", side_effect=fake_run_jar), \
         mock.patch.object(
             conversion.id_normalizer,
             "normalize_paragraph_ids",
             side_effect=fake_normalize,
         ), \
         mock.patch.object(
             conversion.hwp_patcher,
             "patch_hwpx_from_hwp",
             side_effect=fake_patch,
         ):
        conversion.convert_hwp_to_hwpx(str(fake_hwp), str(fake_hwpx))

    assert call_order == ["run_jar", "normalize", "patch"]


@pytest.mark.integration
def test_convert_skips_normalizer_when_disabled(tmp_path: Path) -> None:
    fake_hwp = tmp_path / "in.hwp"
    fake_hwp.write_bytes(b"\x00")
    fake_hwpx = tmp_path / "out.hwpx"

    def fake_run_jar(source: Path, target: Path, *, timeout: int) -> None:
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                zipfile.ZipInfo("mimetype"),
                T.MIMETYPE.encode("utf-8"),
                compress_type=zipfile.ZIP_STORED,
            )
            zf.writestr("Contents/section0.xml", SECTION_DUPLICATE_IDS)

    with mock.patch.object(conversion, "_run_jar", side_effect=fake_run_jar), \
         mock.patch.object(
             conversion.id_normalizer,
             "normalize_paragraph_ids",
         ) as mock_norm:
        conversion.convert_hwp_to_hwpx(
            str(fake_hwp),
            str(fake_hwpx),
            patch_fills=False,
            normalize_ids=False,
        )
        mock_norm.assert_not_called()
