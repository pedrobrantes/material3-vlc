"""Pixel-accurate visual preview compositor for Material 3 VLC skins.

Reads the ACTUAL generated `theme.xml` and PNG assets produced by `build_skin()`
and composites realistic rendered previews of every window & layout:
- Main Player (`main_normal`) — with cinema video frame OR album art showcase
- Main Player + Docked Playlist Side Sheet (`main_playlist`) — with realistic track queue
- Compact Mini-Player (`main_compact`)
- Equalizer Window (`eqwin`) — with realistic musical EQ curve
- Fullscreen Controller HUD (`fullscreenController`) — over cinema backdrop
- Combined Showcase Sheet — presenting all layouts side-by-side for documentation & PR review!
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from material3_vlc.render.svg import find_assets_dir, rasterize_svg, wrap_svg
from material3_vlc.tokens.color import blend_over
from material3_vlc.tokens.theme import DesignTokens


def _sample_backdrop_svg(width: int, height: int, tokens: DesignTokens) -> str:
    """Create a tasteful stylized cinema backdrop for video-stage previews."""
    c = tokens.colors
    c1 = blend_over(c.surface_container_lowest, c.primary_container, 0.45)
    c2 = blend_over(c.surface_container_lowest, c.tertiary_container, 0.35)
    c3 = c.surface_container_lowest
    return wrap_svg(
        width,
        height,
        "<defs>"
        '<radialGradient id="g1" cx="28%" cy="32%" r="65%">'
        f'<stop offset="0%" stop-color="{c1}"/>'
        f'<stop offset="55%" stop-color="{c2}" stop-opacity="0.65"/>'
        f'<stop offset="100%" stop-color="{c3}"/>'
        "</radialGradient>"
        '<linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{c3}" stop-opacity="0.1"/>'
        f'<stop offset="100%" stop-color="{c3}" stop-opacity="0.72"/>'
        "</linearGradient>"
        "</defs>"
        f'<rect width="{width}" height="{height}" fill="{c3}"/>'
        f'<rect width="{width}" height="{height}" fill="url(#g1)"/>'
        # Abstract cinema horizon waves
        f'<path d="M0 {height * 0.72:.1f} Q {width * 0.3:.1f} {height * 0.56:.1f}, '
        f'{width * 0.62:.1f} {height * 0.70:.1f} T {width} {height * 0.64:.1f} '
        f'L {width} {height} L 0 {height} Z" fill="{c.primary}" fill-opacity="0.16"/>'
        f'<path d="M0 {height * 0.82:.1f} Q {width * 0.42:.1f} {height * 0.68:.1f}, '
        f'{width * 0.76:.1f} {height * 0.80:.1f} T {width} {height * 0.76:.1f} '
        f'L {width} {height} L 0 {height} Z" fill="{c.secondary}" fill-opacity="0.14"/>'
        f'<rect width="{width}" height="{height}" fill="url(#g2)"/>',
    )


class SkinPreviewRenderer:
    """Interprets a built skin directory (`theme.xml` + PNGs) to render live layout mockups."""

    def __init__(self, skin_dir: Path, tokens: DesignTokens) -> None:
        self.skin_dir = skin_dir
        self.tokens = tokens
        parser = etree.XMLParser(load_dtd=False, no_network=True, remove_comments=True)
        self.root = etree.parse(str(skin_dir / "theme.xml"), parser).getroot()
        self.bitmaps: dict[str, Image.Image] = {}
        self.fonts: dict[str, tuple[Path, int]] = {}
        self._load_resources()

    def _load_resources(self) -> None:
        for font_el in self.root.findall("Font"):
            fid = font_el.get("id", "")
            ffile = self.skin_dir / font_el.get("file", "")
            fsize = int(font_el.get("size", "12"))
            self.fonts[fid] = (ffile, fsize)

        for bmp_el in self.root.findall("Bitmap"):
            bid = bmp_el.get("id", "")
            img_path = self.skin_dir / bmp_el.get("file", "")
            with Image.open(img_path) as raw:
                full = raw.convert("RGBA")
            self.bitmaps[bid] = full
            for sub_el in bmp_el.findall("SubBitmap"):
                sid = sub_el.get("id", "")
                sx = int(sub_el.get("x", "0"))
                sy = int(sub_el.get("y", "0"))
                sw = int(sub_el.get("width", "0"))
                sh = int(sub_el.get("height", "0"))
                self.bitmaps[sid] = full.crop((sx, sy, sx + sw, sy + sh))

    def _get_font(self, font_id: str) -> ImageFont.FreeTypeFont:
        if font_id in self.fonts:
            path, size = self.fonts[font_id]
            return ImageFont.truetype(str(path), size=size)
        fallback = find_assets_dir() / "fonts" / "Roboto-Regular.ttf"
        return ImageFont.truetype(str(fallback), size=13)

    def _eval_visible(self, expr: str | None, state: dict[str, bool]) -> bool:
        if not expr or expr == "true":
            return True
        if expr == "false":
            return False
        # Safe boolean expression evaluation for Skins2 preview state (preserving foo.isMaximized())
        raw = expr
        for key, val in state.items():
            if "()" in key:
                raw = raw.replace(key, "True" if val else "False")
        tokens_list = raw.replace("(", " ( ").replace(")", " ) ").split()
        mapped: list[str] = []
        for tok in tokens_list:
            if tok in ("and", "or", "not", "(", ")", "True", "False"):
                mapped.append(tok)
            elif tok == "true":
                mapped.append("True")
            elif tok == "false":
                mapped.append("False")
            else:
                mapped.append("True" if state.get(tok, False) else "False")
        try:
            return bool(eval(" ".join(mapped), {"__builtins__": {}}, {}))
        except Exception:
            return True

    def _subst_text(self, raw: str, text_vars: dict[str, str]) -> str:
        out = raw
        for k, v in text_vars.items():
            out = out.replace(k, v)
        return out

    def render_layout(
        self,
        layout_id: str,
        *,
        state: dict[str, bool] | None = None,
        slider_values: dict[str, float] | None = None,
        text_vars: dict[str, str] | None = None,
    ) -> Image.Image:
        """Composite a named `<Layout>` from `theme.xml` into an RGBA `PIL.Image`."""
        layout_el = self.root.find(f".//Layout[@id='{layout_id}']")
        if layout_el is None:
            raise KeyError(f"Layout '{layout_id}' not found in theme.xml")

        st: dict[str, bool] = {
            "vlc.isPlaying": True,
            "vlc.isPaused": False,
            "vlc.isStopped": False,
            "vlc.hasVout": False,
            "vlc.hasAudio": True,
            "vlc.isMute": False,
            "vlc.isOnTop": False,
            "vlc.isRecording": False,
            "dvd.isActive": False,
            "playlist.isRandom": False,
            "playlist.isLoop": True,
            "playlist.isRepeat": False,
            "equalizer.isEnabled": True,
            "eqwin.isVisible": False,
            "toolswin.isVisible": False,
            "main.isMaximized()": False,
        }
        if state:
            st.update(state)

        svals: dict[str, float] = {
            "time": 0.42,
            "volume": 0.72,
            "equalizer.preamp": 0.58,
            "equalizer.band(0)": 0.68,
            "equalizer.band(1)": 0.64,
            "equalizer.band(2)": 0.55,
            "equalizer.band(3)": 0.48,
            "equalizer.band(4)": 0.50,
            "equalizer.band(5)": 0.56,
            "equalizer.band(6)": 0.65,
            "equalizer.band(7)": 0.72,
            "equalizer.band(8)": 0.66,
            "equalizer.band(9)": 0.60,
        }
        if slider_values:
            svals.update(slider_values)

        tvars: dict[str, str] = {
            "$N": "Interstellar (2014) — Hans Zimmer · Cornfield Chase",
            "$t": "01:47",
            "$d": "04:16",
            "$T": "00:01:47",
            "$D": "00:04:16",
            "$V": "72",
            "$R": "1.00x",
            "$B": "320",
            "$S": "48000",
        }
        if text_vars:
            tvars.update(text_vars)

        lw = int(layout_el.get("width", "0"))
        lh = int(layout_el.get("height", "0"))
        canvas = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        def render_children(parent: etree._Element, ox: int, oy: int) -> None:
            for el in parent:
                if not self._eval_visible(el.get("visible"), st):
                    continue
                tag = el.tag
                ex = ox + int(el.get("x", "0"))
                ey = oy + int(el.get("y", "0"))

                if tag in ("Panel", "Group"):
                    render_children(el, ex, ey)
                elif tag == "Image":
                    bmp_id = el.get("image", "")
                    if bmp_id not in self.bitmaps:
                        continue
                    img = self.bitmaps[bmp_id]
                    w_attr = int(el.get("width", "-1"))
                    h_attr = int(el.get("height", "-1"))
                    if w_attr > 0 and h_attr > 0 and (w_attr != img.width or h_attr != img.height):
                        img = img.resize((w_attr, h_attr), Image.Resampling.BILINEAR)
                    canvas.alpha_composite(img, (ex, ey))
                elif tag == "Video":
                    vw = int(el.get("width", "0"))
                    vh = int(el.get("height", "0"))
                    if vw > 0 and vh > 0:
                        backdrop = rasterize_svg(_sample_backdrop_svg(vw, vh, self.tokens))
                        canvas.alpha_composite(backdrop, (ex, ey))
                elif tag == "Button":
                    bmp_id = el.get("up", "")
                    if bmp_id in self.bitmaps:
                        canvas.alpha_composite(self.bitmaps[bmp_id], (ex, ey))
                elif tag == "Checkbox":
                    checked = self._eval_visible(el.get("state"), st)
                    bmp_id = el.get("up2" if checked else "up1", "")
                    if bmp_id in self.bitmaps:
                        canvas.alpha_composite(self.bitmaps[bmp_id], (ex, ey))
                elif tag == "Slider":
                    val_key = el.get("value", "none")
                    ratio = svals.get(val_key, 0.35)
                    bg_el = el.find("SliderBackground")
                    if bg_el is not None:
                        bg_bmp_id = bg_el.get("image", "")
                        if bg_bmp_id in self.bitmaps:
                            strip = self.bitmaps[bg_bmp_id]
                            nbh = int(bg_el.get("nbhoriz", "1"))
                            nbv = int(bg_el.get("nbvert", "1"))
                            total = nbh * nbv
                            idx = max(0, min(total - 1, int(ratio * (total - 1))))
                            fw = strip.width // nbh
                            fh = strip.height // nbv
                            fx = fw * (idx % nbh)
                            fy = fh * (idx // nbh)
                            frame = strip.crop((fx, fy, fx + fw, fy + fh))
                            canvas.alpha_composite(frame, (ex, ey))
                    up_id = el.get("up", "")
                    pts_str = el.get("points", "(0,0),(10,0)")
                    pts = [
                        tuple(int(n) for n in seg.strip("() ").split(","))
                        for seg in pts_str.split("),(")
                    ]
                    if len(pts) >= 2 and up_id in self.bitmaps:
                        (x0, y0), (x1, y1) = pts[0], pts[-1]
                        cx = round(ex + x0 + (x1 - x0) * ratio)
                        cy = round(ey + y0 + (y1 - y0) * ratio)
                        handle = self.bitmaps[up_id]
                        canvas.alpha_composite(handle, (cx - handle.width // 2, cy - handle.height // 2))
                elif tag == "Text":
                    text_str = self._subst_text(el.get("text", ""), tvars)
                    font = self._get_font(el.get("font", ""))
                    color = el.get("color", self.tokens.colors.on_surface)
                    tw = int(el.get("width", "0"))
                    align = el.get("alignment", "left")
                    bbox = draw.textbbox((0, 0), text_str, font=font)
                    measured_w = round(bbox[2] - bbox[0])
                    # Clip / truncate neatly if wider than text box
                    if tw > 0 and measured_w > tw:
                        while len(text_str) > 3 and draw.textbbox((0, 0), text_str + "…", font=font)[2] > tw:
                            text_str = text_str[:-1]
                        text_str += "…"
                        measured_w = round(draw.textbbox((0, 0), text_str, font=font)[2])
                    tx = ex
                    if tw > 0:
                        if align == "center":
                            tx = ex + max(0, (tw - measured_w) // 2)
                        elif align == "right":
                            tx = ex + max(0, tw - measured_w)
                    draw.text((tx, ey), text_str, font=font, fill=color)
                elif tag == "Playtree":
                    pw = int(el.get("width", "0"))
                    ph = int(el.get("height", "0"))
                    bg1 = el.get("bgcolor1", self.tokens.colors.surface_container_low)
                    bg2 = el.get("bgcolor2", bg1)
                    fg = el.get("fgcolor", self.tokens.colors.on_surface)
                    sel = el.get("selcolor", self.tokens.colors.secondary_container)
                    play_c = el.get("playcolor", self.tokens.colors.primary)
                    font = self._get_font(el.get("font", ""))
                    draw.rectangle([ex, ey, ex + pw, ey + ph], fill=bg1)

                    sample_tracks = [
                        ("01. Dreaming of the Crash", False, False),
                        ("02. Cornfield Chase", True, True),
                        ("03. Dust", False, False),
                        ("04. Day One", False, False),
                        ("05. Stay", False, False),
                        ("06. Message from Home", False, False),
                        ("07. The Wormhole", False, False),
                        ("08. Mountains", False, False),
                        ("09. Detach", False, False),
                        ("10. No Time for Caution", False, False),
                        ("11. S.T.A.Y.", False, False),
                        ("12. Where We're Going", False, False),
                    ]
                    s = self.tokens.config.scale
                    item_icon = self.bitmaps.get(el.get("itemimage", ""))
                    row_h = max(
                        round(28 * s),
                        (item_icon.height + round(2 * s)) if item_icon is not None else 0,
                    )
                    sel_r = round(8 * s)
                    row_gap = max(1, round(1 * s))
                    for idx, (label, is_sel, is_play) in enumerate(sample_tracks):
                        ry = ey + idx * row_h
                        if ry + row_h > ey + ph:
                            break
                        if is_sel:
                            draw.rounded_rectangle(
                                [ex, ry + row_gap, ex + pw, ry + row_h - row_gap],
                                radius=sel_r,
                                fill=sel,
                            )
                        elif idx % 2 == 1 and bg2 != bg1:
                            draw.rounded_rectangle(
                                [ex, ry + row_gap, ex + pw, ry + row_h - row_gap],
                                radius=round(6 * s),
                                fill=bg2,
                            )
                        tx = ex + round(4 * s)
                        if item_icon is not None:
                            canvas.alpha_composite(
                                item_icon, (tx, ry + (row_h - item_icon.height) // 2)
                            )
                            tx += item_icon.width + round(4 * s)
                        bbox = draw.textbbox((0, 0), label, font=font)
                        th = bbox[3] - bbox[1]
                        draw.text(
                            (tx, ry + max(0, (row_h - th) // 2) - bbox[1]),
                            label,
                            font=font,
                            fill=play_c if is_play else fg,
                        )
                    # Render nested Playtree scrollbar centered on its rail
                    sb = el.find("Slider")
                    if sb is not None:
                        sb_up = self.bitmaps.get(sb.get("up", ""))
                        if sb_up is not None:
                            sx = ox + int(sb.get("x", "0")) - sb_up.width // 2
                            sy = oy + int(sb.get("y", "0")) + round(16 * s)
                            canvas.alpha_composite(sb_up, (sx, sy))

        render_children(layout_el, 0, 0)
        return canvas


def render_skin_previews(skin_dir: Path, tokens: DesignTokens, out_dir: Path) -> dict[str, Path]:
    """Generate a full suite of PNG previews for every layout in `skin_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = SkinPreviewRenderer(skin_dir, tokens)
    outputs: dict[str, Path] = {}

    # 1. Main Player (Video cinema state)
    main_video = renderer.render_layout("main_normal", state={"vlc.hasVout": True, "vlc.isPlaying": True})
    p_main = out_dir / f"{tokens.config.slug}-main.png"
    main_video.save(p_main, optimize=True)
    outputs["main"] = p_main

    # 2. Main Player + Playlist Side Sheet (Audio / Album Art showcase state)
    main_pl = renderer.render_layout("main_playlist", state={"vlc.hasVout": False, "vlc.isPlaying": True})
    p_pl = out_dir / f"{tokens.config.slug}-playlist.png"
    main_pl.save(p_pl, optimize=True)
    outputs["playlist"] = p_pl

    # 3. Compact Mini-Player
    compact = renderer.render_layout("main_compact", state={"vlc.isPlaying": False})
    p_compact = out_dir / f"{tokens.config.slug}-compact.png"
    compact.save(p_compact, optimize=True)
    outputs["compact"] = p_compact

    # 4. Equalizer Window
    eq = renderer.render_layout("eq_main", state={"equalizer.isEnabled": True})
    p_eq = out_dir / f"{tokens.config.slug}-equalizer.png"
    eq.save(p_eq, optimize=True)
    outputs["equalizer"] = p_eq

    # 4b. Control Center / Quick Tools Window
    tools = renderer.render_layout("tools_main")
    p_tools = out_dir / f"{tokens.config.slug}-tools.png"
    tools.save(p_tools, optimize=True)
    outputs["tools"] = p_tools

    # 5. Fullscreen HUD over cinema backdrop
    fs_hud = renderer.render_layout("fs_hud", state={"vlc.isPlaying": True})
    fs_w = fs_hud.width + round(96 * tokens.config.scale)
    fs_h = fs_hud.height + round(140 * tokens.config.scale)
    fs_scene = rasterize_svg(_sample_backdrop_svg(fs_w, fs_h, tokens))
    fs_scene.alpha_composite(
        fs_hud, ((fs_w - fs_hud.width) // 2, fs_h - fs_hud.height - round(24 * tokens.config.scale))
    )
    p_fs = out_dir / f"{tokens.config.slug}-fullscreen.png"
    fs_scene.save(p_fs, optimize=True)
    outputs["fullscreen"] = p_fs

    # 6. About Dialog
    about = renderer.render_layout("about_main")
    p_about = out_dir / f"{tokens.config.slug}-about.png"
    about.save(p_about, optimize=True)
    outputs["about"] = p_about

    # 7. Composite Showcase Sheet (Playlist + Main on top; Compact + Equalizer + Control Center below!)
    pad = round(28 * tokens.config.scale)
    row2_gap = round(24 * tokens.config.scale)
    row2_total_w = compact.width + row2_gap + eq.width + row2_gap + tools.width
    sheet_w = max(main_pl.width, row2_total_w) + 2 * pad
    bottom_row_h = max(compact.height, eq.height, tools.height)
    sheet_h = pad + main_pl.height + pad + bottom_row_h + pad
    bg_color = blend_over(tokens.colors.surface, tokens.colors.primary_container, 0.08)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), bg_color)
    sheet.alpha_composite(main_pl, ((sheet_w - main_pl.width) // 2, pad))

    row2_y = pad + main_pl.height + pad
    row2_x = (sheet_w - row2_total_w) // 2
    sheet.alpha_composite(compact, (row2_x, row2_y + (bottom_row_h - compact.height) // 2))
    sheet.alpha_composite(
        eq, (row2_x + compact.width + row2_gap, row2_y + (bottom_row_h - eq.height) // 2)
    )
    sheet.alpha_composite(
        tools,
        (
            row2_x + compact.width + row2_gap + eq.width + row2_gap,
            row2_y + (bottom_row_h - tools.height) // 2,
        ),
    )

    p_sheet = out_dir / f"{tokens.config.slug}-showcase.png"
    sheet.save(p_sheet, optimize=True)
    outputs["showcase"] = p_sheet

    return outputs
