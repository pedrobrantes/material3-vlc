"""Authentic Material 3 Expressive slider track & handle renderers.

All slider tracks and handles are pre-composited onto their exact opaque Material 3
surface color (`surface_bg`, alpha=255) so VLC Skins2's Win32/X11 `BitBlt` rendering
has zero 1-bit jagged fringes while cleanly carving the signature Material 3 gap
around the handle at every playback position!
"""

from __future__ import annotations

from typing import Literal

from PIL import Image

from material3_vlc.render.svg import rasterize_svg, wrap_svg
from material3_vlc.tokens.color import blend_over
from material3_vlc.tokens.theme import DesignTokens

SliderState = Literal["up", "over", "down"]


def render_horizontal_slider_strip(
    tokens: DesignTokens,
    width: int,
    height: int,
    track_height: int,
    frames: int,
    *,
    surface_bg: str,
    show_stop_indicator: bool = True,
) -> Image.Image:
    """Render an opaque vertical sprite strip (`width x (height * frames)`) for `<SliderBackground>`."""
    c = tokens.colors
    s = tokens.config.scale
    ty = (height - track_height) / 2.0
    r = track_height / 2.0

    inactive_color = (
        c.surface_container_highest if tokens.config.mode != "light" else c.secondary_container
    )

    inactive_parts = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>',
        f'<rect x="0" y="{ty:.2f}" width="{width}" height="{track_height}" '
        f'rx="{r:.2f}" ry="{r:.2f}" fill="{inactive_color}"/>',
    ]
    if show_stop_indicator:
        dot_r = max(1.5, min(r * 0.62, 2.0 * s))
        dot_cx = width - r
        dot_cy = height / 2.0
        inactive_parts.append(
            f'<circle cx="{dot_cx:.2f}" cy="{dot_cy:.2f}" r="{dot_r:.2f}" fill="{c.primary}"/>'
        )
    inactive_img = rasterize_svg(wrap_svg(width, height, "".join(inactive_parts)))

    active_svg = wrap_svg(
        width,
        height,
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="0" y="{ty:.2f}" width="{width}" height="{track_height}" '
        f'rx="{r:.2f}" ry="{r:.2f}" fill="{c.primary}"/>',
    )
    active_img = rasterize_svg(active_svg)

    strip = Image.new("RGBA", (width, height * frames), (0, 0, 0, 255))
    for idx in range(frames):
        ratio = idx / (frames - 1) if frames > 1 else 1.0
        split_x = round(width * ratio)
        frame = inactive_img.copy()
        if split_x > 0:
            crop = active_img.crop((0, 0, min(width, split_x), height))
            frame.paste(crop, (0, 0))
        strip.paste(frame, (0, idx * height))

    return strip


