"""Hancom Office Viewer integration via AppleScript (macOS)."""

from __future__ import annotations

import subprocess

VIEWER_APP = "Hancom Office HWP Viewer"
_RELOAD_SCRIPT = """
tell application "System Events"
    set viewerRunning to (name of every process) contains "{app}"
end tell

if viewerRunning then
    tell application "System Events"
        tell process "{app}"
            set winPos to position of window 1
            set winSize to size of window 1
        end tell
    end tell

    tell application "{app}" to quit
    delay 0.5

    do shell script "open -a '{app}' " & quoted form of "{path}"
    delay 1.0

    tell application "System Events"
        tell process "{app}"
            set position of window 1 to winPos
            set size of window 1 to winSize
        end tell
    end tell

    return "reloaded"
else
    return "not_running"
end if
"""


def reload_viewer(file_path: str, timeout: int = 15) -> bool:
    """Restart the Hancom Viewer on the given file, preserving window geometry.

    Returns True only if the viewer was already running and was reloaded.
    Returns False if the viewer wasn't running or the AppleScript failed.
    """
    script = _RELOAD_SCRIPT.format(app=VIEWER_APP, path=file_path)
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
    return "reloaded" in result.stdout
