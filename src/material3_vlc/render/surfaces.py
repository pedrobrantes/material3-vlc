"""Material 3 window chrome, cards, album art placeholders, equalizer, HUD, and about surfaces.

All surfaces and cards are 100% opaque (`alpha = 255`) and pre-composited against their
exact parent Material 3 container color so Win32 (`BitBlt` + 1-bit `HRGN`) and X11 (`XShape`)
render razor-sharp anti-aliased artwork with zero jagged edges or black fringes.
"""

from __future__ import annotations

from html import escape

from PIL import Image

from material3_vlc.render.svg import place_icon_svg, rasterize_svg, wrap_svg
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.tokens.color import blend_over
from material3_vlc.tokens.theme import DesignTokens

EQ_BAND_LABELS: tuple[str, ...] = (
    "Pre",
    "60",
    "170",
    "310",
    "600",
    "1K",
    "3K",
    "6K",
    "12K",
    "14K",
    "16K",
)


def render_solid_rect(width: int, height: int, fill: str) -> Image.Image:
    """Render a crisp opaque solid color rectangle."""
    return rasterize_svg(
        wrap_svg(width, height, f'<rect x="0" y="0" width="{width}" height="{height}" fill="{fill}"/>')
    )


def render_topbar_bg(tokens: DesignTokens, width: int, height: int) -> Image.Image:
    """Render the Material 3 Top App Bar (`surfaceContainerLow`) with top border & bottom hairline."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{c.surface_container_low}"/>'
        f'<rect x="0" y="0" width="{width}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.divider_subtle}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_controls_bg(tokens: DesignTokens, width: int, height: int) -> Image.Image:
    """Render the elevated Material 3 Bottom Control Bar (`surfaceContainer`)."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{c.surface_container}"/>'
        f'<rect x="0" y="0" width="{width}" height="{b}" fill="{c.divider_subtle}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_playlist_sheet_bg(tokens: DesignTokens, metrics: SkinMetrics) -> Image.Image:
    """Render the Material 3 Playlist Side Sheet with a symmetric rounded card and scrollbar rail."""
    c = tokens.colors
    s = tokens.config.scale
    w = metrics.playlist_w
    h = metrics.main_h
    hh = metrics.playlist_header_h
    tbh = metrics.playlist_toolbar_h
    b = metrics.border

    card_x = metrics.px(10)
    card_y = hh + metrics.px(10)
    card_w = w - metrics.px(20)
    card_h = h - hh - tbh - metrics.px(20)
    card_r = float(tokens.shapes.large)

    # Center scrollbar rail cleanly inside the right padding of the inset card
    rail_w = max(4, round(4 * s))
    rail_cx = w - metrics.px(20)
    rail_x = rail_cx - rail_w / 2.0
    rail_y = card_y + metrics.px(8)
    rail_h = max(metrics.px(20), card_h - metrics.px(16))
    rail_color = blend_over(c.surface_container_low, c.surface_container_highest, 0.55)

    body = (
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{c.surface_container_low}"/>'
        # Inset rounded Material 3 card framing the Playtree + scrollbar rail symmetrically
        f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" '
        f'rx="{card_r:.2f}" ry="{card_r:.2f}" fill="{c.surface_container_low}" '
        f'stroke="{c.divider_subtle}" stroke-width="{b}"/>'
        f'<rect x="{rail_x:.2f}" y="{rail_y}" width="{rail_w}" height="{rail_h}" '
        f'rx="{rail_w / 2.0:.2f}" ry="{rail_w / 2.0:.2f}" fill="{rail_color}"/>'
    )
    return rasterize_svg(wrap_svg(w, h, body))


