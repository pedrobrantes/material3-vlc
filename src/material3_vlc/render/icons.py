"""Material 3 Icon Button, Expressive Play/Pause FAB, and M3 Switch renderers.

All buttons, FABs, and switches are pre-composited onto their exact opaque
Material 3 surface color (`surface_bg`, alpha=255) so VLC Skins2's Win32/X11
`drawGraphics()` (`BitBlt` + 1-bit `HRGN` mask) renders silky subpixel
anti-aliased edges with zero jaggedness or black fringes.
"""

from __future__ import annotations

from typing import Literal

from PIL import Image

from material3_vlc.render.svg import place_icon_svg, rasterize_svg, wrap_svg
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.tokens.color import blend_over
from material3_vlc.tokens.theme import DesignTokens

ButtonVariant = Literal["standard", "tonal", "filled", "outlined", "close", "muted", "record"]
ButtonState = Literal["up", "over", "down"]


def render_icon_button(
    tokens: DesignTokens,
    icon_name: str,
    size: int,
    icon_size: int,
    *,
    surface_bg: str,
    variant: ButtonVariant = "standard",
    state: ButtonState = "up",
    optical_dx: float = 0.0,
    optical_dy: float = 0.0,
) -> Image.Image:
    """Render a square Material 3 icon button pre-composited on opaque `surface_bg`."""
    c = tokens.colors
    sl = tokens.state_layers
    pad = max(1, round(2 * tokens.config.scale))
    btn_d = size - 2 * pad
    rx = btn_d / 2.0
    cx = size / 2.0
    cy = size / 2.0

    container_fill: str | None = None
    stroke_color: str | None = None
    stroke_w = max(1.0, 1.0 * tokens.config.scale)

    if variant == "standard":
        icon_color = c.on_surface_variant if state == "up" else c.on_surface
        if state == "over":
            container_fill = blend_over(surface_bg, c.on_surface, sl.hover)
        elif state == "down":
            container_fill = blend_over(surface_bg, c.on_surface, sl.pressed + 0.04)
    elif variant == "tonal":
        base = c.secondary_container
        icon_color = c.on_secondary_container
        if state == "up":
            container_fill = base
        elif state == "over":
            container_fill = blend_over(base, icon_color, sl.hover)
        else:
            container_fill = blend_over(base, icon_color, sl.pressed + 0.02)
    elif variant == "filled":
        base = c.primary
        icon_color = c.on_primary
        if state == "up":
            container_fill = base
        elif state == "over":
            container_fill = blend_over(base, icon_color, sl.hover)
        else:
            container_fill = blend_over(base, icon_color, sl.pressed + 0.02)
    elif variant == "outlined":
        icon_color = c.on_surface_variant if state == "up" else c.on_surface
        stroke_color = c.outline
        if state == "over":
            container_fill = blend_over(surface_bg, c.on_surface, sl.hover)
        elif state == "down":
            container_fill = blend_over(surface_bg, c.on_surface, sl.pressed + 0.02)
    elif variant == "close":
        # Follow the active Material 3 theme palette instead of hardcoded red
        if state == "up":
            icon_color = c.on_surface_variant
        elif state == "over":
            container_fill = c.secondary_container
            icon_color = c.on_secondary_container
        else:
            container_fill = c.primary
            icon_color = c.on_primary
    elif variant == "muted":
        base = c.error_container
        icon_color = c.on_error_container
        if state == "up":
            container_fill = base
        elif state == "over":
            container_fill = blend_over(base, icon_color, sl.hover)
        else:
            container_fill = blend_over(base, icon_color, sl.pressed + 0.02)
    elif variant == "record":
        base = c.error
        icon_color = c.on_error
        if state == "up":
            container_fill = base
        elif state == "over":
            container_fill = blend_over(base, icon_color, sl.hover)
        else:
            container_fill = blend_over(base, icon_color, sl.pressed + 0.02)

    parts: list[str] = [
        f'<rect x="0" y="0" width="{size}" height="{size}" fill="{surface_bg}"/>'
    ]
    if container_fill is not None:
        parts.append(
            f'<rect x="{pad}" y="{pad}" width="{btn_d}" height="{btn_d}" '
            f'rx="{rx:.2f}" ry="{rx:.2f}" fill="{container_fill}"/>'
        )
    if stroke_color is not None:
        inset = pad + stroke_w / 2.0
        sd = btn_d - stroke_w
        parts.append(
            f'<rect x="{inset:.2f}" y="{inset:.2f}" width="{sd:.2f}" height="{sd:.2f}" '
            f'rx="{sd / 2.0:.2f}" ry="{sd / 2.0:.2f}" fill="none" '
            f'stroke="{stroke_color}" stroke-width="{stroke_w:.2f}"/>'
        )

    parts.append(
        place_icon_svg(icon_name, cx + optical_dx, cy + optical_dy, icon_size, icon_color)
    )
    return rasterize_svg(wrap_svg(size, size, "".join(parts)))


