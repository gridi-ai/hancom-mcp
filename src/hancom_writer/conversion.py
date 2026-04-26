"""HWP (binary) to HWPX conversion via hwp2hwpx Java library."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import cleanup, hwp_patcher, id_normalizer
from .reader import read_hwpx
from .writer import save_hwpx

JAR_PATH = Path(__file__).resolve().parent.parent.parent / "lib" / "hwp2hwpx.jar"
DEFAULT_TIMEOUT_SEC = 120


@dataclass(frozen=True)
class ConversionResult:
    input_path: str
    output_path: str
    cleanup: cleanup.CleanupReport | None
    patch: hwp_patcher.PatchReport | None = None

    def as_dict(self) -> dict:
        data: dict = {
            "status": "converted",
            "input": self.input_path,
            "output": self.output_path,
        }
        if self.cleanup is not None:
            data["cleanup"] = self.cleanup.as_dict()
        if self.patch is not None:
            data["patch"] = self.patch.as_dict()
        return data


def convert_hwp_to_hwpx(
    hwp_path: str,
    hwpx_path: str | None = None,
    *,
    strip_instructions: bool = False,
    normalize_colors: bool = False,
    remove_dotted_borders: bool = False,
    patch_fills: bool = True,
    normalize_ids: bool = True,
    timeout: int = DEFAULT_TIMEOUT_SEC,
) -> ConversionResult:
    """Convert a .hwp file to .hwpx, optionally applying cleanup post-processing.

    The `strip_instructions`, `normalize_colors`, and `remove_dotted_borders`
    flags request post-conversion cleanups to improve readability when the
    source template contains instruction text, colored helpers, or dotted
    placeholder boxes.

    `patch_fills` (default True) runs the HwpFillDump CLI against the original
    HWP and injects any missing `<hc:fillBrush>` into HWPX borderFills.
    Cleanup ordering: jar convert -> fill patch -> text cleanups (so strips
    happen on the fully-styled document).
    """
    source = Path(hwp_path)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {hwp_path}")
    if source.suffix.lower() not in (".hwp",):
        raise ValueError(f"Not an HWP file: {hwp_path}")

    target = Path(hwpx_path) if hwpx_path else source.with_suffix(".hwpx")
    target.parent.mkdir(parents=True, exist_ok=True)

    _run_jar(source, target, timeout=timeout)

    # B-13: hwp2hwpx leaves duplicate paragraph IDs (id="0" repeated, plus
    # out-of-range values like 2^31). Hancom Viewer rejects these as corrupted,
    # so we renumber per-section before any other post-processing inspects the
    # XML.
    if normalize_ids:
        id_normalizer.normalize_paragraph_ids(str(target))

    patch_report: hwp_patcher.PatchReport | None = None
    if patch_fills:
        patch_report = hwp_patcher.patch_hwpx_from_hwp(str(source), str(target))

    any_cleanup = strip_instructions or normalize_colors or remove_dotted_borders
    report: cleanup.CleanupReport | None = None
    if any_cleanup:
        doc = read_hwpx(str(target))
        report = cleanup.apply_cleanup(
            doc,
            strip_instructions=strip_instructions,
            normalize_colors=normalize_colors,
            remove_dotted_borders=remove_dotted_borders,
        )
        save_hwpx(doc, str(target))

    return ConversionResult(
        input_path=str(source),
        output_path=str(target.resolve()),
        cleanup=report,
        patch=patch_report,
    )


def _run_jar(source: Path, target: Path, *, timeout: int) -> None:
    if not JAR_PATH.exists():
        raise FileNotFoundError(f"hwp2hwpx.jar not found at {JAR_PATH}")
    if shutil.which("java") is None:
        raise RuntimeError("java runtime not found in PATH")

    result = subprocess.run(
        ["java", "-jar", str(JAR_PATH), str(source), str(target)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"hwp2hwpx conversion failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    if not target.exists():
        raise RuntimeError(f"Conversion reported success but {target} was not produced")
