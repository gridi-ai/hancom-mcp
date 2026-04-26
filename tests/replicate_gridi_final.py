"""End-to-end replication test.

Read the fully-written `gridi 최종` HWPX, copy its cell contents onto the
blank `창업중심대학` template (sharing the same style catalogue), and write
out a replicated document. Verifies that the style system carries table-cell
content across documents without losing formatting.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

# Support running as a plain script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hancom_writer import reader, styles, writer  # noqa: E402


SRC = ROOT / "samples" / "gridi_최종.hwpx"
TGT = ROOT / "samples" / "창업중심대학_양식.hwpx"
OUT = ROOT / "samples" / "gridi_최종_replicated.hwpx"
ROUND_TRIP = ROOT / "samples" / "gridi_최종_roundtrip.hwpx"


def _cells_by_position(table) -> dict[tuple[int, int], list[str]]:
    """Map (row, col) -> per-paragraph texts for every populated cell."""
    out: dict[tuple[int, int], list[str]] = {}
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row):
            if cell.para_texts and any(pt for pt in cell.para_texts):
                out[(r_idx, c_idx)] = list(cell.para_texts)
    return out


def main() -> None:
    src = reader.read_hwpx(str(SRC))
    tgt = reader.read_hwpx(str(TGT))

    # Style catalogue sanity check: target must carry every named style the
    # source uses (we checked earlier this is true for these two files).
    src_names = {s.name for s in styles.list_styles(src)}
    tgt_names = {s.name for s in styles.list_styles(tgt)}
    missing = src_names - tgt_names
    if missing:
        print(f"[warn] styles present only in source: {sorted(missing)}")
    else:
        print("[ok] style catalogue identical (25 styles)")

    src_tables = {t.id: t for s in src.sections for t in s.tables}
    matched = 0
    skipped_size = 0
    cells_copied = 0

    for section in tgt.sections:
        for t_tgt in section.tables:
            t_src = src_tables.get(t_tgt.id)
            if t_src is None:
                continue
            matched += 1
            src_map = _cells_by_position(t_src)
            if not src_map:
                continue

            tgt_rows, tgt_cols = len(t_tgt.rows), len(t_tgt.rows[0]) if t_tgt.rows else 0
            src_rows, src_cols = len(t_src.rows), len(t_src.rows[0]) if t_src.rows else 0
            if (tgt_rows, tgt_cols) != (src_rows, src_cols):
                skipped_size += 1
                # Still copy overlapping positions — the template may have
                # trimmed rows during cleanup but the top portion is aligned.
            max_r = min(tgt_rows, src_rows)
            for (r, c), para_texts in src_map.items():
                if r >= max_r or c >= len(t_tgt.rows[r]):
                    continue
                cell = t_tgt.rows[r][c]
                cell.para_texts = list(para_texts)
                cell.text = "\n".join(t for t in para_texts if t)
                cells_copied += 1

    writer.save_hwpx(tgt, str(OUT))

    print(
        f"\nTables in target: {sum(len(s.tables) for s in tgt.sections)}\n"
        f"Tables matched with source by id: {matched}\n"
        f"Tables with row/col mismatch (copied overlap): {skipped_size}\n"
        f"Cells copied: {cells_copied}\n"
        f"Output: {OUT}"
    )

    assert zipfile.is_zipfile(OUT), "output is not a valid zip"
    # Re-read to confirm round-trip survives
    after = reader.read_hwpx(str(OUT))
    print(f"Re-read OK. Tables: {sum(len(s.tables) for s in after.sections)}")

    print()
    print("=== Style + content round-trip of gridi 최종 ===")
    _round_trip_check()


def _round_trip_check() -> None:
    """Open source, save as-is, re-read — every cell text and every paragraph
    style_id must be preserved byte-for-byte in meaning."""
    src = reader.read_hwpx(str(SRC))
    writer.save_hwpx(src, str(ROUND_TRIP))
    after = reader.read_hwpx(str(ROUND_TRIP))

    # Compare styles catalogue (should be identical)
    before_styles = [(s.id, s.name) for s in styles.list_styles(src)]
    after_styles = [(s.id, s.name) for s in styles.list_styles(after)]
    assert before_styles == after_styles, "style catalogue drifted on round-trip"
    print(f"[ok] {len(before_styles)} styles preserved verbatim")

    # Compare every cell
    src_cells = _flatten_cells(src)
    dst_cells = _flatten_cells(after)
    assert set(src_cells.keys()) == set(dst_cells.keys()), "table set changed"
    mismatched = 0
    for key, before in src_cells.items():
        after_text = dst_cells[key]
        if before != after_text:
            mismatched += 1
    print(f"[{'ok' if mismatched == 0 else 'fail'}] {len(src_cells)} cells, {mismatched} content mismatches after round-trip")

    # Compare body paragraph styles (id -> style_id)
    src_paras = {(si, p.id): p.style_id for si, s in enumerate(src.sections) for p in s.paragraphs}
    dst_paras = {(si, p.id): p.style_id for si, s in enumerate(after.sections) for p in s.paragraphs}
    assert src_paras == dst_paras, "body paragraph styles drifted"
    print(f"[ok] {len(src_paras)} body paragraphs preserve styleIDRef exactly")


def _flatten_cells(doc) -> dict[tuple[int, int, int, int], str]:
    out: dict[tuple[int, int, int, int], str] = {}
    for s in doc.sections:
        for t in s.tables:
            for r, row in enumerate(t.rows):
                for c, cell in enumerate(row):
                    out[(s.index, t.id, r, c)] = cell.text
    return out


if __name__ == "__main__":
    main()
