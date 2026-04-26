"""Post-conversion patcher that enriches a hwp2hwpx HWPX with information
read directly from the original HWP binary.

The base converter (`hwp2hwpx.jar`) is faithful for the majority of the
DocInfo catalogue, but it can drop fill definitions (e.g. `<hc:fillBrush>`)
and some table attributes. This module runs a small Java CLI built on top of
`hwplib` (see `lib/java-src/HwpFillDump.java`) to pull the missing data from
the HWP OLE stream and patches it into the HWPX.

Supported patches so far:
  - borderFill color/gradient fills (writes `<hc:fillBrush>` when missing)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import xml_io
from .models import ns

LIB_DIR = Path(__file__).resolve().parent.parent.parent / "lib"
HWPLIB_JAR = LIB_DIR / "hwplib.jar"
FILL_DUMP_JAR = LIB_DIR / "hwpfilldump.jar"
TABLE_DUMP_JAR = LIB_DIR / "hwptabledump.jar"


@dataclass(frozen=True)
class PatchReport:
    fills_added: int = 0
    fills_replaced: int = 0
    cell_bf_fixed: int = 0
    zones_rewritten: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "fills_added": self.fills_added,
            "fills_replaced": self.fills_replaced,
            "cell_bf_fixed": self.cell_bf_fixed,
            "zones_rewritten": self.zones_rewritten,
        }


def dump_hwp_fills(hwp_path: str, *, timeout: int = 60) -> list[dict]:
    """Run the HwpFillDump Java CLI and parse its JSON output."""
    return _run_java_dumper("HwpFillDump", FILL_DUMP_JAR, hwp_path, timeout=timeout)


def dump_hwp_tables(hwp_path: str, *, timeout: int = 60) -> list[dict]:
    """Run the HwpTableDump CLI: per-table cells with authoritative borderFillId."""
    return _run_java_dumper("HwpTableDump", TABLE_DUMP_JAR, hwp_path, timeout=timeout)


def _run_java_dumper(main_class: str, jar: Path, hwp_path: str, *, timeout: int) -> list[dict]:
    if not HWPLIB_JAR.exists() or not jar.exists():
        raise FileNotFoundError(f"Required jars missing: {HWPLIB_JAR}, {jar}")
    if shutil.which("java") is None:
        raise RuntimeError("java runtime not found in PATH")

    classpath = f"{HWPLIB_JAR}:{jar}"
    result = subprocess.run(
        ["java", "-cp", classpath, main_class, hwp_path],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{main_class} failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return json.loads(result.stdout)


def patch_hwpx_from_hwp(hwp_path: str, hwpx_path: str) -> PatchReport:
    """Enrich the HWPX at `hwpx_path` with fill info extracted from `hwp_path`.

    Reads the HWPX header, replaces/adds `<hc:fillBrush>` on every borderFill
    the HWP defines as color-filled, re-zips the HWPX in place.
    """
    import zipfile
    from io import BytesIO

    fills = dump_hwp_fills(hwp_path)
    fills_by_id = {bf["id"]: bf for bf in fills}
    tables = dump_hwp_tables(hwp_path)
    # key: (table_id, row, col) -> authoritative borderFillId
    cell_bf_by_key = {
        (t["id"], c["row"], c["col"]): c["bf"]
        for t in tables
        for c in t["cells"]
    }

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        entries = {name: zf.read(name) for name in zf.namelist()}

    header_bytes = entries.get("Contents/header.xml")
    if header_bytes is None:
        raise RuntimeError("Contents/header.xml missing from HWPX")

    header_root = xml_io.parse(header_bytes)
    fill_added, fill_replaced = _patch_border_fills(header_root, fills_by_id)
    entries["Contents/header.xml"] = xml_io.serialize(header_root)

    # key: table_id -> list of zone dicts (from HWP, axis-swapped for HWPX)
    zones_by_tbl: dict[int, list[dict]] = {
        t["id"]: [_hwp_zone_to_hwpx(z) for z in t.get("zones", [])]
        for t in tables
    }

    cell_bf_fixed = 0
    zones_rewritten = 0
    for name in list(entries):
        if not (name.startswith("Contents/section") and name.endswith(".xml")):
            continue
        sec_root = xml_io.parse(entries[name])
        cell_bf_fixed += _patch_cell_border_fills(sec_root, cell_bf_by_key)
        zones_rewritten += _rewrite_cellzones(sec_root, zones_by_tbl)
        entries[name] = xml_io.serialize(sec_root)

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype first, uncompressed
        if "mimetype" in entries:
            zf.writestr(
                zipfile.ZipInfo("mimetype", date_time=(2026, 1, 1, 0, 0, 0)),
                entries["mimetype"],
                compress_type=zipfile.ZIP_STORED,
            )
        for name, data in entries.items():
            if name == "mimetype":
                continue
            zf.writestr(name, data)
    Path(hwpx_path).write_bytes(buf.getvalue())
    return PatchReport(
        fills_added=fill_added,
        fills_replaced=fill_replaced,
        cell_bf_fixed=cell_bf_fixed,
        zones_rewritten=zones_rewritten,
    )


def _patch_border_fills(header_root, fills_by_id: dict[int, dict]) -> tuple[int, int]:
    """Inject fillBrush only when the HWP fill is a *real* color. hwp2hwpx
    intentionally omits the fillBrush for plain white bf (they act as the
    "no background" marker); resurrecting those would paint white rectangles
    behind paragraphs and cover up genuine cellzone fills underneath."""
    added = 0
    replaced = 0
    for bf_el in header_root.iter(ns("hh", "borderFill")):
        try:
            bf_id = int(bf_el.get("id", "0"))
        except ValueError:
            continue
        info = fills_by_id.get(bf_id)
        if info is None or info["type"] == "none":
            continue
        if info["type"] == "color" and info.get("bgColor", "").upper() == "#FFFFFF":
            continue

        existing = bf_el.find(ns("hc", "fillBrush"))
        new_fill = _build_fill_brush(info)
        if new_fill is None:
            continue
        if existing is None:
            bf_el.append(new_fill)
            added += 1
        else:
            bf_el.remove(existing)
            bf_el.append(new_fill)
            replaced += 1
    return added, replaced


def _hwp_zone_to_hwpx(zone: dict) -> dict:
    """HWP binary stores cellzone ranges with row/column axes swapped compared to
    HWPX's `<hp:cellzone>`. Hancom's own converter emits HWPX with (row, col) in
    the outer sense, so we swap here once."""
    return {
        "startRowAddr": str(zone["startCol"]),
        "startColAddr": str(zone["startRow"]),
        "endRowAddr": str(zone["endCol"]),
        "endColAddr": str(zone["endRow"]),
        "borderFillIDRef": str(zone["bf"]),
    }


def _rewrite_cellzones(sec_root, zones_by_tbl: dict[int, list[dict]]) -> int:
    """Replace every table's <hp:cellzoneList> with HWP-authoritative data."""
    from lxml import etree as LET

    rewritten = 0
    for tbl_el in sec_root.iter(ns("hp", "tbl")):
        try:
            tbl_id = int(tbl_el.get("id", "0"))
        except ValueError:
            continue
        zones = zones_by_tbl.get(tbl_id)
        if zones is None:
            continue

        old = tbl_el.find(ns("hp", "cellzoneList"))
        if old is not None:
            tbl_el.remove(old)

        if not zones:
            rewritten += 1
            continue

        new_list = LET.Element(ns("hp", "cellzoneList"))
        for z in zones:
            el = LET.SubElement(new_list, ns("hp", "cellzone"))
            for attr, val in z.items():
                el.set(attr, val)

        # Must sit before the first <hp:tr> for the viewer to honour it
        first_tr = tbl_el.find(ns("hp", "tr"))
        if first_tr is not None:
            first_tr.addprevious(new_list)
        else:
            tbl_el.append(new_list)
        rewritten += 1
    return rewritten


