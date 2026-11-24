"""Complete Material 3 Theme configuration and compiled DesignTokens bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from material3_vlc.tokens.color import (
    ColorRoles,
    SchemeVariant,
    ThemeMode,
    apply_color_overrides,
    extract_seed_from_image,
    generate_color_roles,
    normalize_hex,
)
from material3_vlc.tokens.elevation import (
    ELEVATION,
    STATE_LAYERS,
    ElevationTokens,
    StateLayerTokens,
)
from material3_vlc.tokens.presets import PRESET_BY_SLUG, PresetSpec
from material3_vlc.tokens.shape import ShapeTokens
from material3_vlc.tokens.typography import TypographyTokens


@dataclass(frozen=True, slots=True)
class ThemeConfig:
    """User-facing theme specification used to build a `.vlt` skin."""

    name: str
    slug: str
    seed: str = "#6750A4"
    mode: ThemeMode = "dark"
    scheme: SchemeVariant = "tonal-spot"
    contrast: float = 0.0
    scale: float = 1.0
    color_overrides: dict[str, str] = field(default_factory=dict)
    author: str = "Pedro Brantes & material3-vlc contributors"
    email: str = "58346706+PedroBrantes@users.noreply.github.com"
    webpage: str = "https://github.com/PedroBrantes/material3-vlc"

    def __post_init__(self) -> None:
        if self.scale <= 0 or self.scale > 4.0:
            raise ValueError(f"Scale must be in (0, 4.0], got {self.scale}")

    @classmethod
    def from_preset(cls, slug: str, scale: float = 1.0) -> ThemeConfig:
        if slug not in PRESET_BY_SLUG:
            available = ", ".join(PRESET_BY_SLUG)
            raise KeyError(f"Unknown preset '{slug}'. Available presets: {available}")
        preset: PresetSpec = PRESET_BY_SLUG[slug]
        scale_suffix = "" if abs(scale - 1.0) < 1e-6 else f"-{scale:g}x"
        name_suffix = "" if abs(scale - 1.0) < 1e-6 else f" ({scale:g}x)"
        return cls(
            name=f"{preset.display_name}{name_suffix}",
            slug=f"{preset.slug}{scale_suffix}",
            seed=preset.seed,
            mode=preset.mode,  # type: ignore[arg-type]
            scheme=preset.scheme,  # type: ignore[arg-type]
            contrast=preset.contrast,
            scale=scale,
        )

    @classmethod
    def from_wallpaper(
        cls,
        image_path: str | Path,
        *,
        name: str = "Material 3 Dynamic",
        slug: str = "m3-dynamic",
        mode: ThemeMode = "dark",
        scheme: SchemeVariant = "content",
        contrast: float = 0.0,
        scale: float = 1.0,
    ) -> ThemeConfig:
        seed = extract_seed_from_image(image_path)
        return cls(
            name=name,
            slug=slug,
            seed=seed,
            mode=mode,
            scheme=scheme,
            contrast=contrast,
            scale=scale,
        )


@dataclass(frozen=True, slots=True)
class DesignTokens:
    """Resolved Material 3 design tokens ready for rendering and XML emission."""

    config: ThemeConfig
    colors: ColorRoles
    shapes: ShapeTokens
    typography: TypographyTokens
    state_layers: StateLayerTokens = STATE_LAYERS
    elevation: ElevationTokens = ELEVATION

    @classmethod
    def from_config(cls, config: ThemeConfig) -> DesignTokens:
        colors = generate_color_roles(
            seed_hex=normalize_hex(config.seed),
            mode=config.mode,
            scheme=config.scheme,
            contrast=config.contrast,
        )
        if config.color_overrides:
            colors = apply_color_overrides(colors, config.color_overrides, mode=config.mode)
        return cls(
            config=config,
            colors=colors,
            shapes=ShapeTokens.for_scale(config.scale),
            typography=TypographyTokens.for_scale(config.scale),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": {
                "name": self.config.name,
                "slug": self.config.slug,
                "seed": normalize_hex(self.config.seed),
                "mode": self.config.mode,
                "scheme": self.config.scheme,
                "contrast": self.config.contrast,
                "scale": self.config.scale,
            },
            "color": self.colors.to_dict(),
            "shape": self.shapes.to_dict(),
            "typography": self.typography.to_dict(),
            "stateLayer": {
                "hover": self.state_layers.hover,
                "focus": self.state_layers.focus,
                "pressed": self.state_layers.pressed,
                "dragged": self.state_layers.dragged,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
