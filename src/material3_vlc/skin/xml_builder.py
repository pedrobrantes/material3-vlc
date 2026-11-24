"""VLC Skins2 `theme.xml` generator for Material 3 VLC.

Engineered specifically around VLC 3.0.x `skins2` C++ layout & rendering rules:
- `<Theme tooltipfont="defaultfont">` (VLC builds Theme before custom Fonts)
- `<Slider>` omits explicit `width`/`height` so `Bezier::getWidth()`/`getHeight()`
  keeps `factorX = 1.0`, `factorY = 1.0` and prevents track stretching / handle offset!
- Every interactive control references surface-matched opaque (`alpha=255`) sprites
  so Win32/X11 `drawGraphics()` (`BitBlt` + 1-bit `HRGN`) renders crisp anti-aliased UI.
"""

from __future__ import annotations

from lxml import etree

from material3_vlc.render.sprites import BitmapSpec
from material3_vlc.render.surfaces import EQ_BAND_LABELS
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.tokens.color import blend_over
from material3_vlc.tokens.theme import DesignTokens

DOCTYPE_DECL = '<!DOCTYPE Theme PUBLIC "-//VideoLAN//DTD VLC Skins V2.0//EN" "skin.dtd">'


def _el(parent: etree._Element, tag: str, **attrs: str | int) -> etree._Element:
    str_attrs: dict[str, str] = {k: str(v) for k, v in attrs.items()}
    return etree.SubElement(parent, tag, attrib=str_attrs)


