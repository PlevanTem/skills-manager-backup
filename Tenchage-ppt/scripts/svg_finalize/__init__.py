"""svg_finalize package stub – provides embed_icons shim so svg_to_pptx works
without a full on-disk finalize step when no <use data-icon="..."> elements
are present in the source SVGs."""

from __future__ import annotations
from xml.etree import ElementTree as ET
from pathlib import Path


def embed_icons(svg_path: str | Path, icons_dir: str | Path | None = None) -> None:
    """No-op stub: expand <use data-icon="..."> elements in place.

    When SVGs contain no data-icon placeholders this function does nothing.
    A full implementation would look up each icon SVG under icons_dir and
    inline it; here we simply leave unknown placeholders in place so the
    conversion can continue without crashing.
    """
    pass