def render_play_pause_fab(
    tokens: DesignTokens,
    width: int,
    height: int,
    icon_size: int,
    *,
    surface_bg: str,
    is_playing: bool,
    state: ButtonState = "up",
) -> Image.Image:
    """Render the Material 3 Expressive morphing Play/Pause Primary FAB on opaque `surface_bg`.

    - Paused (Play): Full pill (`rx = height / 2`) in `primary` + `onPrimary` play glyph.
    - Playing (Pause): Rounded squircle (`rx = shape.medium`) in `primary` + `onPrimary` pause glyph.
    """
    c = tokens.colors
    sl = tokens.state_layers
    pad = max(1, round(2 * tokens.config.scale))
    bw = width - 2 * pad
    bh = height - 2 * pad

    if is_playing:
        rx = min(bh / 2.0, float(tokens.shapes.medium))
        icon_name = "pause-fill"
        dx = 0.0
    else:
        rx = bh / 2.0
        icon_name = "play_arrow-fill"
        dx = 0.8 * tokens.config.scale

    if state == "down":
        rx = max(float(tokens.shapes.small), rx * 0.82)

    base = c.primary
    fg = c.on_primary
    if state == "up":
        fill = base
    elif state == "over":
        fill = blend_over(base, fg, sl.hover)
    else:
        fill = blend_over(base, fg, sl.pressed + 0.03)

    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="{pad}" y="{pad}" width="{bw}" height="{bh}" '
        f'rx="{rx:.2f}" ry="{rx:.2f}" fill="{fill}"/>'
        + place_icon_svg(icon_name, width / 2.0 + dx, height / 2.0, icon_size, fg)
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_m3_switch(
    tokens: DesignTokens,
    metrics: SkinMetrics,
    *,
    surface_bg: str,
    checked: bool,
    state: ButtonState = "up",
) -> Image.Image:
    """Render an authentic Material 3 Switch (52x32dp) pre-composited on opaque `surface_bg`."""
    c = tokens.colors
    sl = tokens.state_layers
    s = tokens.config.scale
    w, h = metrics.switch_w, metrics.switch_h
    pad = max(1, round(2 * s))
    tw = w - 2 * pad
    th = h - 2 * pad
    r_track = th / 2.0
    cy = h / 2.0

    parts: list[str] = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{surface_bg}"/>']
    if checked:
        track_fill = c.primary
        thumb_r = (11.5 if state != "down" else 12.5) * s
        thumb_cx = w - pad - th / 2.0
        thumb_fill = c.on_primary if state == "up" else c.primary_container
        icon_color = c.primary if state == "up" else c.on_primary_container
        halo_color = c.primary

        parts.append(
            f'<rect x="{pad}" y="{pad}" width="{tw}" height="{th}" '
            f'rx="{r_track:.2f}" ry="{r_track:.2f}" fill="{track_fill}"/>'
        )
        if state != "up":
            halo_op = sl.hover if state == "over" else sl.pressed + 0.04
            parts.append(
                f'<circle cx="{thumb_cx:.2f}" cy="{cy:.2f}" r="{min(h / 2.0, thumb_r + 3.0 * s):.2f}" '
                f'fill="{halo_color}" fill-opacity="{halo_op:.3f}"/>'
            )
        parts.append(
            f'<circle cx="{thumb_cx:.2f}" cy="{cy:.2f}" r="{thumb_r:.2f}" fill="{thumb_fill}"/>'
        )
        parts.append(place_icon_svg("check", thumb_cx, cy, 14.0 * s, icon_color))
    else:
        stroke_w = max(1.5, 2.0 * s)
        inset = pad + stroke_w / 2.0
        stw = tw - stroke_w
        sth = th - stroke_w
        thumb_r = (7.5 if state == "up" else (8.5 if state == "over" else 10.0)) * s
        thumb_cx = pad + th / 2.0
        thumb_fill = c.outline if state == "up" else c.on_surface_variant

        parts.append(
            f'<rect x="{inset:.2f}" y="{inset:.2f}" width="{stw:.2f}" height="{sth:.2f}" '
            f'rx="{sth / 2.0:.2f}" ry="{sth / 2.0:.2f}" '
            f'fill="{c.surface_container_highest}" stroke="{c.outline}" stroke-width="{stroke_w:.2f}"/>'
        )
        if state != "up":
            halo_op = sl.hover if state == "over" else sl.pressed + 0.04
            parts.append(
                f'<circle cx="{thumb_cx:.2f}" cy="{cy:.2f}" r="{min(h / 2.0, thumb_r + 4.0 * s):.2f}" '
                f'fill="{c.on_surface}" fill-opacity="{halo_op:.3f}"/>'
            )
        parts.append(
            f'<circle cx="{thumb_cx:.2f}" cy="{cy:.2f}" r="{thumb_r:.2f}" fill="{thumb_fill}"/>'
        )

    return rasterize_svg(wrap_svg(w, h, "".join(parts)))


def render_tree_glyph(
    tokens: DesignTokens,
    icon_name: str,
    width: int,
    height: int,
    icon_size: int,
    color: str,
) -> Image.Image:
    """Render a spacious Material 3 Playtree row glyph (`width x height`).

    VLC `CtrlTree::itemHeight()` uses `max(font_size, glyph.height) + LINE_INTERVAL`
    and aligns text near the lower portion of the row, so placing the icon at `cy = 0.62 * height`
    gives breathable ~30dp Material 3 list rows with optically centered icons!
    """
    _ = tokens
    cx = width * 0.50
    cy = height * 0.60
    body = place_icon_svg(icon_name, cx, cy, icon_size, color)
    return rasterize_svg(wrap_svg(width, height, body))
