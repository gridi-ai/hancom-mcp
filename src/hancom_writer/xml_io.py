"""Hancom-compatible XML parsing and serialization.

Uses lxml so that:
  - xmlns declarations on the root are preserved (Hancom Viewer rejects files
    that dropped declared prefixes such as `hp10`, `hhs`, `hm`, `ooxmlchart`,
    `hwpunitchar`, `epub`, `config`, even if the section body doesn't use them).
  - The XML declaration matches Hancom's exact form:
        <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    Any deviation (single quotes, lowercase utf-8, missing standalone) gets the
    file flagged as corrupted by Hancom Viewer.
"""

from __future__ import annotations

from typing import Any

from lxml import etree as LET

XML_DECL = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'


def parse(xml_bytes: bytes) -> Any:
    """Parse bytes into an lxml element. Keeps all namespace declarations."""
    return LET.fromstring(xml_bytes)


def serialize(root: Any) -> bytes:
    """Serialize an lxml element with the Hancom-style XML declaration."""
    body = LET.tostring(root, encoding="UTF-8", xml_declaration=False)
    return XML_DECL + body


def ns_tag(prefix: str, tag: str, nsmap: dict[str, str]) -> str:
    """Return a Clark-notation tag using a given nsmap (for lxml queries)."""
    return f"{{{nsmap[prefix]}}}{tag}"
