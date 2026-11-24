"""Single source of truth for scaled Material 3 VLC Skins2 geometry metrics.

Every window dimension, panel frame, icon button bounding box, slider track,
and coordinate across all layouts is derived from `SkinMetrics.for_scale(scale)`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkinMetrics:
    """Pixel geometry scaled cleanly for 1x, 1.25x, 1.5x, or 2x displays."""

    scale: float

    # Common chrome
    border: int
    topbar_h: int
    controls_h: int
    resize_edge: int
    resize_corner: int

    # Button sizes
    btn_sm: int          # 32dp Top App Bar / compact icon button
    btn_md: int          # 36dp Bottom Control Bar icon button
    btn_dvd: int         # 28dp Contextual DVD bar icon button
    fab_w: int           # 56dp Primary Play/Pause M3 Expressive FAB width
    fab_h: int           # 44dp Primary Play/Pause M3 Expressive FAB height
    fab_compact_w: int   # 48dp Compact Mini-Player Play/Pause FAB width
    fab_compact_h: int   # 36dp Compact Mini-Player Play/Pause FAB height
    switch_w: int        # 52dp Authentic Material 3 Switch width
    switch_h: int        # 32dp Authentic Material 3 Switch height

    # Icon glyph sizes inside buttons
    icon_xs: int         # 16dp
    icon_sm: int         # 18dp
    icon_md: int         # 20dp
    icon_lg: int         # 24dp

    # Sliders
    seek_h: int          # 24dp interactive seek bar height
    seek_track_h: int    # 6dp M3 track height
    seek_handle_w: int   # 14dp cursor bitmap width (includes gap cutout around 4dp pill)
    seek_handle_h: int   # 24dp cursor bitmap height
    vol_w: int           # 84dp volume slider width
    vol_compact_w: int   # 64dp mini-player volume slider width
    vol_h: int           # 24dp volume slider height
    eq_slider_w: int     # 26dp vertical EQ slider frame width
    eq_slider_h: int     # 136dp vertical EQ slider frame height
    eq_handle_w: int     # 22dp vertical EQ slider handle width
    eq_handle_h: int     # 12dp vertical EQ slider handle height
    scrollbar_w: int     # 8dp playtree scrollbar thumb width
    scrollbar_h: int     # 32dp playtree scrollbar thumb height

    # Main player window (Normal layout)
    main_w: int
    main_h: int
    main_min_w: int
    main_min_h: int
    stage_h: int         # main_h - topbar_h - controls_h
    art_card_size: int   # 196dp album art showcase size

    # Main player + docked Playlist Side Sheet layout
    playlist_w: int      # 272dp M3 Side Sheet width
    playlist_header_h: int
    playlist_toolbar_h: int
    main_pl_w: int
    main_pl_min_w: int

    # Compact Mini-Player layout
    compact_w: int
    compact_h: int
    compact_min_w: int
    compact_max_w: int
    compact_art: int     # 100dp mini-player album art square

    # Equalizer window
    eq_w: int
    eq_h: int
    eq_header_h: int

    # Material 3 Control Center / Quick Tools window
    tools_w: int
    tools_h: int
    tools_header_h: int
    tools_footer_h: int

    # Fullscreen floating HUD controller
    fs_w: int
    fs_h: int

    # About card window
    about_w: int
    about_h: int

    # Derived seek track widths (for SliderBackground sprite generation)
    main_seek_w: int
    main_pl_seek_w: int
    compact_seek_w: int
    fs_seek_w: int

    # Playtree glyphs
    tree_glyph: int

    @classmethod
    def for_scale(cls, scale: float = 1.0) -> SkinMetrics:
        def px(dp: int) -> int:
            return max(1, round(dp * scale))

        def px_even(dp: int) -> int:
            v = max(2, round(dp * scale))
            return v + (v % 2)

        border = max(1, round(1 * scale))
        topbar_h = px_even(40)
        controls_h = px_even(96)

        main_w = px_even(900)
        main_h = px_even(568)
        main_min_w = px_even(760)
        main_min_h = px_even(340)
        stage_h = main_h - topbar_h - controls_h

        playlist_w = px_even(272)
        main_pl_w = main_w + playlist_w
        main_pl_min_w = main_min_w + playlist_w

        compact_w = px_even(500)
        compact_h = px_even(132)
        compact_min_w = px_even(436)
        compact_max_w = px_even(960)
        compact_art = px_even(100)

        eq_w = px_even(492)
        eq_h = px_even(268)
        eq_header_h = px_even(48)

        tools_w = px_even(416)
        tools_h = px_even(320)
        tools_header_h = px_even(48)
        tools_footer_h = px_even(30)

        fs_w = px_even(780)
        fs_h = px_even(96)

        about_w = px_even(380)
        about_h = px_even(220)

        time_pad = px_even(68)
        main_seek_w = main_w - 2 * time_pad
        main_pl_seek_w = main_w - 2 * time_pad
        compact_left = px_even(128)
        compact_time_pad = px_even(48)
        compact_seek_w = compact_w - compact_left - px_even(10) - 2 * compact_time_pad
        fs_seek_w = fs_w - 2 * time_pad

        return cls(
            scale=scale,
            border=border,
            topbar_h=topbar_h,
            controls_h=controls_h,
            resize_edge=px(6),
            resize_corner=px(14),
            btn_sm=px_even(32),
            btn_md=px_even(36),
            btn_dvd=px_even(28),
            fab_w=px_even(56),
            fab_h=px_even(44),
            fab_compact_w=px_even(48),
            fab_compact_h=px_even(36),
            switch_w=px_even(52),
            switch_h=px_even(32),
            icon_xs=px_even(16),
            icon_sm=px_even(18),
            icon_md=px_even(20),
            icon_lg=px_even(24),
            seek_h=px_even(24),
            seek_track_h=px_even(6),
            seek_handle_w=px_even(14),
            seek_handle_h=px_even(24),
            vol_w=px_even(84),
            vol_compact_w=px_even(64),
            vol_h=px_even(24),
            eq_slider_w=px_even(26),
            eq_slider_h=px_even(136),
            eq_handle_w=px_even(22),
            eq_handle_h=px_even(12),
            scrollbar_w=px_even(8),
            scrollbar_h=px_even(32),
            main_w=main_w,
            main_h=main_h,
            main_min_w=main_min_w,
            main_min_h=main_min_h,
            stage_h=stage_h,
            art_card_size=px_even(196),
            playlist_w=playlist_w,
            playlist_header_h=topbar_h,
            playlist_toolbar_h=px_even(48),
            main_pl_w=main_pl_w,
            main_pl_min_w=main_pl_min_w,
            compact_w=compact_w,
            compact_h=compact_h,
            compact_min_w=compact_min_w,
            compact_max_w=compact_max_w,
            compact_art=compact_art,
            eq_w=eq_w,
            eq_h=eq_h,
            eq_header_h=eq_header_h,
            tools_w=tools_w,
            tools_h=tools_h,
            tools_header_h=tools_header_h,
            tools_footer_h=tools_footer_h,
            fs_w=fs_w,
            fs_h=fs_h,
            about_w=about_w,
            about_h=about_h,
            main_seek_w=main_seek_w,
            main_pl_seek_w=main_pl_seek_w,
            compact_seek_w=compact_seek_w,
            fs_seek_w=fs_seek_w,
            tree_glyph=px_even(12),
        )

    def px(self, dp: int) -> int:
        return max(1, round(dp * self.scale))

    def px0(self, dp: int) -> int:
        return round(dp * self.scale)
