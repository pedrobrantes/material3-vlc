"""SVG asset loading, Material Symbols path injection, and resvg rasterization."""

from __future__ import annotations

import io
import re
from functools import lru_cache
from pathlib import Path

import resvg_py
from PIL import Image

_PATH_RE = re.compile(r"<path\b[^>]*>", re.IGNORECASE)
_FILL_ATTR_RE = re.compile(r'\bfill="[^"]*"')


def find_assets_dir() -> Path:
    """Locate the repository/package `assets/` directory."""
    # Check relative to this module (works in editable / source tree layouts)
    candidates = [
        Path(__file__).resolve().parents[1] / "assets",
        Path(__file__).resolve().parents[3] / "assets",
        Path(__file__).resolve().parents[2] / "assets",
        Path.cwd() / "assets",
    ]
    for candidate in candidates:
        if (candidate / "icons").is_dir() and (candidate / "fonts").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate material3-vlc assets/ directory containing icons/ and fonts/."
    )


def get_font_files() -> list[str]:
    """Return paths to bundled Apache-2.0 Roboto TTF files for SVG text rendering."""
    fonts_dir = find_assets_dir() / "fonts"
    return [
        str(fonts_dir / "Roboto-Regular.ttf"),
        str(fonts_dir / "Roboto-Medium.ttf"),
    ]


@lru_cache(maxsize=128)
def load_icon_inner_svg(icon_name: str) -> str:
    """Load the raw `<path .../>` geometry from a bundled Material Symbols Rounded SVG."""
    icon_path = find_assets_dir() / "icons" / f"{icon_name}.svg"
    if not icon_path.is_file():
        raise FileNotFoundError(f"Bundled Material Symbol SVG not found: {icon_path}")
    raw = icon_path.read_text(encoding="utf-8")
    paths = _PATH_RE.findall(raw)
    if not paths:
        raise ValueError(f"No <path> elements found in SVG icon: {icon_path}")
    # Strip any hardcoded fill attributes so callers control icon color cleanly
    cleaned = [_FILL_ATTR_RE.sub("", p) for p in paths]
    return "".join(cleaned)


def place_icon_svg(
    icon_name: str,
    cx: float,
    cy: float,
    size: float,
    color: str,
    opacity: float = 1.0,
) -> str:
    """Return an SVG `<g>` fragment placing a Material Symbol centered at `(cx, cy)`.

    Material Symbols SVGs use `viewBox="0 -960 960 960"`.
    """
    inner = load_icon_inner_svg(icon_name)
    scale = size / 960.0
    x = cx - size / 2.0
    y = cy - size / 2.0
    op_attr = "" if opacity >= 0.999 else f' fill-opacity="{opacity:.3f}"'
    return (
        f'<g transform="translate({x:.3f} {y:.3f}) scale({scale:.6f}) translate(0 960)" '
        f'fill="{color}"{op_attr}>{inner}</g>'
    )


def wrap_svg(width: int, height: int, body: str) -> str:
    """Wrap SVG elements in a standard well-formed `<svg>` root."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f"{body}</svg>"
    )


def rasterize_svg(
    svg: str,
    *,
    width: int | None = None,
    height: int | None = None,
    use_fonts: bool = False,
) -> Image.Image:
    """Render an SVG string into an RGBA `PIL.Image` using `resvg_py`."""
    png_bytes = resvg_py.svg_to_bytes(
        svg_string=svg,
        width=width,
        height=height,
        skip_system_fonts=True,
        font_files=get_font_files() if use_fonts else None,
    )
    with Image.open(io.BytesIO(png_bytes)) as img:
        return img.convert("RGBA")
