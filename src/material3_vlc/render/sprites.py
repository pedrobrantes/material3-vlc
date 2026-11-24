"""Sprite sheet packer & complete surface-matched opaque asset renderer.

Every interactive sprite (`ui_controls.png`), slider strip, and window surface is
pre-composited onto its exact opaque Material 3 surface container color (`alpha = 255`)
so VLC Skins2's Win32/X11 `BitBlt` rendering produces crisp anti-aliased graphics
with zero serrilhado or dark fringes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from material3_vlc.render.icons import (
    ButtonState,
    ButtonVariant,
    render_icon_button,
    render_m3_switch,
    render_play_pause_fab,
    render_tree_glyph,
)
from material3_vlc.render.sliders import (
    render_eq_slider_handle,
    render_eq_slider_strip,
    render_horizontal_slider_handle,
    render_horizontal_slider_strip,
    render_scrollbar_thumb,
)
from material3_vlc.render.surfaces import (
    render_about_card,
    render_album_art_placeholder,
    render_compact_bg,
    render_controls_bg,
    render_equalizer_bg,
    render_fullscreen_hud_bg,
    render_playlist_sheet_bg,
    render_playlist_toolbar_bg,
    render_resize_grip,
    render_resize_strip_e,
    render_resize_strip_s,
    render_solid_rect,
    render_tools_card,
    render_topbar_bg,
)
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.tokens.theme import DesignTokens

STATES: tuple[ButtonState, ...] = ("up", "over", "down")


@dataclass(frozen=True, slots=True)
class SubBitmapSpec:
    """A sliced rectangular region within a packed sprite sheet."""

    id: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class BitmapSpec:
    """A PNG `<Bitmap>` entry in `theme.xml`, with optional `<SubBitmap>` slices."""

    id: str
    file: str
    subbitmaps: tuple[SubBitmapSpec, ...] = ()


class SpriteSheetBuilder:
    """Deterministic shelf packer for grouping icons and buttons into compact PNG atlases."""

    def __init__(self, max_width: int = 1024, padding: int = 2) -> None:
        self._max_width = max_width
        self._padding = padding
        self._items: list[tuple[str, Image.Image]] = []

    def add(self, sub_id: str, image: Image.Image) -> None:
        self._items.append((sub_id, image))

    def pack(self) -> tuple[Image.Image, tuple[SubBitmapSpec, ...]]:
        if not self._items:
            raise ValueError("Cannot pack an empty sprite sheet.")

        x = 0
        y = 0
        row_h = 0
        sheet_w = 0
        placements: list[tuple[str, Image.Image, int, int]] = []

        for sub_id, img in self._items:
            w, h = img.size
            if x > 0 and x + w > self._max_width:
                x = 0
                y += row_h + self._padding
                row_h = 0
            placements.append((sub_id, img, x, y))
            x += w + self._padding
            sheet_w = max(sheet_w, x - self._padding)
            row_h = max(row_h, h)

        sheet_h = y + row_h
        canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
        subs: list[SubBitmapSpec] = []
        for sub_id, img, px, py in placements:
            canvas.paste(img, (px, py))
            subs.append(SubBitmapSpec(id=sub_id, x=px, y=py, width=img.width, height=img.height))
        return canvas, tuple(subs)


def render_all_skin_assets(
    tokens: DesignTokens,
    metrics: SkinMetrics,
    assets_out_dir: Path,
) -> list[BitmapSpec]:
    """Render every sprite sheet, slider strip, and surface PNG into `assets_out_dir`."""
    assets_out_dir.mkdir(parents=True, exist_ok=True)
    bitmaps: list[BitmapSpec] = []
    c = tokens.colors

    bg_low = c.surface_container_low
    bg_mid = c.surface_container
    bg_high = c.surface_container_high

    def save_png(
        bitmap_id: str,
        filename: str,
        img: Image.Image,
        subs: tuple[SubBitmapSpec, ...] = (),
    ) -> None:
        rel = f"images/{filename}"
        out_path = assets_out_dir / filename
        img.save(out_path, format="PNG", optimize=True)
        bitmaps.append(BitmapSpec(id=bitmap_id, file=rel, subbitmaps=subs))

    # ------------------------------------------------------------------
    # 1. Surface-Matched Opaque Controls Atlas (`ui_controls.png`)
    # ------------------------------------------------------------------
    btn_sheet = SpriteSheetBuilder(max_width=round(1024 * metrics.scale))

    def add_btn(
        prefix: str,
        icon: str,
        size: int,
        icon_size: int,
        *,
        surface_bg: str,
        variant: ButtonVariant = "standard",
        optical_dx: float = 0.0,
    ) -> None:
        for st in STATES:
            btn_sheet.add(
                f"{prefix}_{st}",
                render_icon_button(
                    tokens,
                    icon,
                    size,
                    icon_size,
                    surface_bg=surface_bg,
                    variant=variant,
                    state=st,
                    optical_dx=optical_dx,
                ),
            )

    # --- Top App Bar, Playlist Header, Equalizer Header (surface_container_low) ---
    add_btn("btn_menu", "menu", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_tools_off", "tune", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_tools_on", "tune", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low, variant="tonal")
    add_btn("btn_pin_off", "keep", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_pin_on", "keep-fill", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low, variant="tonal")
    add_btn("btn_info", "info", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_rec_on", "radio_button_checked", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low, variant="record")
    add_btn("btn_mini", "picture_in_picture_alt", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_min", "remove", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_max", "crop_square", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_restore", "filter_none", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low)
    add_btn("btn_close_low", "close", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_low, variant="close")

    # Contextual DVD buttons in Top App Bar (surface_container_low)
    add_btn("btn_dvd_ptitle", "first_page", metrics.btn_dvd, metrics.icon_xs, surface_bg=bg_low)
    add_btn("btn_dvd_pchap", "chevron_left", metrics.btn_dvd, metrics.icon_xs, surface_bg=bg_low)
    add_btn("btn_dvd_menu", "album", metrics.btn_dvd, metrics.icon_xs, surface_bg=bg_low)
    add_btn("btn_dvd_nchap", "chevron_right", metrics.btn_dvd, metrics.icon_xs, surface_bg=bg_low)
    add_btn("btn_dvd_ntitle", "last_page", metrics.btn_dvd, metrics.icon_xs, surface_bg=bg_low)

    # --- Bottom Control Bar & Playlist Toolbar (surface_container) ---
    add_btn("btn_open", "folder_open", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_stop", "stop-fill", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_audio", "headphones", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_subs", "subtitles", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_eq_off", "equalizer", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_eq_on", "equalizer", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_pl_off", "queue_music", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_on", "queue_music-fill", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_shuffle_off", "shuffle", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_shuffle_on", "shuffle", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_prev", "skip_previous-fill", metrics.btn_md, metrics.icon_lg, surface_bg=bg_mid)
    add_btn("btn_next", "skip_next-fill", metrics.btn_md, metrics.icon_lg, surface_bg=bg_mid)
    add_btn("btn_repeat_off", "repeat", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_repeat_all", "repeat", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_repeat_one", "repeat_one", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_vol", "volume_up", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_mute", "volume_off-fill", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid, variant="muted")
    add_btn("btn_more", "more_vert", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_fs", "fullscreen", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)

    add_btn("btn_pl_add", "add", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_del", "delete", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_sort", "sort_by_alpha", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_load", "file_open", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_save", "save", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_pl_dialog", "more_vert", metrics.btn_md, metrics.icon_md, surface_bg=bg_mid)

    # --- Compact Mini-Player buttons (surface_container) ---
    add_btn("btn_c_pin_off", "keep", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid)
    add_btn("btn_c_pin_on", "keep-fill", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_expand", "open_in_full", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid)
    add_btn("btn_close_mid", "close", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="close")
    add_btn("btn_c_shuffle_off", "shuffle", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid)
    add_btn("btn_c_shuffle_on", "shuffle", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_c_prev", "skip_previous-fill", metrics.btn_sm, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_c_next", "skip_next-fill", metrics.btn_sm, metrics.icon_md, surface_bg=bg_mid)
    add_btn("btn_c_repeat_off", "repeat", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid)
    add_btn("btn_c_repeat_all", "repeat", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_c_repeat_one", "repeat_one", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="tonal")
    add_btn("btn_c_vol", "volume_up", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid)
    add_btn("btn_c_mute", "volume_off-fill", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_mid, variant="muted")

    # --- Floating Fullscreen Controller HUD & About Dialog (surface_container_high) ---
    add_btn("btn_fs_audio", "headphones", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_subs", "subtitles", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_slower", "fast_rewind", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_prev", "skip_previous-fill", metrics.btn_md, metrics.icon_lg, surface_bg=bg_high)
    add_btn("btn_fs_next", "skip_next-fill", metrics.btn_md, metrics.icon_lg, surface_bg=bg_high)
    add_btn("btn_fs_faster", "fast_forward", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_vol", "volume_up", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_mute", "volume_off-fill", metrics.btn_md, metrics.icon_md, surface_bg=bg_high, variant="muted")
    add_btn("btn_fs_snap", "photo_camera", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_fs_exit", "fullscreen_exit", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_close_high", "close", metrics.btn_sm, metrics.icon_sm, surface_bg=bg_high, variant="close")

    # --- Control Center Section Card buttons (surface_container_high) ---
    add_btn("btn_t_step", "step_over", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_rec_off", "radio_button_checked", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_rec_on", "radio_button_checked", metrics.btn_md, metrics.icon_md, surface_bg=bg_high, variant="record")
    add_btn("btn_t_folder", "folder", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_net", "public", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_cast", "cast", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_info", "info", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_eq", "equalizer", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_mini", "picture_in_picture_alt", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_palette", "palette", metrics.btn_md, metrics.icon_md, surface_bg=bg_high, variant="tonal")
    add_btn("btn_t_prefs", "settings", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_msgs", "terminal", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)
    add_btn("btn_t_menu", "menu", metrics.btn_md, metrics.icon_md, surface_bg=bg_high)

    # --- Expressive Play/Pause Primary FABs (surface_container & surface_container_high) ---
    for st in STATES:
        btn_sheet.add(
            f"fab_play_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_w, metrics.fab_h, metrics.icon_lg,
                surface_bg=bg_mid, is_playing=False, state=st,
            ),
        )
        btn_sheet.add(
            f"fab_pause_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_w, metrics.fab_h, metrics.icon_lg,
                surface_bg=bg_mid, is_playing=True, state=st,
            ),
        )
        btn_sheet.add(
            f"fab_fs_play_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_w, metrics.fab_h, metrics.icon_lg,
                surface_bg=bg_high, is_playing=False, state=st,
            ),
        )
        btn_sheet.add(
            f"fab_fs_pause_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_w, metrics.fab_h, metrics.icon_lg,
                surface_bg=bg_high, is_playing=True, state=st,
            ),
        )
        btn_sheet.add(
            f"fab_compact_play_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_compact_w, metrics.fab_compact_h, metrics.icon_md,
                surface_bg=bg_mid, is_playing=False, state=st,
            ),
        )
        btn_sheet.add(
            f"fab_compact_pause_{st}",
            render_play_pause_fab(
                tokens, metrics.fab_compact_w, metrics.fab_compact_h, metrics.icon_md,
                surface_bg=bg_mid, is_playing=True, state=st,
            ),
        )

    # --- Authentic Material 3 Switch (Equalizer Top Bar -> surface_container_low) ---
    for st in STATES:
        btn_sheet.add(
            f"switch_off_{st}",
            render_m3_switch(tokens, metrics, surface_bg=bg_low, checked=False, state=st),
        )
        btn_sheet.add(
            f"switch_on_{st}",
            render_m3_switch(tokens, metrics, surface_bg=bg_low, checked=True, state=st),
        )

    # --- Opaque Slider Handles & Scrollbar ---
    for st in STATES:
        btn_sheet.add(
            f"handle_seek_{st}",
            render_horizontal_slider_handle(
                tokens, metrics.seek_handle_w, metrics.seek_handle_h, metrics.seek_track_h,
                surface_bg=bg_mid, state=st,
            ),
        )
        btn_sheet.add(
            f"handle_fs_{st}",
            render_horizontal_slider_handle(
                tokens, metrics.seek_handle_w, metrics.seek_handle_h, metrics.seek_track_h,
                surface_bg=bg_high, state=st,
            ),
        )
        btn_sheet.add(
            f"handle_eq_{st}",
            render_eq_slider_handle(
                tokens, metrics.eq_handle_w, metrics.eq_handle_h,
                surface_bg=bg_mid, state=st,
            ),
        )
        btn_sheet.add(
            f"scrollbar_{st}",
            render_scrollbar_thumb(
                tokens, metrics.scrollbar_w, metrics.scrollbar_h,
                surface_bg=bg_low, state=st,
            ),
        )

    btn_sheet.add("resize_grip", render_resize_grip(tokens, metrics.resize_corner))

    sheet_img, sheet_subs = btn_sheet.pack()
    save_png("ui_controls", "ui_controls.png", sheet_img, sheet_subs)

    # Separate sheet for spacious 26x26dp Material 3 Playtree row glyphs (sets row height ~28dp!)
    glyph_w = metrics.px(26)
    glyph_h = metrics.px(26)
    glyph_icon = metrics.px(14)
    glyph_sheet = SpriteSheetBuilder(max_width=256, padding=2)
    glyph_sheet.add(
        "tree_item",
        render_tree_glyph(tokens, "music_note", glyph_w, glyph_h, glyph_icon, c.on_surface_variant),
    )
    glyph_sheet.add(
        "tree_open",
        render_tree_glyph(tokens, "keyboard_arrow_down", glyph_w, glyph_h, glyph_icon, c.primary),
    )
    glyph_sheet.add(
        "tree_closed",
        render_tree_glyph(tokens, "chevron_right", glyph_w, glyph_h, glyph_icon, c.on_surface_variant),
    )
    g_img, g_subs = glyph_sheet.pack()
    save_png("tree_glyphs", "tree_glyphs.png", g_img, g_subs)

    # ------------------------------------------------------------------
    # 2. Opaque Slider Background Sprite Strips
    # ------------------------------------------------------------------
    save_png(
        "slider_seek_main",
        "slider_seek_main.png",
        render_horizontal_slider_strip(
            tokens, metrics.main_seek_w, metrics.seek_h, metrics.seek_track_h, frames=160, surface_bg=bg_mid
        ),
    )
    save_png(
        "slider_seek_compact",
        "slider_seek_compact.png",
        render_horizontal_slider_strip(
            tokens, metrics.compact_seek_w, metrics.seek_h, metrics.seek_track_h, frames=100, surface_bg=bg_mid
        ),
    )
    save_png(
        "slider_seek_fs",
        "slider_seek_fs.png",
        render_horizontal_slider_strip(
            tokens, metrics.fs_seek_w, metrics.seek_h, metrics.seek_track_h, frames=160, surface_bg=bg_high
        ),
    )
    save_png(
        "slider_vol_main",
        "slider_vol_main.png",
        render_horizontal_slider_strip(
            tokens, metrics.vol_w, metrics.vol_h, metrics.seek_track_h, frames=60, surface_bg=bg_mid
        ),
    )
    save_png(
        "slider_vol_fs",
        "slider_vol_fs.png",
        render_horizontal_slider_strip(
            tokens, metrics.vol_w, metrics.vol_h, metrics.seek_track_h, frames=60, surface_bg=bg_high
        ),
    )
    save_png(
        "slider_vol_compact",
        "slider_vol_compact.png",
        render_horizontal_slider_strip(
            tokens, metrics.vol_compact_w, metrics.vol_h, metrics.seek_track_h, frames=48, surface_bg=bg_mid
        ),
    )
    save_png(
        "slider_eq_band",
        "slider_eq_band.png",
        render_eq_slider_strip(
            tokens, metrics.eq_slider_w, metrics.eq_slider_h, frames=41, surface_bg=bg_mid
        ),
    )

    # ------------------------------------------------------------------
    # 3. Window Chrome, Surfaces, Borders, Album Art, Equalizer, HUD, About
    # ------------------------------------------------------------------
    b = metrics.border
    edge = max(3, round(3 * metrics.scale))
    save_png("bg_topbar", "bg_topbar.png", render_topbar_bg(tokens, metrics.main_w, metrics.topbar_h))
    save_png("bg_controls", "bg_controls.png", render_controls_bg(tokens, metrics.main_w, metrics.controls_h))
    save_png("bg_stage", "bg_stage.png", render_solid_rect(16, 16, c.media_stage))
    save_png("bg_playlist", "bg_playlist.png", render_playlist_sheet_bg(tokens, metrics))
    save_png(
        "bg_playlist_toolbar",
        "bg_playlist_toolbar.png",
        render_playlist_toolbar_bg(tokens, metrics.playlist_w, metrics.playlist_toolbar_h),
    )
    save_png("bg_compact", "bg_compact.png", render_compact_bg(tokens, metrics.compact_w, metrics.compact_h))
    save_png("bg_eq", "bg_eq.png", render_equalizer_bg(tokens, metrics))
    save_png("bg_tools", "bg_tools.png", render_tools_card(tokens, metrics))
    save_png("bg_fs", "bg_fs.png", render_fullscreen_hud_bg(tokens, metrics.fs_w, metrics.fs_h))
    save_png("bg_about", "bg_about.png", render_about_card(tokens, metrics))

    save_png(
        "art_placeholder",
        "art_placeholder.png",
        render_album_art_placeholder(tokens, metrics.art_card_size, surface_bg=c.media_stage, compact=False),
    )
    save_png(
        "art_placeholder_compact",
        "art_placeholder_compact.png",
        render_album_art_placeholder(tokens, metrics.compact_art, surface_bg=bg_mid, compact=True),
    )

    save_png("border_v", "border_v.png", render_solid_rect(b, 16, c.window_border))
    save_png("divider_v", "divider_v.png", render_solid_rect(b, 16, c.divider_subtle))
    save_png("resize_e_stage", "resize_e_stage.png", render_resize_strip_e(tokens, edge, 16, c.media_stage))
    save_png("resize_e_controls", "resize_e_controls.png", render_resize_strip_e(tokens, edge, 16, bg_mid))
    save_png("resize_e_playlist", "resize_e_playlist.png", render_resize_strip_e(tokens, edge, 16, bg_low))
    save_png("resize_s_controls", "resize_s_controls.png", render_resize_strip_s(tokens, 16, edge, bg_mid))

    return bitmaps