def _patch_cell_border_fills(
    sec_root, cell_bf_by_key: dict[tuple[int, int, int], int]
) -> int:
    """Align every HWPX <hp:tc borderFillIDRef> with the value HWP reports.

    jar sometimes emits a plausible-looking but shifted borderFillID (esp. on
    merged / complex tables). This walks every <hp:tc> and, if the HWP-side
    dump disagrees, overwrites it.
    """
    fixed = 0
    for tbl_el in sec_root.iter(ns("hp", "tbl")):
        try:
            tbl_id = int(tbl_el.get("id", "0"))
        except ValueError:
            continue
        for tr_el in tbl_el.findall(ns("hp", "tr")):
            for tc_el in tr_el.findall(ns("hp", "tc")):
                addr = tc_el.find(ns("hp", "cellAddr"))
                if addr is None:
                    continue
                try:
                    row = int(addr.get("rowAddr", "0"))
                    col = int(addr.get("colAddr", "0"))
                except ValueError:
                    continue
                expected = cell_bf_by_key.get((tbl_id, row, col))
                if expected is None:
                    continue
                current = tc_el.get("borderFillIDRef")
                if current != str(expected):
                    tc_el.set("borderFillIDRef", str(expected))
                    fixed += 1
    return fixed


def _build_fill_brush(info: dict):
    """Build an <hc:fillBrush> element from the HWP-side fill info dict."""
    from lxml import etree as LET

    brush = LET.Element(ns("hc", "fillBrush"))
    if info["type"] == "color":
        win = LET.SubElement(brush, ns("hc", "winBrush"))
        win.set("faceColor", info.get("bgColor", "#FFFFFF"))
        win.set("hatchColor", info.get("patternColor", "#000000"))
        win.set("hatchStyle", info.get("patternType") or "NONE")
        win.set("alpha", "0")
        return brush
    if info["type"] == "gradient":
        grad = LET.SubElement(brush, ns("hc", "gradation"))
        grad.set("type", info.get("gradientType") or "LINEAR")
        grad.set("angle", str(info.get("angle", 0)))
        grad.set("centerX", str(info.get("centerX", 0)))
        grad.set("centerY", str(info.get("centerY", 0)))
        grad.set("step", str(info.get("blur", 50)))
        colors = info.get("colors") or []
        grad.set("colorNum", str(len(colors)))
        for c in colors:
            col_el = LET.SubElement(grad, ns("hc", "color"))
            col_el.text = c
        return brush
    return None
