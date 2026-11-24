"""Tests for SVG rendering, Material Symbols loading, sliders, and sprite packing."""

from __future__ import annotations

from pathlib import Path

from material3_vlc.render.icons import render_icon_button, render_m3_switch, render_play_pause_fab
from material3_vlc.render.sliders import (
    render_eq_slider_strip,
    render_horizontal_slider_handle,
    render_horizontal_slider_strip,
)
from material3_vlc.render.sprites import render_all_skin_assets
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig


def test_icon_button_states_differ() -> None:
    tokens = DesignTokens.from_config(ThemeConfig.from_preset("m3-baseline-dark"))
    bg = tokens.colors.surface_container_low
    up = render_icon_button(tokens, "menu", 32, 18, surface_bg=bg, variant="standard", state="up")
    over = render_icon_button(tokens, "menu", 32, 18, surface_bg=bg, variant="standard", state="over")
    down = render_icon_button(tokens, "menu", 32, 18, surface_bg=bg, variant="standard", state="down")
    assert up.size == (32, 32)
    # Every pixel must be fully opaque (alpha=255) for zero-serrilhado Win32 BitBlt!
    assert min(p[3] for p in up.get_flattened_data()) == 255
    assert min(p[3] for p in over.get_flattened_data()) == 255
    assert min(p[3] for p in down.get_flattened_data()) == 255
    assert up.tobytes() != over.tobytes()
    assert over.tobytes() != down.tobytes()


def test_play_pause_fab_expressive_morph() -> None:
    tokens = DesignTokens.from_config(ThemeConfig.from_preset("m3-vlc-orange-dark"))
    bg = tokens.colors.surface_container
    play = render_play_pause_fab(tokens, 56, 44, 24, surface_bg=bg, is_playing=False, state="up")
    pause = render_play_pause_fab(tokens, 56, 44, 24, surface_bg=bg, is_playing=True, state="up")
    assert play.size == (56, 44)
    assert pause.size == (56, 44)
    assert min(p[3] for p in play.get_flattened_data()) == 255
    assert min(p[3] for p in pause.get_flattened_data()) == 255
    assert play.tobytes() != pause.tobytes()


def test_switch_and_sliders_dimensions() -> None:
    tokens = DesignTokens.from_config(ThemeConfig.from_preset("m3-baseline-light"))
    metrics = SkinMetrics.for_scale(1.0)
    bg_low = tokens.colors.surface_container_low
    bg_mid = tokens.colors.surface_container

    sw_off = render_m3_switch(tokens, metrics, surface_bg=bg_low, checked=False, state="up")
    sw_on = render_m3_switch(tokens, metrics, surface_bg=bg_low, checked=True, state="up")
    assert sw_off.size == (metrics.switch_w, metrics.switch_h)
    assert sw_on.size == (metrics.switch_w, metrics.switch_h)
    assert min(p[3] for p in sw_on.get_flattened_data()) == 255

    h_strip = render_horizontal_slider_strip(tokens, 200, 24, 6, frames=20, surface_bg=bg_mid)
    assert h_strip.size == (200, 24 * 20)
    assert min(p[3] for p in h_strip.get_flattened_data()) == 255

    handle = render_horizontal_slider_handle(
        tokens, 14, 24, 6, surface_bg=bg_mid, state="down"
    )
    assert handle.size == (14, 24)
    assert min(p[3] for p in handle.get_flattened_data()) == 255

    eq_strip = render_eq_slider_strip(tokens, 26, 136, frames=41, surface_bg=bg_mid)
    assert eq_strip.size == (26 * 41, 136)
    assert min(p[3] for p in eq_strip.get_flattened_data()) == 255


def test_hidpi_asset_rendering(tmp_path: Path) -> None:
    cfg = ThemeConfig.from_preset("m3-ocean-dark", scale=2.0)
    tokens = DesignTokens.from_config(cfg)
    metrics = SkinMetrics.for_scale(2.0)
    bitmaps = render_all_skin_assets(tokens, metrics, tmp_path)
    assert len(bitmaps) >= 18
    assert (tmp_path / "ui_controls.png").is_file()
    assert (tmp_path / "bg_eq.png").is_file()