def _ft2_text_y(container_top: int, container_h: int, font_size: int) -> int:
    """Vertically center a FreeType2 `<Text>` box inside `container_h`.

    FreeType renders Roboto with a bounding box of approximately `1.22 * size`.
    """
    rendered_h = round(font_size * 1.22)
    return container_top + max(0, (container_h - rendered_h) // 2)


def _add_repeat_cycle(
    parent: etree._Element,
    prefix: str,
    x: int,
    y: int,
    *,
    compact: bool = False,
    lefttop: str = "lefttop",
    rightbottom: str = "lefttop",
) -> None:
    """Emit 3 mutually exclusive M3 Repeat buttons: Off -> Repeat All -> Repeat One."""
    b = "btn_c_repeat" if compact else "btn_repeat"
    _el(
        parent,
        "Button",
        id=f"{prefix}_repeat_off",
        x=x,
        y=y,
        lefttop=lefttop,
        rightbottom=rightbottom,
        up=f"{b}_off_up",
        over=f"{b}_off_over",
        down=f"{b}_off_down",
        action="playlist.setLoop(true)",
        visible="not playlist.isLoop and not playlist.isRepeat",
        tooltiptext="Repeat: Off (Click for Repeat All)",
        help="Enable Repeat All",
    )
    _el(
        parent,
        "Button",
        id=f"{prefix}_repeat_all",
        x=x,
        y=y,
        lefttop=lefttop,
        rightbottom=rightbottom,
        up=f"{b}_all_up",
        over=f"{b}_all_over",
        down=f"{b}_all_down",
        action="playlist.setLoop(false);playlist.setRepeat(true)",
        visible="playlist.isLoop",
        tooltiptext="Repeat: All (Click for Repeat One)",
        help="Switch to Repeat One",
    )
    _el(
        parent,
        "Button",
        id=f"{prefix}_repeat_one",
        x=x,
        y=y,
        lefttop=lefttop,
        rightbottom=rightbottom,
        up=f"{b}_one_up",
        over=f"{b}_one_over",
        down=f"{b}_one_down",
        action="playlist.setRepeat(false);playlist.setLoop(false)",
        visible="playlist.isRepeat",
        tooltiptext="Repeat: One (Click to Disable)",
        help="Disable Repeat",
    )


def _add_main_topbar(
    layout: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
    *,
    prefix: str,
    bar_w: int,
) -> None:
    """Build the Material 3 Top App Bar (40dp) on `surface_container_low`."""
    c = tokens.colors
    btn_y = (m.topbar_h - m.btn_sm) // 2
    gap = m.px(2)

    panel = _el(
        layout,
        "Panel",
        id=f"{prefix}_topbar",
        x=0,
        y=0,
        width=bar_w,
        height=m.topbar_h,
        lefttop="lefttop",
        rightbottom="righttop",
    )

    _el(
        panel,
        "Image",
        id=f"{prefix}_topbar_bg_norm",
        x=0,
        y=0,
        width=bar_w,
        height=m.topbar_h,
        image="bg_topbar",
        resize="scale",
        action="move",
        action2="main.maximize()",
        visible="not main.isMaximized()",
        lefttop="lefttop",
        rightbottom="righttop",
    )
    _el(
        panel,
        "Image",
        id=f"{prefix}_topbar_bg_max",
        x=0,
        y=0,
        width=bar_w,
        height=m.topbar_h,
        image="bg_topbar",
        resize="scale",
        action="move",
        action2="main.unmaximize()",
        visible="main.isMaximized()",
        lefttop="lefttop",
        rightbottom="righttop",
    )

    # Left app-bar icon buttons: VLC Menu, Control Center, Always-on-Top Pin, File Info, Recording
    lx = m.px(6)
    _el(
        panel,
        "Button",
        id=f"{prefix}_menu",
        x=lx,
        y=btn_y,
        up="btn_menu_up",
        over="btn_menu_over",
        down="btn_menu_down",
        action="dialogs.popup()",
        tooltiptext="Full VLC Menu",
        help="Open Full Native VLC Menu",
    )
    lx += m.btn_sm + gap
    _el(
        panel,
        "Checkbox",
        id=f"{prefix}_tools_toggle",
        x=lx,
        y=btn_y,
        state="toolswin.isVisible",
        up1="btn_tools_off_up",
        over1="btn_tools_off_over",
        down1="btn_tools_off_down",
        up2="btn_tools_on_up",
        over2="btn_tools_on_over",
        down2="btn_tools_on_down",
        action1="toolswin.show()",
        action2="toolswin.hide()",
        tooltiptext1="Open Control Center (Speed, Tracks, Themes & Tools)",
        tooltiptext2="Close Control Center",
        help="Toggle Material 3 Control Center",
    )
    lx += m.btn_sm + gap
    _el(
        panel,
        "Checkbox",
        id=f"{prefix}_aot",
        x=lx,
        y=btn_y,
        state="vlc.isOnTop",
        up1="btn_pin_off_up",
        over1="btn_pin_off_over",
        down1="btn_pin_off_down",
        up2="btn_pin_on_up",
        over2="btn_pin_on_over",
        down2="btn_pin_on_down",
        action1="vlc.onTop()",
        action2="vlc.onTop()",
        tooltiptext1="Pin Always on Top",
        tooltiptext2="Unpin Always on Top",
        help="Toggle Always on Top",
    )
    lx += m.btn_sm + gap
    _el(
        panel,
        "Button",
        id=f"{prefix}_info",
        x=lx,
        y=btn_y,
        up="btn_info_up",
        over="btn_info_over",
        down="btn_info_down",
        action="dialogs.fileInfo()",
        tooltiptext="Media Information",
        help="Show Media Information",
    )
    lx += m.btn_sm + gap
    _el(
        panel,
        "Button",
        id=f"{prefix}_rec_active",
        x=lx,
        y=btn_y,
        up="btn_rec_on_up",
        over="btn_rec_on_over",
        down="btn_rec_on_down",
        action="vlc.toggleRecord()",
        visible="vlc.isRecording",
        tooltiptext="Recording Active (Click to Stop)",
        help="Stop Recording",
    )

    # Right window controls: Mini-Player, Minimize, Maximize/Restore, Close
    right_count = 4
    right_block_w = right_count * m.btn_sm + (right_count - 1) * gap + m.px(6)
    rx = bar_w - right_block_w

    _el(
        panel,
        "Button",
        id=f"{prefix}_mini",
        x=rx,
        y=btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_mini_up",
        over="btn_mini_over",
        down="btn_mini_down",
        action="main.setLayout(main_compact)",
        tooltiptext="Compact Mini-Player",
        help="Switch to Compact Mini-Player",
    )
    rx += m.btn_sm + gap
    _el(
        panel,
        "Button",
        id=f"{prefix}_min",
        x=rx,
        y=btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_min_up",
        over="btn_min_over",
        down="btn_min_down",
        action="vlc.minimize()",
        tooltiptext="Minimize",
        help="Minimize VLC",
    )
    rx += m.btn_sm + gap
    _el(
        panel,
        "Button",
        id=f"{prefix}_max",
        x=rx,
        y=btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_max_up",
        over="btn_max_over",
        down="btn_max_down",
        action="main.maximize()",
        visible="not main.isMaximized()",
        tooltiptext="Maximize",
        help="Maximize Window",
    )
    _el(
        panel,
        "Button",
        id=f"{prefix}_restore",
        x=rx,
        y=btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_restore_up",
        over="btn_restore_over",
        down="btn_restore_down",
        action="main.unmaximize()",
        visible="main.isMaximized()",
        tooltiptext="Restore Down",
        help="Restore Window Size",
    )
    rx += m.btn_sm + gap
    _el(
        panel,
        "Button",
        id=f"{prefix}_close",
        x=rx,
        y=btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_close_low_up",
        over="btn_close_low_over",
        down="btn_close_low_down",
        action="vlc.quit()",
        tooltiptext="Quit VLC",
        help="Quit VLC",
    )

    # Contextual DVD controls strip
    dvd_w = 5 * m.btn_dvd + 4 * m.px(2)
    dvd_x = bar_w - right_block_w - dvd_w - m.px(10)
    dvd_y = (m.topbar_h - m.btn_dvd) // 2
    dvd_items = [
        ("ptitle", "btn_dvd_ptitle", "dvd.previousTitle()", "Previous DVD Title"),
        ("pchap", "btn_dvd_pchap", "dvd.previousChapter()", "Previous DVD Chapter"),
        ("menu", "btn_dvd_menu", "dvd.rootMenu()", "DVD Root Menu"),
        ("nchap", "btn_dvd_nchap", "dvd.nextChapter()", "Next DVD Chapter"),
        ("ntitle", "btn_dvd_ntitle", "dvd.nextTitle()", "Next DVD Title"),
    ]
    for idx, (slug, bmp, act, tip) in enumerate(dvd_items):
        _el(
            panel,
            "Button",
            id=f"{prefix}_dvd_{slug}",
            x=dvd_x + idx * (m.btn_dvd + m.px(2)),
            y=dvd_y,
            lefttop="righttop",
            rightbottom="righttop",
            up=f"{bmp}_up",
            over=f"{bmp}_over",
            down=f"{bmp}_down",
            action=act,
            visible="dvd.isActive",
            tooltiptext=tip,
            help=tip,
        )

    # Scrolling Media Title ($N) vertically centered with FT2 metrics
    title_x = lx + m.btn_sm + m.px(8)
    title_y = _ft2_text_y(0, m.topbar_h, tokens.typography.title_small.size)
    title_w_normal = max(m.px(120), bar_w - title_x - right_block_w - m.px(12))
    title_w_dvd = max(m.px(80), dvd_x - title_x - m.px(8))

    _el(
        panel,
        "Text",
        id=f"{prefix}_title",
        x=title_x,
        y=title_y,
        width=title_w_normal,
        lefttop="lefttop",
        rightbottom="righttop",
        text="$N",
        font=tokens.typography.title_small.id,
        color=c.on_surface,
        alignment="center",
        scrolling="auto",
        visible="not dvd.isActive",
    )
    _el(
        panel,
        "Text",
        id=f"{prefix}_title_dvd",
        x=title_x,
        y=title_y,
        width=title_w_dvd,
        lefttop="lefttop",
        rightbottom="righttop",
        text="$N",
        font=tokens.typography.title_small.id,
        color=c.on_surface,
        alignment="left",
        scrolling="auto",
        visible="dvd.isActive",
    )


def _add_main_stage(
    layout: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
    *,
    prefix: str,
    stage_w: int,
) -> None:
    """Build the Video canvas & Album Art showcase stage."""
    c = tokens.colors
    stage = _el(
        layout,
        "Panel",
        id=f"{prefix}_stage",
        x=0,
        y=m.topbar_h,
        width=stage_w,
        height=m.stage_h,
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    _el(
        stage,
        "Image",
        id=f"{prefix}_stage_bg",
        x=0,
        y=0,
        width=stage_w,
        height=m.stage_h,
        image="bg_stage",
        resize="scale",
        action="move",
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    # Centered Album Art panel bounded safely inside minwidth
    art_panel_w = min(stage_w - m.px(32), m.px(600))
    art_panel_x = (stage_w - art_panel_w) // 2
    art_panel_h = m.art_card_size + m.px(40)
    art_panel_y = max(m.px(12), (m.stage_h - art_panel_h) // 2)
    art_panel = _el(
        stage,
        "Panel",
        id=f"{prefix}_art_panel",
        x=art_panel_x,
        y=art_panel_y,
        width=art_panel_w,
        height=art_panel_h,
        lefttop="lefttop",
        rightbottom="lefttop",
        xkeepratio="true",
        ykeepratio="true",
    )
    art_x = (art_panel_w - m.art_card_size) // 2
    _el(
        art_panel,
        "Image",
        id=f"{prefix}_album_art",
        x=art_x,
        y=0,
        width=m.art_card_size,
        height=m.art_card_size,
        image="art_placeholder",
        art="true",
        resize="scale2",
        action2="dialogs.fileInfo()",
        visible="not vlc.hasVout",
        help="Double-click for Media Information",
    )
    _el(
        art_panel,
        "Text",
        id=f"{prefix}_art_title",
        x=m.px(8),
        y=m.art_card_size + m.px(14),
        width=art_panel_w - m.px(16),
        text="$N",
        font=tokens.typography.title_medium.id,
        color=c.on_surface,
        alignment="center",
        scrolling="auto",
        visible="not vlc.hasVout and not vlc.isStopped",
    )

    _el(
        stage,
        "Video",
        id=f"{prefix}_video",
        x=0,
        y=0,
        width=stage_w,
        height=m.stage_h,
        lefttop="lefttop",
        rightbottom="rightbottom",
        autoresize="false",
        visible="vlc.hasVout",
    )


def _add_main_controls(
    layout: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
    *,
    prefix: str,
    bar_w: int,
    playlist_open: bool,
) -> None:
    """Build the elevated Material 3 Bottom Control Bar (96dp) on `surface_container`."""
    c = tokens.colors
    ctrl_y = m.main_h - m.controls_h

    ctrl = _el(
        layout,
        "Panel",
        id=f"{prefix}_controls",
        x=0,
        y=ctrl_y,
        width=bar_w,
        height=m.controls_h,
        lefttop="leftbottom",
        rightbottom="rightbottom",
    )

    _el(
        ctrl,
        "Image",
        id=f"{prefix}_controls_bg",
        x=0,
        y=0,
        width=bar_w,
        height=m.controls_h,
        image="bg_controls",
        resize="scale",
        action="move",
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    # ------------------------------------------------------------------
    # Row 1: Timestamps + Material 3 Expressive Seek Slider
    # NOTE: `<Slider>` intentionally omits width/height so VLC Bezier keeps factorY=1.0!
    # ------------------------------------------------------------------
    time_pad = m.px(68)
    time_w = m.px(48)
    seek_y = m.px(8)
    time_y = _ft2_text_y(seek_y, m.seek_h, tokens.typography.label_medium.size)
    seek_w = bar_w - 2 * time_pad
    seek_mid_y = m.seek_h // 2

    _el(
        ctrl,
        "Text",
        id=f"{prefix}_time_cur",
        x=m.px(10),
        y=time_y,
        width=time_w,
        text="$t",
        font=tokens.typography.label_medium.id,
        color=c.on_surface_variant,
        alignment="right",
        visible="not vlc.isStopped",
    )
    seek_slider = _el(
        ctrl,
        "Slider",
        id=f"{prefix}_seek",
        x=time_pad,
        y=seek_y,
        lefttop="lefttop",
        rightbottom="righttop",
        points=f"(0,{seek_mid_y}),({seek_w - 1},{seek_mid_y})",
        thickness=m.seek_h // 2,
        value="time",
        up="handle_seek_up",
        over="handle_seek_over",
        down="handle_seek_down",
        tooltiptext="$t / $d",
        help="Seek playback position",
    )
    _el(
        seek_slider,
        "SliderBackground",
        id=f"{prefix}_seek_bg",
        image="slider_seek_main",
        nbvert=160,
    )
    _el(
        ctrl,
        "Text",
        id=f"{prefix}_time_tot",
        x=bar_w - m.px(58),
        y=time_y,
        width=time_w,
        lefttop="righttop",
        rightbottom="righttop",
        text="$d",
        font=tokens.typography.label_medium.id,
        color=c.on_surface_variant,
        alignment="left",
        visible="not vlc.isStopped",
    )

    # ------------------------------------------------------------------
    # Row 2: Left Actions | Center Expressive Transport | Right Volume & FS
    # ------------------------------------------------------------------
    row2_y = m.px(36)
    row2_h = m.controls_h - row2_y - m.px(4)
    btn_y = (row2_h - m.btn_md) // 2
    fab_y = (row2_h - m.fab_h) // 2
    gap = m.px(4)

    # Left cluster: Open, Stop, Audio Tracks, Subtitles/Video, Equalizer, Playlist
    left_gap = m.px(2)
    left_panel = _el(
        ctrl,
        "Panel",
        id=f"{prefix}_ctrl_left",
        x=m.px(12),
        y=row2_y,
        width=6 * m.btn_md + 5 * left_gap,
        height=row2_h,
        lefttop="lefttop",
        rightbottom="lefttop",
    )
    lx = 0
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_open",
        x=lx,
        y=btn_y,
        up="btn_open_up",
        over="btn_open_over",
        down="btn_open_down",
        action="dialogs.file()",
        tooltiptext="Open Media File",
        help="Open Media File",
    )
    lx += m.btn_md + left_gap
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_stop",
        x=lx,
        y=btn_y,
        up="btn_stop_up",
        over="btn_stop_over",
        down="btn_stop_down",
        action="vlc.stop()",
        tooltiptext="Stop",
        help="Stop Playback",
    )
    lx += m.btn_md + left_gap
    # Audio button: native VLC Audio Tracks/Devices menu while playing, M3 Audio menu when stopped
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_audio_live",
        x=lx,
        y=btn_y,
        up="btn_audio_up",
        over="btn_audio_over",
        down="btn_audio_down",
        action="dialogs.audioPopup()",
        visible="not vlc.isStopped",
        tooltiptext="Audio Tracks & Output Device",
        help="Open Audio Tracks & Devices Menu",
    )
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_audio_idle",
        x=lx,
        y=btn_y,
        up="btn_audio_up",
        over="btn_audio_over",
        down="btn_audio_down",
        action="m3_audio_menu.show()",
        visible="vlc.isStopped",
        tooltiptext="Audio Controls & Equalizer (Play media for Audio Tracks)",
        help="Open Audio Menu",
    )
    lx += m.btn_md + left_gap
    # Video/Subtitles button: native VLC Video/Subtitles menu while playing, M3 Video menu when stopped
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_subs_live",
        x=lx,
        y=btn_y,
        up="btn_subs_up",
        over="btn_subs_over",
        down="btn_subs_down",
        action="dialogs.videoPopup()",
        visible="not vlc.isStopped",
        tooltiptext="Video, Aspect Ratio & Subtitles",
        help="Open Video & Subtitles Menu",
    )
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_subs_idle",
        x=lx,
        y=btn_y,
        up="btn_subs_up",
        over="btn_subs_over",
        down="btn_subs_down",
        action="m3_video_menu.show()",
        visible="vlc.isStopped",
        tooltiptext="Video, Themes & Display Settings (Play media for Subtitles)",
        help="Open Video & Display Menu",
    )
    lx += m.btn_md + left_gap
    _el(
        left_panel,
        "Checkbox",
        id=f"{prefix}_eq_toggle",
        x=lx,
        y=btn_y,
        state="eqwin.isVisible",
        up1="btn_eq_off_up",
        over1="btn_eq_off_over",
        down1="btn_eq_off_down",
        up2="btn_eq_on_up",
        over2="btn_eq_on_over",
        down2="btn_eq_on_down",
        action1="eqwin.show()",
        action2="eqwin.hide()",
        tooltiptext1="Show Equalizer",
        tooltiptext2="Hide Equalizer",
        help="Toggle Equalizer Window",
    )
    lx += m.btn_md + left_gap
    pl_bmp = "btn_pl_on" if playlist_open else "btn_pl_off"
    pl_target = "main_normal" if playlist_open else "main_playlist"
    pl_tip = "Hide Playlist Side Sheet" if playlist_open else "Show Playlist Side Sheet"
    _el(
        left_panel,
        "Button",
        id=f"{prefix}_pl_toggle",
        x=lx,
        y=btn_y,
        up=f"{pl_bmp}_up",
        over=f"{pl_bmp}_over",
        down=f"{pl_bmp}_down",
        action=f"main.setLayout({pl_target})",
        tooltiptext=pl_tip,
        help=pl_tip,
    )

    # Center transport cluster (keeps exact 0.5 horizontal ratio on resize)
    fab_gap = m.px(8)
    center_w = 4 * m.btn_md + m.fab_w + 2 * gap + 2 * fab_gap
    center_x = (bar_w - center_w) // 2
    center_panel = _el(
        ctrl,
        "Panel",
        id=f"{prefix}_ctrl_center",
        x=center_x,
        y=row2_y,
        width=center_w,
        height=row2_h,
        lefttop="lefttop",
        rightbottom="lefttop",
        xkeepratio="true",
    )
    cx = 0
    _el(
        center_panel,
        "Checkbox",
        id=f"{prefix}_shuffle",
        x=cx,
        y=btn_y,
        state="playlist.isRandom",
        up1="btn_shuffle_off_up",
        over1="btn_shuffle_off_over",
        down1="btn_shuffle_off_down",
        up2="btn_shuffle_on_up",
        over2="btn_shuffle_on_over",
        down2="btn_shuffle_on_down",
        action1="playlist.setRandom(true)",
        action2="playlist.setRandom(false)",
        tooltiptext1="Enable Shuffle",
        tooltiptext2="Disable Shuffle",
        help="Toggle Shuffle",
    )
    cx += m.btn_md + gap
    _el(
        center_panel,
        "Button",
        id=f"{prefix}_prev",
        x=cx,
        y=btn_y,
        up="btn_prev_up",
        over="btn_prev_over",
        down="btn_prev_down",
        action="playlist.previous()",
        tooltiptext="Previous Track",
        help="Play Previous Item",
    )
    cx += m.btn_md + fab_gap
    _el(
        center_panel,
        "Checkbox",
        id=f"{prefix}_playpause",
        x=cx,
        y=fab_y,
        state="vlc.isPlaying",
        up1="fab_play_up",
        over1="fab_play_over",
        down1="fab_play_down",
        up2="fab_pause_up",
        over2="fab_pause_over",
        down2="fab_pause_down",
        action1="vlc.play()",
        action2="vlc.pause()",
        tooltiptext1="Play",
        tooltiptext2="Pause",
        help="Play / Pause",
    )
    cx += m.fab_w + fab_gap
    _el(
        center_panel,
        "Button",
        id=f"{prefix}_next",
        x=cx,
        y=btn_y,
        up="btn_next_up",
        over="btn_next_over",
        down="btn_next_down",
        action="playlist.next()",
        tooltiptext="Next Track",
        help="Play Next Item",
    )
    cx += m.btn_md + gap
    _add_repeat_cycle(center_panel, prefix, cx, btn_y)

    # Right cluster: Mute + Interactive Volume Slider + Quick Actions Menu + Fullscreen
    right_w = 3 * m.btn_md + m.vol_w + m.px(24)
    right_panel = _el(
        ctrl,
        "Panel",
        id=f"{prefix}_ctrl_right",
        x=bar_w - right_w - m.px(16),
        y=row2_y,
        width=right_w,
        height=row2_h,
        lefttop="righttop",
        rightbottom="righttop",
    )
    rx = 0
    _el(
        right_panel,
        "Checkbox",
        id=f"{prefix}_mute",
        x=rx,
        y=btn_y,
        state="vlc.isMute",
        up1="btn_vol_up",
        over1="btn_vol_over",
        down1="btn_vol_down",
        up2="btn_mute_up",
        over2="btn_mute_over",
        down2="btn_mute_down",
        action1="vlc.mute()",
        action2="vlc.mute()",
        tooltiptext1="Mute ($V%)",
        tooltiptext2="Unmute",
        help="Toggle Mute",
    )
    rx += m.btn_md + m.px(8)
    vol_y = (row2_h - m.vol_h) // 2
    vol_mid = m.vol_h // 2
    vol_slider = _el(
        right_panel,
        "Slider",
        id=f"{prefix}_volume",
        x=rx,
        y=vol_y,
        points=f"(0,{vol_mid}),({m.vol_w - 1},{vol_mid})",
        thickness=m.vol_h // 2,
        value="volume",
        up="handle_seek_up",
        over="handle_seek_over",
        down="handle_seek_down",
        tooltiptext="Volume: $V%",
        help="Adjust Volume",
    )
    _el(
        vol_slider,
        "SliderBackground",
        id=f"{prefix}_volume_bg",
        image="slider_vol_main",
        nbvert=60,
    )
    rx += m.vol_w + m.px(12)
    _el(
        right_panel,
        "Button",
        id=f"{prefix}_more",
        x=rx,
        y=btn_y,
        up="btn_more_up",
        over="btn_more_over",
        down="btn_more_down",
        action="m3_menu.show()",
        tooltiptext="More Options & Tracks",
        help="Open Material 3 Quick Menu",
    )
    rx += m.btn_md + m.px(4)
    _el(
        right_panel,
        "Button",
        id=f"{prefix}_fullscreen",
        x=rx,
        y=btn_y,
        up="btn_fs_up",
        over="btn_fs_over",
        down="btn_fs_down",
        action="vlc.fullscreen()",
        tooltiptext="Fullscreen",
        help="Toggle Fullscreen",
    )