def render_horizontal_slider_handle(
    tokens: DesignTokens,
    width: int,
    height: int,
    track_height: int,
    *,
    surface_bg: str,
    state: SliderState = "up",
) -> Image.Image:
    """Render an opaque Material 3 Expressive vertical-pill slider handle.

    Filling the full `width x height` handle bitmap with `surface_bg` simultaneously:
    1. Carves out the authentic Material 3 4dp gap around the vertical pill handle
    2. Eliminates 100% of Win32 1-bit `HRGN` jagged edges on the handle & hover halo!
    """
    c = tokens.colors
    sl = tokens.state_layers
    s = tokens.config.scale
    cx = width / 2.0
    cy = height / 2.0
    _ = track_height  # kept in signature for caller clarity

    if state == "up":
        pill_w = max(3.0, 4.0 * s)
        pill_h = min(float(height - 2), 18.0 * s)
    elif state == "over":
        pill_w = max(3.5, 4.5 * s)
        pill_h = min(float(height - 2), 20.0 * s)
    else:
        pill_w = max(2.2, 2.6 * s)
        pill_h = min(float(height), 22.0 * s)

    parts: list[str] = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
    ]

    if state != "up":
        halo_op = sl.hover + 0.06 if state == "over" else sl.dragged + 0.04
        halo_color = blend_over(surface_bg, c.primary, halo_op)
        halo_w = min(float(width), pill_w + 6.0 * s)
        halo_h = min(float(height), pill_h + 2.0 * s)
        parts.append(
            f'<rect x="{cx - halo_w / 2.0:.2f}" y="{cy - halo_h / 2.0:.2f}" '
            f'width="{halo_w:.2f}" height="{halo_h:.2f}" '
            f'rx="{halo_w / 2.0:.2f}" ry="{halo_w / 2.0:.2f}" fill="{halo_color}"/>'
        )

    parts.append(
        f'<rect x="{cx - pill_w / 2.0:.2f}" y="{cy - pill_h / 2.0:.2f}" '
        f'width="{pill_w:.2f}" height="{pill_h:.2f}" '
        f'rx="{pill_w / 2.0:.2f}" ry="{pill_w / 2.0:.2f}" fill="{c.primary}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, "".join(parts)))


def render_eq_slider_strip(
    tokens: DesignTokens,
    width: int,
    height: int,
    frames: int = 41,
    *,
    surface_bg: str,
) -> Image.Image:
    """Render an opaque horizontal sprite strip (`(width * frames) x height`) for vertical EQ sliders."""
    c = tokens.colors
    s = tokens.config.scale
    track_w = max(4, round(6 * s))
    pad_y = max(4, round(6 * s))
    tx = (width - track_w) / 2.0
    r = track_w / 2.0
    track_len = height - 2 * pad_y
    mid_y = height / 2.0
    b = max(1, round(s))
    inactive_color = (
        c.surface_container_highest if tokens.config.mode != "light" else c.secondary_container
    )

    base_svg = wrap_svg(
        width,
        height,
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        # Preserve horizontal +20 / 0 dB / -20 grid guides seamlessly behind each band!
        f'<line x1="0" y1="{pad_y}" x2="{width}" y2="{pad_y}" stroke="{c.divider_subtle}" stroke-width="{b}"/>'
        f'<line x1="0" y1="{height - pad_y}" x2="{width}" y2="{height - pad_y}" stroke="{c.divider_subtle}" stroke-width="{b}"/>'
        f'<line x1="0" y1="{mid_y:.1f}" x2="{width}" y2="{mid_y:.1f}" '
        f'stroke="{c.outline_variant}" stroke-width="{b}" stroke-dasharray="{max(2, round(3 * s))},{max(2, round(3 * s))}"/>'
        f'<rect x="{tx:.2f}" y="{pad_y}" width="{track_w}" height="{track_len}" '
        f'rx="{r:.2f}" ry="{r:.2f}" fill="{inactive_color}"/>'
        f'<circle cx="{width / 2.0:.2f}" cy="{mid_y:.2f}" r="{max(1.5, 2.0 * s):.2f}" '
        f'fill="{c.outline}"/>',
    )
    base_img = rasterize_svg(base_svg)

    active_svg = wrap_svg(
        width,
        height,
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="{tx:.2f}" y="{pad_y}" width="{track_w}" height="{track_len}" '
        f'rx="{r:.2f}" ry="{r:.2f}" fill="{c.primary}"/>',
    )
    active_img = rasterize_svg(active_svg)

    strip = Image.new("RGBA", (width * frames, height), (0, 0, 0, 255))
    for idx in range(frames):
        ratio = idx / (frames - 1) if frames > 1 else 0.5
        pos_y = round((height - pad_y) - ratio * track_len)
        y1 = min(round(mid_y), pos_y)
        y2 = max(round(mid_y), pos_y)
        frame = base_img.copy()
        if y2 > y1:
            # Only overwrite the central track column so horizontal grid lines remain intact
            x0 = max(0, int(tx))
            x1 = min(width, int(tx + track_w + 1))
            crop = active_img.crop((x0, max(0, y1), x1, min(height, y2)))
            frame.paste(crop, (x0, max(0, y1)))
        strip.paste(frame, (idx * width, 0))

    return strip


def render_eq_slider_handle(
    tokens: DesignTokens,
    width: int,
    height: int,
    *,
    surface_bg: str,
    state: SliderState = "up",
) -> Image.Image:
    """Render an opaque horizontal M3 pill handle for vertical Equalizer bands."""
    c = tokens.colors
    sl = tokens.state_layers
    s = tokens.config.scale
    cx = width / 2.0
    cy = height / 2.0

    pill_w = min(float(width - 2), (16.0 if state == "up" else 18.0) * s)
    pill_h = max(3.0, (4.0 if state != "down" else 3.0) * s)

    parts: list[str] = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
    ]
    if state != "up":
        halo_op = sl.hover + 0.06 if state == "over" else sl.dragged + 0.04
        halo_color = blend_over(surface_bg, c.primary, halo_op)
        hw = min(float(width), pill_w + 4.0 * s)
        hh = min(float(height), pill_h + 4.0 * s)
        parts.append(
            f'<rect x="{cx - hw / 2.0:.2f}" y="{cy - hh / 2.0:.2f}" '
            f'width="{hw:.2f}" height="{hh:.2f}" '
            f'rx="{hh / 2.0:.2f}" ry="{hh / 2.0:.2f}" fill="{halo_color}"/>'
        )
    parts.append(
        f'<rect x="{cx - pill_w / 2.0:.2f}" y="{cy - pill_h / 2.0:.2f}" '
        f'width="{pill_w:.2f}" height="{pill_h:.2f}" '
        f'rx="{pill_h / 2.0:.2f}" ry="{pill_h / 2.0:.2f}" fill="{c.primary}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, "".join(parts)))


def render_scrollbar_thumb(
    tokens: DesignTokens,
    width: int,
    height: int,
    *,
    surface_bg: str,
    state: SliderState = "up",
) -> Image.Image:
    """Render an opaque slim Material 3 pill scrollbar thumb for the Playlist tree."""
    c = tokens.colors
    s = tokens.config.scale
    bar_w = max(3.0, (4.0 if state == "up" else 6.0) * s)
    x = (width - bar_w) / 2.0
    if state == "up":
        fill = blend_over(surface_bg, c.outline, 0.65)
    elif state == "over":
        fill = blend_over(surface_bg, c.on_surface_variant, 0.85)
    else:
        fill = c.primary
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="{x:.2f}" y="1" width="{bar_w:.2f}" height="{height - 2}" '
        f'rx="{bar_w / 2.0:.2f}" ry="{bar_w / 2.0:.2f}" fill="{fill}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))
