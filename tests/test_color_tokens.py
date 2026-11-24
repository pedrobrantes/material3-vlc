"""Tests for Material 3 HCT color token engine, WCAG contrast, and wallpaper extraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from material3_vlc.tokens.color import (
    blend_over,
    contrast_ratio,
    extract_seed_from_image,
    generate_color_roles,
    normalize_hex,
)
from material3_vlc.tokens.dynamic import decode_windows_abgr
from material3_vlc.tokens.presets import CURATED_PRESETS
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig


def test_decode_windows_abgr() -> None:
    # 0xFFBBGGRR -> R=0x48, G=0x55, B=0x79 => #485579
    assert decode_windows_abgr(0xFF795548) == "#485579"
    assert decode_windows_abgr(0xFF0088FF) == "#FF8800"


def test_normalize_hex() -> None:
    assert normalize_hex("#6750a4") == "#6750A4"
    assert normalize_hex("1a73e8") == "#1A73E8"
    with pytest.raises(ValueError):
        normalize_hex("#XYZ")


def test_blend_over() -> None:
    assert blend_over("#000000", "#FFFFFF", 0.0) == "#000000"
    assert blend_over("#000000", "#FFFFFF", 1.0) == "#FFFFFF"
    mid = blend_over("#000000", "#FFFFFF", 0.5)
    assert mid in ("#7F7F7F", "#808080")


@pytest.mark.parametrize("preset", CURATED_PRESETS, ids=lambda p: p.slug)
def test_all_curated_presets_meet_wcag_aa(preset) -> None:  # type: ignore[no-untyped-def]
    tokens = DesignTokens.from_config(ThemeConfig.from_preset(preset.slug))
    c = tokens.colors

    # Core text & primary action contrast must exceed WCAG AA (4.5:1)
    assert contrast_ratio(c.on_primary, c.primary) >= 4.5
    assert contrast_ratio(c.on_surface, c.surface_container) >= 7.0
    assert contrast_ratio(c.on_surface, c.surface_container_low) >= 7.0
    assert contrast_ratio(c.on_surface_variant, c.surface_container) >= 4.5
    assert contrast_ratio(c.on_secondary_container, c.secondary_container) >= 4.5
    assert contrast_ratio(c.primary, c.surface_container) >= 3.0


def test_amoled_pure_black_canvas() -> None:
    roles = generate_color_roles("#6750A4", mode="amoled", scheme="tonal-spot")
    assert roles.surface == "#000000"
    assert roles.surface_container_lowest == "#000000"
    assert roles.media_stage == "#000000"
    # Tonal elevation surfaces remain distinct from pure black
    assert roles.surface_container != "#000000"
    assert roles.surface_container_high != roles.surface_container


def test_high_contrast_increases_legibility() -> None:
    std = generate_color_roles("#1A73E8", mode="dark", contrast=0.0)
    high = generate_color_roles("#1A73E8", mode="dark", contrast=1.0)
    assert contrast_ratio(high.on_primary, high.primary) > contrast_ratio(
        std.on_primary, std.primary
    )


def test_wallpaper_seed_extraction(tmp_path: Path) -> None:
    wallpaper = tmp_path / "sunset.png"
    img = Image.new("RGB", (64, 64), (240, 120, 30))
    img.save(wallpaper)
    seed = extract_seed_from_image(wallpaper)
    assert seed.startswith("#") and len(seed) == 7