def _add_window_borders_and_resize(
    layout: etree._Element,
    m: SkinMetrics,
    *,
    prefix: str,
    win_w: int,
    win_h: int,
    east_mode: str = "stage",
    allow_v_resize: bool = True,
) -> None:
    """Add crisp 1px outer borders plus opaque surface-matched East, South, and SE resize edges."""
    b = m.border
    edge = max(3, round(3 * m.scale))

    # Left crisp 1px border
    _el(
        layout,
        "Image",
        id=f"{prefix}_border_l",
        x=0,
        y=0,
        width=b,
        height=win_h,
        image="border_v",
        resize="scale",
        lefttop="lefttop",
        rightbottom="leftbottom",
    )
    # Right crisp 1px border on topbar area
    _el(
        layout,
        "Image",
        id=f"{prefix}_border_r_top",
        x=win_w - b,
        y=0,
        width=b,
        height=m.topbar_h if allow_v_resize else win_h,
        image="border_v",
        resize="scale",
        lefttop="righttop",
        rightbottom="righttop" if allow_v_resize else "rightbottom",
    )

    if east_mode == "stage":
        # Opaque East resize strip along Stage (`media_stage` + border)
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_e_stage",
            x=win_w - edge,
            y=m.topbar_h,
            width=edge,
            height=m.stage_h,
            image="resize_e_stage",
            resize="scale",
            action="resizeE",
            lefttop="righttop",
            rightbottom="rightbottom",
            help="Resize Horizontally",
        )
        # Opaque East resize strip along Bottom Controls (`surface_container` + border)
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_e_ctrl",
            x=win_w - edge,
            y=win_h - m.controls_h,
            width=edge,
            height=m.controls_h - m.resize_corner,
            image="resize_e_controls",
            resize="scale",
            action="resizeE",
            lefttop="rightbottom",
            rightbottom="rightbottom",
            help="Resize Horizontally",
        )
    elif east_mode == "playlist":
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_e_pl",
            x=win_w - edge,
            y=m.topbar_h,
            width=edge,
            height=win_h - m.topbar_h - m.playlist_toolbar_h,
            image="resize_e_playlist",
            resize="scale",
            action="resizeE",
            lefttop="righttop",
            rightbottom="rightbottom",
            help="Resize Horizontally",
        )
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_e_pltb",
            x=win_w - edge,
            y=win_h - m.playlist_toolbar_h,
            width=edge,
            height=m.playlist_toolbar_h - m.resize_corner,
            image="resize_e_controls",
            resize="scale",
            action="resizeE",
            lefttop="rightbottom",
            rightbottom="rightbottom",
            help="Resize Horizontally",
        )
    else:
        # Compact mini-player horizontal resize strip on right edge
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_e_compact",
            x=win_w - edge,
            y=m.px(44),
            width=edge,
            height=win_h - m.px(48),
            image="resize_e_controls",
            resize="scale",
            action="resizeE",
            lefttop="righttop",
            rightbottom="rightbottom",
            help="Resize Horizontally",
        )

    if allow_v_resize:
        # Opaque South resize strip along bottom (`surface_container` + 1px bottom border)
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_s",
            x=b,
            y=win_h - edge,
            width=win_w - b - m.resize_corner,
            height=edge,
            image="resize_s_controls",
            resize="scale",
            action="resizeS",
            lefttop="leftbottom",
            rightbottom="rightbottom",
            help="Resize Vertically",
        )
        # Opaque South-East Material 3 dot-matrix resize corner
        _el(
            layout,
            "Image",
            id=f"{prefix}_resize_se",
            x=win_w - m.resize_corner,
            y=win_h - m.resize_corner,
            image="resize_grip",
            action="resizeSE",
            lefttop="rightbottom",
            rightbottom="rightbottom",
            help="Resize Window",
        )