def render_playlist_toolbar_bg(tokens: DesignTokens, width: int, height: int) -> Image.Image:
    """Render the docked Playlist Side Sheet bottom action toolbar."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{c.surface_container}"/>'
        f'<rect x="0" y="0" width="{width}" height="{b}" fill="{c.divider_subtle}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_compact_bg(tokens: DesignTokens, width: int, height: int) -> Image.Image:
    """Render the Compact Mini-Player (`surfaceContainer`) framed surface."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{c.surface_container}"/>'
        f'<rect x="0" y="0" width="{width}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="0" width="{b}" height="{height}" fill="{c.window_border}"/>'
        f'<rect x="{width - b}" y="0" width="{b}" height="{height}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_album_art_placeholder(
    tokens: DesignTokens,
    size: int,
    *,
    surface_bg: str,
    compact: bool = False,
) -> Image.Image:
    """Render a sleek Material 3 tonal Album Art placeholder card pre-composited on `surface_bg`."""
    c = tokens.colors
    s = tokens.config.scale
    rx = float(tokens.shapes.large if compact else tokens.shapes.extra_large)
    pad = max(1, round(2 * s))
    cw = size - 2 * pad
    cx = size / 2.0
    cy = size / 2.0

    grad_top = blend_over(c.surface_container_high, c.primary_container, 0.22)
    grad_bot = c.surface_container_high
    badge_r = cw * (0.28 if compact else 0.24)
    icon_sz = cw * (0.34 if compact else 0.30)
    stroke_w = max(1.0, 1.0 * s)

    body = (
        "<defs>"
        '<linearGradient id="artGrad" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{grad_top}"/>'
        f'<stop offset="100%" stop-color="{grad_bot}"/>'
        "</linearGradient>"
        "</defs>"
        f'<rect x="0" y="0" width="{size}" height="{size}" fill="{surface_bg}"/>'
        f'<rect x="{pad}" y="{pad}" width="{cw}" height="{cw}" '
        f'rx="{rx:.2f}" ry="{rx:.2f}" fill="url(#artGrad)" '
        f'stroke="{c.outline_variant}" stroke-width="{stroke_w:.2f}"/>'
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{badge_r:.2f}" fill="{c.primary_container}"/>'
        + place_icon_svg("music_note", cx, cy, icon_sz, c.on_primary_container)
    )
    return rasterize_svg(wrap_svg(size, size, body))


def render_fullscreen_hud_bg(tokens: DesignTokens, width: int, height: int) -> Image.Image:
    """Render the elevated floating Fullscreen Controller HUD (`surfaceContainerHigh`)."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    accent_h = max(2, round(2 * tokens.config.scale))
    top_tint = blend_over(c.surface_container_high, c.primary, 0.14)

    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{c.surface_container_high}"/>'
        f'<rect x="{b}" y="{b}" width="{width - 2 * b}" height="{accent_h}" fill="{top_tint}"/>'
        f'<rect x="0" y="0" width="{width}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="0" width="{b}" height="{height}" fill="{c.window_border}"/>'
        f'<rect x="{width - b}" y="0" width="{b}" height="{height}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_equalizer_bg(tokens: DesignTokens, metrics: SkinMetrics) -> Image.Image:
    """Render the complete Material 3 Equalizer window surface with scale & frequency labels."""
    c = tokens.colors
    s = tokens.config.scale
    w, h = metrics.eq_w, metrics.eq_h
    hh = metrics.eq_header_h
    b = metrics.border

    slider_top = hh + metrics.px(24)
    slider_h = metrics.eq_slider_h
    mid_y = slider_top + slider_h / 2.0
    top_y = slider_top + metrics.px(6)
    bot_y = slider_top + slider_h - metrics.px(6)

    preamp_x = metrics.px(52)
    band0_x = metrics.px(108)
    band_step = metrics.px(36)
    col_centers = [preamp_x] + [band0_x + i * band_step for i in range(10)]
    label_y = slider_top + slider_h + metrics.px(18)

    grid_left = metrics.px(40)
    grid_right = w - metrics.px(16)
    font_title = round(14 * s)
    font_sub = round(10 * s)

    parts: list[str] = [
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{c.surface_container}"/>',
        f'<rect x="0" y="0" width="{w}" height="{hh}" fill="{c.surface_container_low}"/>',
        f'<rect x="0" y="{hh - b}" width="{w}" height="{b}" fill="{c.divider_subtle}"/>',
        f'<rect x="0" y="0" width="{w}" height="{b}" fill="{c.window_border}"/>',
        f'<rect x="0" y="{h - b}" width="{w}" height="{b}" fill="{c.window_border}"/>',
        f'<rect x="0" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>',
        f'<rect x="{w - b}" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>',
        place_icon_svg("equalizer", metrics.px(24), hh / 2.0, metrics.icon_md, c.primary),
        f'<text x="{metrics.px(42)}" y="{hh / 2.0 + font_title * 0.35:.1f}" '
        f'font-family="Roboto" font-weight="500" font-size="{font_title}" '
        f'fill="{c.on_surface}">Equalizer</text>',
        f'<line x1="{metrics.px(80)}" y1="{slider_top}" x2="{metrics.px(80)}" '
        f'y2="{slider_top + slider_h}" stroke="{c.divider_subtle}" stroke-width="{b}"/>',
        f'<line x1="{grid_left}" y1="{mid_y:.1f}" x2="{grid_right}" y2="{mid_y:.1f}" '
        f'stroke="{c.outline_variant}" stroke-width="{b}" stroke-dasharray="{metrics.px(3)},{metrics.px(3)}"/>',
        f'<line x1="{grid_left}" y1="{top_y:.1f}" x2="{grid_right}" y2="{top_y:.1f}" '
        f'stroke="{c.divider_subtle}" stroke-width="{b}"/>',
        f'<line x1="{grid_left}" y1="{bot_y:.1f}" x2="{grid_right}" y2="{bot_y:.1f}" '
        f'stroke="{c.divider_subtle}" stroke-width="{b}"/>',
        f'<text x="{metrics.px(34)}" y="{top_y + font_sub * 0.35:.1f}" text-anchor="end" '
        f'font-family="Roboto" font-weight="500" font-size="{font_sub}" fill="{c.on_surface_variant}">+20</text>',
        f'<text x="{metrics.px(34)}" y="{mid_y + font_sub * 0.35:.1f}" text-anchor="end" '
        f'font-family="Roboto" font-weight="500" font-size="{font_sub}" fill="{c.on_surface_variant}">0 dB</text>',
        f'<text x="{metrics.px(34)}" y="{bot_y + font_sub * 0.35:.1f}" text-anchor="end" '
        f'font-family="Roboto" font-weight="500" font-size="{font_sub}" fill="{c.on_surface_variant}">-20</text>',
    ]

    for cx, label in zip(col_centers, EQ_BAND_LABELS, strict=True):
        parts.append(
            f'<text x="{cx}" y="{label_y}" text-anchor="middle" '
            f'font-family="Roboto" font-weight="500" font-size="{font_sub}" '
            f'fill="{c.on_surface_variant}">{label}</text>'
        )

    return rasterize_svg(wrap_svg(w, h, "".join(parts)), use_fonts=True)


def render_tools_card(tokens: DesignTokens, metrics: SkinMetrics) -> Image.Image:
    """Render the Material 3 Control Center (`toolswin`) surface with 3 elevated section cards."""
    c = tokens.colors
    s = tokens.config.scale
    w, h = metrics.tools_w, metrics.tools_h
    hh = metrics.tools_header_h
    fh = metrics.tools_footer_h
    b = metrics.border

    f_title = round(14 * s)
    f_section = round(11 * s)
    card_x = metrics.px(14)
    card_w = w - 2 * card_x
    card_h = metrics.px(68)
    card_gap = metrics.px(10)
    card_r = float(tokens.shapes.medium)

    y1 = hh + metrics.px(12)
    y2 = y1 + card_h + card_gap
    y3 = y2 + card_h + card_gap
    footer_y = h - fh

    sections = [
        (y1, "PLAYBACK & CAPTURE"),
        (y2, "MEDIA, TRACKS & STREAMS"),
        (y3, "APPEARANCE, TOOLS & VLC"),
    ]

    parts: list[str] = [
        # Main card & Top App Bar + Footer strip
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{c.surface_container}"/>',
        f'<rect x="0" y="0" width="{w}" height="{hh}" fill="{c.surface_container_low}"/>',
        f'<rect x="0" y="{hh - b}" width="{w}" height="{b}" fill="{c.divider_subtle}"/>',
        f'<rect x="0" y="{footer_y}" width="{w}" height="{fh}" fill="{c.surface_container_low}"/>',
        f'<rect x="0" y="{footer_y}" width="{w}" height="{b}" fill="{c.divider_subtle}"/>',
        # Outer border
        f'<rect x="0" y="0" width="{w}" height="{b}" fill="{c.window_border}"/>',
        f'<rect x="0" y="{h - b}" width="{w}" height="{b}" fill="{c.window_border}"/>',
        f'<rect x="0" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>',
        f'<rect x="{w - b}" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>',
        # Header icon & title
        place_icon_svg("tune", metrics.px(24), hh / 2.0, metrics.icon_md, c.primary),
        f'<text x="{metrics.px(42)}" y="{hh / 2.0 + f_title * 0.35:.1f}" '
        f'font-family="Roboto" font-weight="500" font-size="{f_title}" '
        f'fill="{c.on_surface}">Control Center</text>',
    ]

    for cy, title in sections:
        parts.append(
            f'<rect x="{card_x}" y="{cy}" width="{card_w}" height="{card_h}" '
            f'rx="{card_r:.2f}" ry="{card_r:.2f}" fill="{c.surface_container_high}" '
            f'stroke="{c.divider_subtle}" stroke-width="{b}"/>'
        )
        parts.append(
            f'<text x="{card_x + metrics.px(12)}" y="{cy + metrics.px(18)}" '
            f'font-family="Roboto" font-weight="500" font-size="{f_section}" '
            f'letter-spacing="{0.6 * s:.2f}" fill="{c.on_surface_variant}">{escape(title)}</text>'
        )

    return rasterize_svg(wrap_svg(w, h, "".join(parts)), use_fonts=True)


def render_about_card(tokens: DesignTokens, metrics: SkinMetrics) -> Image.Image:
    """Render the Material 3 About Dialog card displaying active theme tokens."""
    c = tokens.colors
    cfg = tokens.config
    s = cfg.scale
    w, h = metrics.about_w, metrics.about_h
    b = metrics.border

    f_title = round(16 * s)
    f_body = round(12 * s)
    f_small = round(11 * s)

    swatches = [
        ("Primary", c.primary),
        ("Secondary", c.secondary),
        ("Tertiary", c.tertiary),
        ("Container", c.primary_container),
        ("Surface", c.surface_container_highest),
    ]
    sw_y = metrics.px(124)
    sw_w = metrics.px(56)
    sw_h = metrics.px(22)
    sw_gap = metrics.px(10)
    sw_start = metrics.px(24)

    swatch_svg: list[str] = []
    for idx, (_lbl, hex_c) in enumerate(swatches):
        sx = sw_start + idx * (sw_w + sw_gap)
        swatch_svg.append(
            f'<rect x="{sx}" y="{sw_y}" width="{sw_w}" height="{sw_h}" '
            f'rx="{metrics.px(6)}" ry="{metrics.px(6)}" fill="{hex_c}" '
            f'stroke="{c.outline_variant}" stroke-width="{b}"/>'
        )

    meta_line = f"{cfg.mode.upper()}  •  {cfg.scheme}  •  Seed {cfg.seed.upper()}  •  {cfg.scale:g}x"
    body = (
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{c.surface_container_high}"/>'
        f'<rect x="0" y="0" width="{w}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="{h - b}" width="{w}" height="{b}" fill="{c.window_border}"/>'
        f'<rect x="0" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>'
        f'<rect x="{w - b}" y="0" width="{b}" height="{h}" fill="{c.window_border}"/>'
        f'<rect x="{metrics.px(24)}" y="{metrics.px(24)}" width="{metrics.px(44)}" height="{metrics.px(44)}" '
        f'rx="{tokens.shapes.medium}" ry="{tokens.shapes.medium}" fill="{c.primary_container}"/>'
        + place_icon_svg(
            "graphic_eq", metrics.px(46), metrics.px(46), metrics.icon_lg, c.on_primary_container
        )
        + f'<text x="{metrics.px(80)}" y="{metrics.px(43)}" font-family="Roboto" font-weight="500" '
        f'font-size="{f_title}" fill="{c.on_surface}">{escape(cfg.name)}</text>'
        f'<text x="{metrics.px(80)}" y="{metrics.px(62)}" font-family="Roboto" font-weight="400" '
        f'font-size="{f_small}" fill="{c.on_surface_variant}">Material 3 Design Engine for VLC</text>'
        f'<line x1="{metrics.px(24)}" y1="{metrics.px(84)}" x2="{w - metrics.px(24)}" y2="{metrics.px(84)}" '
        f'stroke="{c.divider_subtle}" stroke-width="{b}"/>'
        f'<text x="{metrics.px(24)}" y="{metrics.px(108)}" font-family="Roboto" font-weight="500" '
        f'font-size="{f_body}" fill="{c.on_surface}">{escape(meta_line)}</text>'
        + "".join(swatch_svg)
        + f'<text x="{metrics.px(24)}" y="{metrics.px(176)}" font-family="Roboto" font-weight="400" '
        f'font-size="{f_small}" fill="{c.on_surface_variant}">github.com/PedroBrantes/material3-vlc</text>'
        f'<text x="{metrics.px(24)}" y="{metrics.px(196)}" font-family="Roboto" font-weight="400" '
        f'font-size="{f_small}" fill="{c.outline}">MIT License  •  Double-click anywhere to close</text>'
    )
    return rasterize_svg(wrap_svg(w, h, body), use_fonts=True)


def render_resize_grip(tokens: DesignTokens, size: int) -> Image.Image:
    """Render an opaque Material 3 resize corner indicator baked onto `surface_container`."""
    c = tokens.colors
    s = tokens.config.scale
    b = max(1, round(s))
    r = max(1.0, 1.15 * s)
    dot_color = blend_over(c.surface_container, c.outline, 0.72)
    pts = [
        (size - 3.5 * s, size - 3.5 * s),
        (size - 7.0 * s, size - 3.5 * s),
        (size - 3.5 * s, size - 7.0 * s),
        (size - 10.5 * s, size - 3.5 * s),
        (size - 7.0 * s, size - 7.0 * s),
        (size - 3.5 * s, size - 10.5 * s),
    ]
    parts = [
        f'<rect x="0" y="0" width="{size}" height="{size}" fill="{c.surface_container}"/>',
        f'<rect x="0" y="{size - b}" width="{size}" height="{b}" fill="{c.window_border}"/>',
        f'<rect x="{size - b}" y="0" width="{b}" height="{size}" fill="{c.window_border}"/>',
        *(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{dot_color}"/>' for x, y in pts),
    ]
    return rasterize_svg(wrap_svg(size, size, "".join(parts)))


def render_resize_strip_e(tokens: DesignTokens, width: int, height: int, surface_bg: str) -> Image.Image:
    """Render an opaque East edge resize strip matching `surface_bg` + 1px outer `window_border`."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="{width - b}" y="0" width="{b}" height="{height}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))


def render_resize_strip_s(tokens: DesignTokens, width: int, height: int, surface_bg: str) -> Image.Image:
    """Render an opaque South edge resize strip matching `surface_bg` + 1px bottom `window_border`."""
    c = tokens.colors
    b = max(1, round(tokens.config.scale))
    body = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{surface_bg}"/>'
        f'<rect x="0" y="{height - b}" width="{width}" height="{b}" fill="{c.window_border}"/>'
    )
    return rasterize_svg(wrap_svg(width, height, body))