def _add_playlist_side_sheet(
    layout: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
) -> None:
    """Build the docked Material 3 Side Sheet Playlist (`surfaceContainerLow`)."""
    c = tokens.colors
    pl_x = m.main_w
    pl_w = m.playlist_w
    pl_h = m.main_h

    sheet = _el(
        layout,
        "Panel",
        id="pl_sheet",
        x=pl_x,
        y=0,
        width=pl_w,
        height=pl_h,
        lefttop="righttop",
        rightbottom="rightbottom",
    )

    _el(
        sheet,
        "Image",
        id="pl_sheet_bg",
        x=0,
        y=0,
        width=pl_w,
        height=pl_h,
        image="bg_playlist",
        resize="scale",
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    _el(
        sheet,
        "Image",
        id="pl_header_bg",
        x=0,
        y=0,
        width=pl_w,
        height=m.playlist_header_h,
        image="bg_topbar",
        resize="scale",
        action="move",
        lefttop="lefttop",
        rightbottom="righttop",
    )
    _el(
        sheet,
        "Text",
        id="pl_header_title",
        x=m.px(16),
        y=_ft2_text_y(0, m.playlist_header_h, tokens.typography.title_small.size),
        width=pl_w - m.btn_sm - m.px(28),
        text="Playlist",
        font=tokens.typography.title_small.id,
        color=c.on_surface,
        alignment="left",
    )
    _el(
        sheet,
        "Button",
        id="pl_header_close",
        x=pl_w - m.btn_sm - m.px(6),
        y=(m.playlist_header_h - m.btn_sm) // 2,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_close_low_up",
        over="btn_close_low_over",
        down="btn_close_low_down",
        action="main.setLayout(main_normal)",
        tooltiptext="Close Playlist Panel",
        help="Collapse Playlist Side Sheet",
    )

    tree_x = m.px(18)
    tree_y = m.playlist_header_h + m.px(18)
    tree_h = pl_h - m.playlist_header_h - m.playlist_toolbar_h - m.px(36)
    tree_w = pl_w - m.px(48)
    row_alt = blend_over(c.surface_container_low, c.surface_container, 0.48)

    playtree = _el(
        sheet,
        "Playtree",
        id="pl_playtree",
        x=tree_x,
        y=tree_y,
        width=tree_w,
        height=tree_h,
        lefttop="lefttop",
        rightbottom="rightbottom",
        font=tokens.typography.body_medium.id,
        bgcolor1=c.surface_container_low,
        bgcolor2=row_alt,
        fgcolor=c.on_surface,
        selcolor=c.secondary_container,
        playcolor=c.primary,
        itemimage="tree_item",
        openimage="tree_open",
        closedimage="tree_closed",
        flat="true",
    )
    sb_pad = m.scrollbar_h // 2 + m.px(2)
    _el(
        playtree,
        "Slider",
        id="pl_scrollbar",
        x=pl_w - m.px(20),
        y=tree_y,
        points=f"(0,{tree_h - sb_pad}),(0,{sb_pad})",
        thickness=m.scrollbar_w,
        up="scrollbar_up",
        over="scrollbar_over",
        down="scrollbar_down",
        lefttop="righttop",
        rightbottom="rightbottom",
        tooltiptext="Scroll Playlist",
    )

    tb_y = pl_h - m.playlist_toolbar_h
    toolbar = _el(
        sheet,
        "Panel",
        id="pl_toolbar",
        x=0,
        y=tb_y,
        width=pl_w,
        height=m.playlist_toolbar_h,
        lefttop="leftbottom",
        rightbottom="rightbottom",
    )
    _el(
        toolbar,
        "Image",
        id="pl_toolbar_bg",
        x=0,
        y=0,
        width=pl_w,
        height=m.playlist_toolbar_h,
        image="bg_playlist_toolbar",
        resize="scale",
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    tb_buttons = [
        ("add", "btn_pl_add", "playlist.add()", "Add Files to Playlist"),
        ("del", "btn_pl_del", "playlist.del()", "Remove Selected Item"),
        ("sort", "btn_pl_sort", "playlist.sort()", "Sort Playlist A-Z"),
        ("load", "btn_pl_load", "playlist.load()", "Load Playlist File"),
        ("save", "btn_pl_save", "playlist.save()", "Save Playlist File"),
        ("dialog", "btn_pl_dialog", "dialogs.playlist()", "Open Full Playlist Dialog"),
    ]
    tb_btn_y = (m.playlist_toolbar_h - m.btn_md) // 2 - m.px(1)
    slot_w = (pl_w - m.px(20)) // len(tb_buttons)
    for idx, (slug, bmp, act, tip) in enumerate(tb_buttons):
        bx = m.px(8) + idx * slot_w + (slot_w - m.btn_md) // 2
        _el(
            toolbar,
            "Button",
            id=f"pl_btn_{slug}",
            x=bx,
            y=tb_btn_y,
            up=f"{bmp}_up",
            over=f"{bmp}_over",
            down=f"{bmp}_down",
            action=act,
            tooltiptext=tip,
            help=tip,
        )

    _el(
        sheet,
        "Image",
        id="pl_divider_left",
        x=0,
        y=0,
        width=m.border,
        height=pl_h,
        image="divider_v",
        resize="scale",
        lefttop="lefttop",
        rightbottom="leftbottom",
    )


def _add_compact_layout(
    main_win: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
) -> None:
    """Build the Compact Mini-Player layout (`main_compact`) on `surface_container`."""
    c = tokens.colors
    cw, ch = m.compact_w, m.compact_h

    layout = _el(
        main_win,
        "Layout",
        id="main_compact",
        width=cw,
        height=ch,
        minwidth=m.compact_min_w,
        maxwidth=m.compact_max_w,
        minheight=ch,
        maxheight=ch,
    )

    _el(
        layout,
        "Image",
        id="compact_bg",
        x=0,
        y=0,
        width=cw,
        height=ch,
        image="bg_compact",
        resize="scale",
        action="move",
        action2="main.setLayout(main_normal)",
        lefttop="lefttop",
        rightbottom="rightbottom",
    )

    art_pad = (ch - m.compact_art) // 2
    _el(
        layout,
        "Image",
        id="compact_art",
        x=art_pad,
        y=art_pad,
        width=m.compact_art,
        height=m.compact_art,
        image="art_placeholder_compact",
        art="true",
        resize="scale2",
        action2="dialogs.fileInfo()",
        help="Double-click for Media Information",
    )

    col_x = art_pad + m.compact_art + m.px(12)
    col_right_pad = m.px(10)
    top_y = m.px(8)
    gap = m.px(2)
    win_btns_w = 3 * m.btn_sm + 2 * gap

    _el(
        layout,
        "Text",
        id="compact_title",
        x=col_x,
        y=_ft2_text_y(top_y, m.btn_sm, tokens.typography.title_small.size),
        width=max(m.px(100), cw - col_x - win_btns_w - col_right_pad - m.px(8)),
        lefttop="lefttop",
        rightbottom="righttop",
        text="$N",
        font=tokens.typography.title_small.id,
        color=c.on_surface,
        alignment="left",
        scrolling="auto",
    )

    rx = cw - col_right_pad - win_btns_w
    _el(
        layout,
        "Checkbox",
        id="compact_aot",
        x=rx,
        y=top_y,
        lefttop="righttop",
        rightbottom="righttop",
        state="vlc.isOnTop",
        up1="btn_c_pin_off_up",
        over1="btn_c_pin_off_over",
        down1="btn_c_pin_off_down",
        up2="btn_c_pin_on_up",
        over2="btn_c_pin_on_over",
        down2="btn_c_pin_on_down",
        action1="vlc.onTop()",
        action2="vlc.onTop()",
        tooltiptext1="Pin Always on Top",
        tooltiptext2="Unpin Always on Top",
    )
    rx += m.btn_sm + gap
    _el(
        layout,
        "Button",
        id="compact_expand",
        x=rx,
        y=top_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_expand_up",
        over="btn_expand_over",
        down="btn_expand_down",
        action="main.setLayout(main_normal)",
        tooltiptext="Expand to Full Player",
        help="Return to Full Player",
    )
    rx += m.btn_sm + gap
    _el(
        layout,
        "Button",
        id="compact_close",
        x=rx,
        y=top_y,
        lefttop="righttop",
        rightbottom="righttop",
        up="btn_close_mid_up",
        over="btn_close_mid_over",
        down="btn_close_mid_down",
        action="vlc.quit()",
        tooltiptext="Quit VLC",
    )

    # Row 2: Compact Seek Bar + Timestamps (no width/height on Slider!)
    seek_row_y = m.px(46)
    t_w = m.px(40)
    t_y = _ft2_text_y(seek_row_y, m.seek_h, tokens.typography.label_small.size)
    seek_x = col_x + t_w + m.px(8)
    seek_w = cw - seek_x - t_w - col_right_pad - m.px(8)
    seek_mid = m.seek_h // 2

    _el(
        layout,
        "Text",
        id="compact_time_cur",
        x=col_x,
        y=t_y,
        width=t_w,
        text="$t",
        font=tokens.typography.label_small.id,
        color=c.on_surface_variant,
        alignment="right",
        visible="not vlc.isStopped",
    )
    c_seek = _el(
        layout,
        "Slider",
        id="compact_seek",
        x=seek_x,
        y=seek_row_y,
        lefttop="lefttop",
        rightbottom="righttop",
        points=f"(0,{seek_mid}),({seek_w - 1},{seek_mid})",
        thickness=m.seek_h // 2,
        value="time",
        up="handle_seek_up",
        over="handle_seek_over",
        down="handle_seek_down",
        tooltiptext="$t / $d",
    )
    _el(
        c_seek,
        "SliderBackground",
        id="compact_seek_bg",
        image="slider_seek_compact",
        nbvert=100,
    )
    _el(
        layout,
        "Text",
        id="compact_time_tot",
        x=cw - col_right_pad - t_w,
        y=t_y,
        width=t_w,
        lefttop="righttop",
        rightbottom="righttop",
        text="$d",
        font=tokens.typography.label_small.id,
        color=c.on_surface_variant,
        alignment="left",
        visible="not vlc.isStopped",
    )

    # Row 3: Compact Transport + Mini Volume
    tr_y = m.px(82)
    c_btn_y = tr_y + (m.fab_compact_h - m.btn_sm) // 2
    tx = col_x
    _el(
        layout,
        "Checkbox",
        id="compact_shuffle",
        x=tx,
        y=c_btn_y,
        state="playlist.isRandom",
        up1="btn_c_shuffle_off_up",
        over1="btn_c_shuffle_off_over",
        down1="btn_c_shuffle_off_down",
        up2="btn_c_shuffle_on_up",
        over2="btn_c_shuffle_on_over",
        down2="btn_c_shuffle_on_down",
        action1="playlist.setRandom(true)",
        action2="playlist.setRandom(false)",
        tooltiptext1="Enable Shuffle",
        tooltiptext2="Disable Shuffle",
    )
    tx += m.btn_sm + gap
    _el(
        layout,
        "Button",
        id="compact_prev",
        x=tx,
        y=c_btn_y,
        up="btn_c_prev_up",
        over="btn_c_prev_over",
        down="btn_c_prev_down",
        action="playlist.previous()",
        tooltiptext="Previous Track",
    )
    tx += m.btn_sm + m.px(6)
    _el(
        layout,
        "Checkbox",
        id="compact_playpause",
        x=tx,
        y=tr_y,
        state="vlc.isPlaying",
        up1="fab_compact_play_up",
        over1="fab_compact_play_over",
        down1="fab_compact_play_down",
        up2="fab_compact_pause_up",
        over2="fab_compact_pause_over",
        down2="fab_compact_pause_down",
        action1="vlc.play()",
        action2="vlc.pause()",
        tooltiptext1="Play",
        tooltiptext2="Pause",
    )
    tx += m.fab_compact_w + m.px(6)
    _el(
        layout,
        "Button",
        id="compact_next",
        x=tx,
        y=c_btn_y,
        up="btn_c_next_up",
        over="btn_c_next_over",
        down="btn_c_next_down",
        action="playlist.next()",
        tooltiptext="Next Track",
    )
    tx += m.btn_sm + gap
    _add_repeat_cycle(layout, "compact", tx, c_btn_y, compact=True)

    vol_blk_w = m.btn_sm + m.px(8) + m.vol_compact_w
    vx = cw - col_right_pad - vol_blk_w
    _el(
        layout,
        "Checkbox",
        id="compact_mute",
        x=vx,
        y=c_btn_y,
        lefttop="righttop",
        rightbottom="righttop",
        state="vlc.isMute",
        up1="btn_c_vol_up",
        over1="btn_c_vol_over",
        down1="btn_c_vol_down",
        up2="btn_c_mute_up",
        over2="btn_c_mute_over",
        down2="btn_c_mute_down",
        action1="vlc.mute()",
        action2="vlc.mute()",
        tooltiptext1="Mute ($V%)",
        tooltiptext2="Unmute",
    )
    c_vol_mid = m.vol_h // 2
    c_vol = _el(
        layout,
        "Slider",
        id="compact_volume",
        x=vx + m.btn_sm + m.px(8),
        y=tr_y + (m.fab_compact_h - m.vol_h) // 2,
        lefttop="righttop",
        rightbottom="righttop",
        points=f"(0,{c_vol_mid}),({m.vol_compact_w - 1},{c_vol_mid})",
        thickness=m.vol_h // 2,
        value="volume",
        up="handle_seek_up",
        over="handle_seek_over",
        down="handle_seek_down",
        tooltiptext="Volume: $V%",
    )
    _el(
        c_vol,
        "SliderBackground",
        id="compact_volume_bg",
        image="slider_vol_compact",
        nbvert=48,
    )

    _add_window_borders_and_resize(
        layout, m, prefix="compact", win_w=cw, win_h=ch, east_mode="compact", allow_v_resize=False
    )


def _add_equalizer_window(root: etree._Element, m: SkinMetrics) -> None:
    """Build the standalone Material 3 10-band Equalizer window (`eqwin`)."""
    eq_win = _el(root, "Window", id="eqwin", visible="false", position="Center")
    layout = _el(
        eq_win,
        "Layout",
        id="eq_main",
        width=m.eq_w,
        height=m.eq_h,
        minwidth=m.eq_w,
        maxwidth=m.eq_w,
        minheight=m.eq_h,
        maxheight=m.eq_h,
    )

    _el(layout, "Image", id="eq_bg_img", x=0, y=0, image="bg_eq", action="move")

    sw_x = m.eq_w - m.btn_sm - m.switch_w - m.px(20)
    sw_y = (m.eq_header_h - m.switch_h) // 2
    _el(
        layout,
        "Checkbox",
        id="eq_enable_switch",
        x=sw_x,
        y=sw_y,
        state="equalizer.isEnabled",
        up1="switch_off_up",
        over1="switch_off_over",
        down1="switch_off_down",
        up2="switch_on_up",
        over2="switch_on_over",
        down2="switch_on_down",
        action1="equalizer.enable()",
        action2="equalizer.disable()",
        tooltiptext1="Enable Equalizer",
        tooltiptext2="Disable Equalizer",
        help="Toggle Equalizer",
    )

    _el(
        layout,
        "Button",
        id="eq_close",
        x=m.eq_w - m.btn_sm - m.px(8),
        y=(m.eq_header_h - m.btn_sm) // 2,
        up="btn_close_low_up",
        over="btn_close_low_over",
        down="btn_close_low_down",
        action="eqwin.hide()",
        tooltiptext="Close Equalizer",
    )

    slider_top = m.eq_header_h + m.px(24)
    preamp_cx = m.px(52)
    band0_cx = m.px(108)
    band_step = m.px(36)
    centers = [preamp_cx] + [band0_cx + i * band_step for i in range(10)]
    values = ["equalizer.preamp"] + [f"equalizer.band({i})" for i in range(10)]
    tooltips = ["Preamp (dB)"] + [f"{lbl} Hz" for lbl in EQ_BAND_LABELS[1:]]

    pad_y = m.px(6)
    mid_x = m.eq_slider_w // 2
    for idx, (cx, val_name, tip) in enumerate(zip(centers, values, tooltips, strict=True)):
        sx = cx - m.eq_slider_w // 2
        # Omit width/height so VLC Bezier keeps factorX=1.0, factorY=1.0!
        sl = _el(
            layout,
            "Slider",
            id=f"eq_slider_{idx}",
            x=sx,
            y=slider_top,
            points=f"({mid_x},{m.eq_slider_h - pad_y}),({mid_x},{pad_y})",
            thickness=m.eq_slider_w // 2,
            value=val_name,
            up="handle_eq_up",
            over="handle_eq_over",
            down="handle_eq_down",
            tooltiptext=tip,
            help=tip,
        )
        _el(
            sl,
            "SliderBackground",
            id=f"eq_slider_bg_{idx}",
            image="slider_eq_band",
            nbhoriz=41,
            nbvert=1,
        )


def _add_fullscreen_controller(
    root: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
) -> None:
    """Build the South-anchored floating Material 3 Fullscreen Controller HUD (`surface_container_high`)."""
    c = tokens.colors
    fw, fh = m.fs_w, m.fs_h

    fs_win = _el(
        root,
        "Window",
        id="fullscreenController",
        position="South",
        ymargin="3%",
    )
    layout = _el(
        fs_win,
        "Layout",
        id="fs_hud",
        width=fw,
        height=fh,
        minwidth=fw,
        maxwidth=fw,
        minheight=fh,
        maxheight=fh,
    )

    _el(layout, "Image", id="fs_bg_img", x=0, y=0, image="bg_fs", action="move")

    # Row 1: Timestamps + Wide Seek Slider (no width/height on Slider!)
    time_pad = m.px(68)
    time_w = m.px(48)
    seek_y = m.px(8)
    time_y = _ft2_text_y(seek_y, m.seek_h, tokens.typography.label_medium.size)
    seek_mid = m.seek_h // 2

    _el(
        layout,
        "Text",
        id="fs_time_cur",
        x=m.px(10),
        y=time_y,
        width=time_w,
        text="$t",
        font=tokens.typography.label_medium.id,
        color=c.on_surface_variant,
        alignment="right",
        visible="not vlc.isStopped",
    )
    fs_seek = _el(
        layout,
        "Slider",
        id="fs_seek",
        x=time_pad,
        y=seek_y,
        points=f"(0,{seek_mid}),({m.fs_seek_w - 1},{seek_mid})",
        thickness=m.seek_h // 2,
        value="time",
        up="handle_fs_up",
        over="handle_fs_over",
        down="handle_fs_down",
        tooltiptext="$t / $d",
    )
    _el(
        fs_seek,
        "SliderBackground",
        id="fs_seek_bg",
        image="slider_seek_fs",
        nbvert=160,
    )
    _el(
        layout,
        "Text",
        id="fs_time_tot",
        x=fw - m.px(58),
        y=time_y,
        width=time_w,
        text="$d",
        font=tokens.typography.label_medium.id,
        color=c.on_surface_variant,
        alignment="left",
        visible="not vlc.isStopped",
    )

    # Row 2: Left (Audio/Subtitles + Title) | Center (Transport) | Right (Volume + Snapshot + Exit FS)
    row2_y = m.px(36)
    row2_h = fh - row2_y - m.px(4)
    btn_y = row2_y + (row2_h - m.btn_md) // 2
    fab_y = row2_y + (row2_h - m.fab_h) // 2
    gap = m.px(4)

    lx = m.px(14)
    _el(
        layout,
        "Button",
        id="fs_audio",
        x=lx,
        y=btn_y,
        up="btn_fs_audio_up",
        over="btn_fs_audio_over",
        down="btn_fs_audio_down",
        action="dialogs.audioPopup()",
        tooltiptext="Audio Tracks & Device",
    )
    lx += m.btn_md + gap
    _el(
        layout,
        "Button",
        id="fs_subs",
        x=lx,
        y=btn_y,
        up="btn_fs_subs_up",
        over="btn_fs_subs_over",
        down="btn_fs_subs_down",
        action="dialogs.videoPopup()",
        tooltiptext="Video & Subtitles",
    )
    lx += m.btn_md + m.px(8)
    _el(
        layout,
        "Text",
        id="fs_title",
        x=lx,
        y=_ft2_text_y(row2_y, row2_h, tokens.typography.body_small.size),
        width=m.px(160),
        text="$N",
        font=tokens.typography.body_small.id,
        color=c.on_surface,
        alignment="left",
        scrolling="auto",
    )

    fab_gap = m.px(8)
    center_w = 4 * m.btn_md + m.fab_w + 2 * gap + 2 * fab_gap
    cx = (fw - center_w) // 2
    _el(
        layout,
        "Button",
        id="fs_slower",
        x=cx,
        y=btn_y,
        up="btn_fs_slower_up",
        over="btn_fs_slower_over",
        down="btn_fs_slower_down",
        action="vlc.slower()",
        tooltiptext="Play Slower ($R)",
    )
    cx += m.btn_md + gap
    _el(
        layout,
        "Button",
        id="fs_prev",
        x=cx,
        y=btn_y,
        up="btn_fs_prev_up",
        over="btn_fs_prev_over",
        down="btn_fs_prev_down",
        action="playlist.previous()",
        tooltiptext="Previous Track",
    )
    cx += m.btn_md + fab_gap
    _el(
        layout,
        "Checkbox",
        id="fs_playpause",
        x=cx,
        y=fab_y,
        state="vlc.isPlaying",
        up1="fab_fs_play_up",
        over1="fab_fs_play_over",
        down1="fab_fs_play_down",
        up2="fab_fs_pause_up",
        over2="fab_fs_pause_over",
        down2="fab_fs_pause_down",
        action1="vlc.play()",
        action2="vlc.pause()",
        tooltiptext1="Play",
        tooltiptext2="Pause",
    )
    cx += m.fab_w + fab_gap
    _el(
        layout,
        "Button",
        id="fs_next",
        x=cx,
        y=btn_y,
        up="btn_fs_next_up",
        over="btn_fs_next_over",
        down="btn_fs_next_down",
        action="playlist.next()",
        tooltiptext="Next Track",
    )
    cx += m.btn_md + gap
    _el(
        layout,
        "Button",
        id="fs_faster",
        x=cx,
        y=btn_y,
        up="btn_fs_faster_up",
        over="btn_fs_faster_over",
        down="btn_fs_faster_down",
        action="vlc.faster()",
        tooltiptext="Play Faster ($R)",
    )

    right_w = 3 * m.btn_md + m.vol_w + m.px(24)
    rx = fw - right_w - m.px(14)
    _el(
        layout,
        "Checkbox",
        id="fs_mute",
        x=rx,
        y=btn_y,
        state="vlc.isMute",
        up1="btn_fs_vol_up",
        over1="btn_fs_vol_over",
        down1="btn_fs_vol_down",
        up2="btn_fs_mute_up",
        over2="btn_fs_mute_over",
        down2="btn_fs_mute_down",
        action1="vlc.mute()",
        action2="vlc.mute()",
        tooltiptext1="Mute ($V%)",
        tooltiptext2="Unmute",
    )
    rx += m.btn_md + m.px(8)
    vol_mid = m.vol_h // 2
    fs_vol = _el(
        layout,
        "Slider",
        id="fs_volume",
        x=rx,
        y=row2_y + (row2_h - m.vol_h) // 2,
        points=f"(0,{vol_mid}),({m.vol_w - 1},{vol_mid})",
        thickness=m.vol_h // 2,
        value="volume",
        up="handle_fs_up",
        over="handle_fs_over",
        down="handle_fs_down",
        tooltiptext="Volume: $V%",
    )
    _el(
        fs_vol,
        "SliderBackground",
        id="fs_volume_bg",
        image="slider_vol_fs",
        nbvert=60,
    )
    rx += m.vol_w + m.px(12)
    _el(
        layout,
        "Button",
        id="fs_snapshot",
        x=rx,
        y=btn_y,
        up="btn_fs_snap_up",
        over="btn_fs_snap_over",
        down="btn_fs_snap_down",
        action="vlc.snapshot()",
        tooltiptext="Take Video Snapshot",
    )
    rx += m.btn_md + m.px(4)
    _el(
        layout,
        "Button",
        id="fs_exit",
        x=rx,
        y=btn_y,
        up="btn_fs_exit_up",
        over="btn_fs_exit_over",
        down="btn_fs_exit_down",
        action="vlc.fullscreen()",
        tooltiptext="Exit Fullscreen",
    )


def _add_tools_window(
    root: etree._Element,
    tokens: DesignTokens,
    m: SkinMetrics,
) -> None:
    """Build the Material 3 Control Center (`toolswin`) with 3 elevated quick-settings cards."""
    c = tokens.colors
    w, h = m.tools_w, m.tools_h
    hh = m.tools_header_h
    fh = m.tools_footer_h

    win = _el(root, "Window", id="toolswin", visible="false", position="Center")
    layout = _el(
        win,
        "Layout",
        id="tools_main",
        width=w,
        height=h,
        minwidth=w,
        maxwidth=w,
        minheight=h,
        maxheight=h,
    )

    _el(layout, "Image", id="tools_bg_img", x=0, y=0, image="bg_tools", action="move")

    _el(
        layout,
        "Button",
        id="tools_close",
        x=w - m.btn_sm - m.px(8),
        y=(hh - m.btn_sm) // 2,
        up="btn_close_low_up",
        over="btn_close_low_over",
        down="btn_close_low_down",
        action="toolswin.hide()",
        tooltiptext="Close Control Center",
    )

    card_x = m.px(14)
    card_w = w - 2 * card_x
    card_h = m.px(68)
    card_gap = m.px(10)
    y1 = hh + m.px(12)
    y2 = y1 + card_h + card_gap
    y3 = y2 + card_h + card_gap

    # Live speed readout on Card 1 header right
    _el(
        layout,
        "Text",
        id="tools_speed_val",
        x=card_x + card_w - m.px(96),
        y=y1 + m.px(6),
        width=m.px(84),
        text="Speed $R",
        font=tokens.typography.label_medium.id,
        color=c.primary,
        alignment="right",
    )

    grid_x = card_x + m.px(10)
    slot_w = (card_w - m.px(20)) // 6

    def slot_x(idx: int) -> int:
        return grid_x + idx * slot_w + (slot_w - m.btn_md) // 2

    # Card 1: Playback & Capture
    r1_y = y1 + m.px(26)
    c1_btns = [
        ("slower", "btn_fs_slower", "vlc.slower()", "Play Slower ($R)"),
        ("faster", "btn_fs_faster", "vlc.faster()", "Play Faster ($R)"),
        ("step", "btn_t_step", "vlc.nextFrame()", "Next Video Frame"),
        ("snap", "btn_fs_snap", "vlc.snapshot()", "Take Video Snapshot"),
    ]
    for idx, (slug, bmp, act, tip) in enumerate(c1_btns):
        _el(
            layout,
            "Button",
            id=f"tools_{slug}",
            x=slot_x(idx),
            y=r1_y,
            up=f"{bmp}_up",
            over=f"{bmp}_over",
            down=f"{bmp}_down",
            action=act,
            tooltiptext=tip,
            help=tip,
        )
    _el(
        layout,
        "Checkbox",
        id="tools_record",
        x=slot_x(4),
        y=r1_y,
        state="vlc.isRecording",
        up1="btn_t_rec_off_up",
        over1="btn_t_rec_off_over",
        down1="btn_t_rec_off_down",
        up2="btn_t_rec_on_up",
        over2="btn_t_rec_on_over",
        down2="btn_t_rec_on_down",
        action1="vlc.toggleRecord()",
        action2="vlc.toggleRecord()",
        tooltiptext1="Start Recording",
        tooltiptext2="Stop Recording",
        help="Toggle Stream Recording",
    )
    _el(
        layout,
        "Button",
        id="tools_misc",
        x=slot_x(5),
        y=r1_y,
        up="btn_t_menu_up",
        over="btn_t_menu_over",
        down="btn_t_menu_down",
        action="dialogs.miscPopup()",
        tooltiptext="Tools, Bookmarks & Extensions",
        help="Open VLC Tools & Misc Menu",
    )

    # Card 2: Media, Tracks & Streams
    r2_y = y2 + m.px(26)
    c2_btns = [
        ("folder", "btn_t_folder", "dialogs.directory()", "Open Folder..."),
        ("net", "btn_t_net", "dialogs.net()", "Open Network Stream..."),
        ("cast", "btn_t_cast", "dialogs.streamingWizard()", "Convert / Stream Wizard..."),
        ("audio", "btn_fs_audio", "dialogs.audioPopup()", "Audio Tracks & Device"),
        ("subs", "btn_fs_subs", "dialogs.videoPopup()", "Video, Crop & Subtitles"),
        ("info", "btn_t_info", "dialogs.fileInfo()", "Media Information & Codecs"),
    ]
    for idx, (slug, bmp, act, tip) in enumerate(c2_btns):
        _el(
            layout,
            "Button",
            id=f"tools_{slug}",
            x=slot_x(idx),
            y=r2_y,
            up=f"{bmp}_up",
            over=f"{bmp}_over",
            down=f"{bmp}_down",
            action=act,
            tooltiptext=tip,
            help=tip,
        )

    # Card 3: Appearance, Tools & VLC
    r3_y = y3 + m.px(26)
    c3_btns = [
        ("eq", "btn_t_eq", "eqwin.show()", "Open Equalizer"),
        ("mini", "btn_t_mini", "main.setLayout(main_compact)", "Compact Mini-Player"),
        ("palette", "btn_t_palette", "dialogs.changeSkin()", "Switch Theme / Color Palette..."),
        ("prefs", "btn_t_prefs", "dialogs.prefs()", "VLC Preferences..."),
        ("msgs", "btn_t_msgs", "dialogs.messages()", "Messages & Debug Log"),
        ("vlcmenu", "btn_t_menu", "dialogs.popup()", "Full Native VLC Menu"),
    ]
    for idx, (slug, bmp, act, tip) in enumerate(c3_btns):
        _el(
            layout,
            "Button",
            id=f"tools_{slug}",
            x=slot_x(idx),
            y=r3_y,
            up=f"{bmp}_up",
            over=f"{bmp}_over",
            down=f"{bmp}_down",
            action=act,
            tooltiptext=tip,
            help=tip,
        )

    # Footer live telemetry bar
    footer_y = h - fh
    _el(
        layout,
        "Text",
        id="tools_telemetry",
        x=m.px(14),
        y=_ft2_text_y(footer_y, fh, tokens.typography.label_small.size),
        width=w - m.px(28),
        text="Vol $V%  •  Speed $R  •  $B kbps  •  $S Hz",
        font=tokens.typography.label_small.id,
        color=c.on_surface_variant,
        alignment="center",
    )


def _add_about_window(root: etree._Element, m: SkinMetrics) -> None:
    """Build the Material 3 About Theme Dialog window (`aboutwin`)."""
    win = _el(root, "Window", id="aboutwin", visible="false", position="Center")
    layout = _el(
        win,
        "Layout",
        id="about_main",
        width=m.about_w,
        height=m.about_h,
        minwidth=m.about_w,
        maxwidth=m.about_w,
        minheight=m.about_h,
        maxheight=m.about_h,
    )
    _el(
        layout,
        "Image",
        id="about_bg_img",
        x=0,
        y=0,
        image="bg_about",
        action="move",
        action2="aboutwin.hide()",
    )
    _el(
        layout,
        "Button",
        id="about_close",
        x=m.about_w - m.btn_sm - m.px(10),
        y=m.px(10),
        up="btn_close_high_up",
        over="btn_close_high_over",
        down="btn_close_high_down",
        action="aboutwin.hide()",
        tooltiptext="Close",
    )


def _add_popup_menu(root: etree._Element) -> None:
    """Build the enriched Material 3 Quick Actions `<PopupMenu id="m3_menu">`."""
    menu = _el(root, "PopupMenu", id="m3_menu")

    def item(label: str, action: str) -> None:
        _el(menu, "MenuItem", label=label, action=action)

    def sep() -> None:
        _el(menu, "MenuSeparator")

    item("Open File...", "dialogs.file()")
    item("Quick Open File...", "dialogs.fileSimple()")
    item("Open Folder...", "dialogs.directory()")
    item("Open Network Stream...", "dialogs.net()")
    item("Open Disc...", "dialogs.disc()")
    item("Convert / Stream Wizard...", "dialogs.streamingWizard()")
    sep()
    item("Audio Tracks & Devices", "dialogs.audioPopup()")
    item("Video, Aspect Ratio & Subtitles", "dialogs.videoPopup()")
    item("Tools, Bookmarks & Extensions", "dialogs.miscPopup()")
    item("Full Native VLC Menu", "dialogs.popup()")
    sep()
    item("Play Faster (+)", "vlc.faster()")
    item("Play Slower (-)", "vlc.slower()")
    item("Next Video Frame", "vlc.nextFrame()")
    item("Take Video Snapshot", "vlc.snapshot()")
    item("Toggle Recording", "vlc.toggleRecord()")
    sep()
    item("Control Center (Quick Tools)", "toolswin.show()")
    item("Equalizer", "eqwin.show()")
    item("Playlist Side Sheet", "main.setLayout(main_playlist)")
    item("Compact Mini-Player", "main.setLayout(main_compact)")
    item("Standard Player", "main.setLayout(main_normal)")
    item("Always on Top", "vlc.onTop()")
    sep()
    item("Switch Theme / Palette...", "dialogs.changeSkin()")
    item("Media Information & Codecs", "dialogs.fileInfo()")
    item("Messages & Debug Console", "dialogs.messages()")
    item("Preferences...", "dialogs.prefs()")
    sep()
    item("About Material 3 Skin", "aboutwin.show()")

    # Dedicated Audio Menu (used when VLC is stopped/idle, since dialogs.audioPopup() requires active media)
    audio_menu = _el(root, "PopupMenu", id="m3_audio_menu")
    _el(audio_menu, "MenuItem", label="Open Audio / Media File...", action="dialogs.file()")
    _el(audio_menu, "MenuSeparator")
    _el(audio_menu, "MenuItem", label="Open Equalizer", action="eqwin.show()")
    _el(audio_menu, "MenuItem", label="Volume Up", action="vlc.volumeUp()")
    _el(audio_menu, "MenuItem", label="Volume Down", action="vlc.volumeDown()")
    _el(audio_menu, "MenuItem", label="Toggle Mute", action="vlc.mute()")
    _el(audio_menu, "MenuSeparator")
    _el(audio_menu, "MenuItem", label="Audio Device & Preferences...", action="dialogs.prefs()")
    _el(audio_menu, "MenuItem", label="Full VLC Menu", action="dialogs.popup()")

    # Dedicated Video/Display Menu (used when VLC is stopped/idle, since dialogs.videoPopup() requires active media)
    video_menu = _el(root, "PopupMenu", id="m3_video_menu")
    _el(video_menu, "MenuItem", label="Open Video File...", action="dialogs.file()")
    _el(video_menu, "MenuItem", label="Open Network Stream...", action="dialogs.net()")
    _el(video_menu, "MenuSeparator")
    _el(video_menu, "MenuItem", label="Toggle Fullscreen", action="vlc.fullscreen()")
    _el(video_menu, "MenuItem", label="Toggle Always on Top", action="vlc.onTop()")
    _el(video_menu, "MenuItem", label="Switch Theme / Palette...", action="dialogs.changeSkin()")
    _el(video_menu, "MenuSeparator")
    _el(video_menu, "MenuItem", label="Video & Subtitles Preferences...", action="dialogs.prefs()")
    _el(video_menu, "MenuItem", label="Full VLC Menu", action="dialogs.popup()")


def build_theme_xml(
    tokens: DesignTokens,
    metrics: SkinMetrics,
    bitmaps: list[BitmapSpec],
) -> bytes:
    """Build the complete, pretty-printed, DTD-compliant `theme.xml` document."""
    cfg = tokens.config
    # IMPORTANT: VLC Builder calls addTheme() BEFORE addFont(), so tooltipfont MUST be "defaultfont"
    root = etree.Element(
        "Theme",
        version="2.0",
        tooltipfont="defaultfont",
        magnet="15",
        alpha="255",
        movealpha="230",
    )

    _el(
        root,
        "ThemeInfo",
        name=cfg.name,
        author=cfg.author,
        email=cfg.email,
        webpage=cfg.webpage,
    )

    for font in tokens.typography.all_fonts():
        _el(root, "Font", id=font.id, file=font.file, size=font.size)

    for bmp in bitmaps:
        bmp_el = _el(root, "Bitmap", id=bmp.id, file=bmp.file, alphacolor="#FF00FF")
        for sub in bmp.subbitmaps:
            _el(
                bmp_el,
                "SubBitmap",
                id=sub.id,
                x=sub.x,
                y=sub.y,
                width=sub.width,
                height=sub.height,
            )

    _add_popup_menu(root)

    main_win = _el(
        root,
        "Window",
        id="main",
        visible="true",
        position="Center",
        dragdrop="true",
        playondrop="true",
    )

    _add_compact_layout(main_win, tokens, metrics)

    pl_layout = _el(
        main_win,
        "Layout",
        id="main_playlist",
        width=metrics.main_pl_w,
        height=metrics.main_h,
        minwidth=metrics.main_pl_min_w,
        maxwidth=99999,
        minheight=metrics.main_min_h,
        maxheight=99999,
    )
    main_pl_host = _el(
        pl_layout,
        "Panel",
        id="pl_main_host",
        x=0,
        y=0,
        width=metrics.main_w,
        height=metrics.main_h,
        lefttop="lefttop",
        rightbottom="rightbottom",
    )
    _add_main_topbar(main_pl_host, tokens, metrics, prefix="pl", bar_w=metrics.main_w)
    _add_main_stage(main_pl_host, tokens, metrics, prefix="pl", stage_w=metrics.main_w)
    _add_main_controls(
        main_pl_host, tokens, metrics, prefix="pl", bar_w=metrics.main_w, playlist_open=True
    )
    _add_playlist_side_sheet(pl_layout, tokens, metrics)
    _add_window_borders_and_resize(
        pl_layout,
        metrics,
        prefix="pl",
        win_w=metrics.main_pl_w,
        win_h=metrics.main_h,
        east_mode="playlist",
    )

    # Default Main Player layout (LAST layout => active on startup!)
    norm_layout = _el(
        main_win,
        "Layout",
        id="main_normal",
        width=metrics.main_w,
        height=metrics.main_h,
        minwidth=metrics.main_min_w,
        maxwidth=99999,
        minheight=metrics.main_min_h,
        maxheight=99999,
    )
    _add_main_topbar(norm_layout, tokens, metrics, prefix="norm", bar_w=metrics.main_w)
    _add_main_stage(norm_layout, tokens, metrics, prefix="norm", stage_w=metrics.main_w)
    _add_main_controls(
        norm_layout, tokens, metrics, prefix="norm", bar_w=metrics.main_w, playlist_open=False
    )
    _add_window_borders_and_resize(
        norm_layout,
        metrics,
        prefix="norm",
        win_w=metrics.main_w,
        win_h=metrics.main_h,
        east_mode="stage",
    )

    _add_equalizer_window(root, metrics)
    _add_tools_window(root, tokens, metrics)
    _add_fullscreen_controller(root, tokens, metrics)
    _add_about_window(root, metrics)

    xml_bytes: bytes = etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        doctype=DOCTYPE_DECL,
        pretty_print=True,
    )
    return xml_bytes
