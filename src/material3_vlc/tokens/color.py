"""Material 3 (HCT / Dynamic Color) color system engine.

Uses Google's official Material Color Utilities algorithms via `materialyoucolor`
to compute perceptually uniform, WCAG-compliant Material 3 color roles from any
seed hex color or wallpaper image.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_content import SchemeContent
from materialyoucolor.scheme.scheme_expressive import SchemeExpressive
from materialyoucolor.scheme.scheme_fidelity import SchemeFidelity
from materialyoucolor.scheme.scheme_fruit_salad import SchemeFruitSalad
from materialyoucolor.scheme.scheme_monochrome import SchemeMonochrome
from materialyoucolor.scheme.scheme_neutral import SchemeNeutral
from materialyoucolor.scheme.scheme_rainbow import SchemeRainbow
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.scheme.scheme_vibrant import SchemeVibrant
from materialyoucolor.score.score import Score, ScoreOptions
from PIL import Image

ThemeMode = Literal["dark", "light", "amoled"]
SchemeVariant = Literal[
    "tonal-spot",
    "expressive",
    "vibrant",
    "content",
    "fidelity",
    "monochrome",
    "neutral",
    "fruit-salad",
    "rainbow",
]
ContrastName = Literal["standard", "medium", "high"]

CONTRAST_LEVELS: dict[ContrastName, float] = {
    "standard": 0.0,
    "medium": 0.5,
    "high": 1.0,
}

_SCHEME_CLASSES: dict[SchemeVariant, type] = {
    "tonal-spot": SchemeTonalSpot,
    "expressive": SchemeExpressive,
    "vibrant": SchemeVibrant,
    "content": SchemeContent,
    "fidelity": SchemeFidelity,
    "monochrome": SchemeMonochrome,
    "neutral": SchemeNeutral,
    "fruit-salad": SchemeFruitSalad,
    "rainbow": SchemeRainbow,
}

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def normalize_hex(color: str) -> str:
    """Validate and normalize a 6-digit hex color string to `#RRGGBB`."""
    match = _HEX_RE.match(color.strip())
    if not match:
        raise ValueError(f"Invalid hex color '{color}'. Expected format '#RRGGBB'.")
    return f"#{match.group(1).upper()}"


def hex_to_argb(color: str) -> int:
    """Convert `#RRGGBB` to a 32-bit opaque ARGB integer."""
    norm = normalize_hex(color)
    return 0xFF000000 | int(norm[1:], 16)


def argb_to_hex(argb: int) -> str:
    """Convert a 32-bit ARGB integer to `#RRGGBB`."""
    return f"#{(argb & 0xFFFFFF):06X}"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert `#RRGGBB` to an `(r, g, b)` tuple in `0..255`."""
    norm = normalize_hex(color)
    val = int(norm[1:], 16)
    return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert `(r, g, b)` integers in `0..255` to `#RRGGBB`."""
    rc = max(0, min(255, r))
    gc = max(0, min(255, g))
    bc = max(0, min(255, b))
    return f"#{rc:02X}{gc:02X}{bc:02X}"


def blend_over(base_hex: str, overlay_hex: str, alpha: float) -> str:
    """Alpha-composite `overlay_hex` at `alpha` (`0..1`) on top of opaque `base_hex`.

    Implements the Material 3 state layer compositing formula:
    `out = overlay * alpha + base * (1 - alpha)`.
    """
    a = max(0.0, min(1.0, alpha))
    br, bg, bb = hex_to_rgb(base_hex)
    or_, og, ob = hex_to_rgb(overlay_hex)
    return rgb_to_hex(
        round(or_ * a + br * (1.0 - a)),
        round(og * a + bg * (1.0 - a)),
        round(ob * a + bb * (1.0 - a)),
    )


def relative_luminance(color_hex: str) -> float:
    """Compute WCAG 2.1 relative luminance in `[0.0, 1.0]`."""

    def linearize(channel: int) -> float:
        srgb = channel / 255.0
        return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

    r, g, b = hex_to_rgb(color_hex)
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors (range `1.0` to `21.0`)."""
    l1 = relative_luminance(fg_hex)
    l2 = relative_luminance(bg_hex)
    lighter, darker = (l1, l2) if l1 >= l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)


def extract_seed_from_image(image_path: str | Path, fallback: str = "#6750A4") -> str:
    """Extract the optimal Material You seed color from a wallpaper/image file.

    Uses `QuantizeCelebi` + `Score.score` when the native extension is available,
    falling back transparently to Pillow median-cut quantization + `Score.score`.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Wallpaper image not found: {path}")

    with Image.open(path) as img:
        rgb_img = img.convert("RGB")
        # Resize down for fast, consistent perceptual quantization (per Material guidelines)
        rgb_img.thumbnail((128, 128), Image.Resampling.LANCZOS)
        if hasattr(rgb_img, "get_flattened_data"):
            pixels = list(rgb_img.get_flattened_data())
        else:
            pixels = list(rgb_img.getdata())

    color_counts: dict[int, int] | None = None
    try:
        from materialyoucolor.quantize import QuantizeCelebi

        color_counts = dict(QuantizeCelebi(pixels, 128))
    except Exception:
        # Pure-Python fallback via Pillow quantization if libstdc++ is absent
        quantized = rgb_img.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette() or []
        hist = quantized.histogram()
        fallback_counts: dict[int, int] = {}
        for idx, count in enumerate(hist[:64]):
            if count > 0 and idx * 3 + 2 < len(palette):
                r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
                argb = 0xFF000000 | (r << 16) | (g << 8) | b
                fallback_counts[argb] = count
        color_counts = fallback_counts

    if not color_counts:
        return normalize_hex(fallback)

    options = ScoreOptions(desired=4, fallback_color_argb=hex_to_argb(fallback))
    scored = Score.score(color_counts, options)
    return argb_to_hex(scored[0]) if scored else normalize_hex(fallback)


@dataclass(frozen=True, slots=True)
class ColorRoles:
    """Complete Material 3 semantic color role palette (`#RRGGBB`)."""

    # Primary
    primary: str
    on_primary: str
    primary_container: str
    on_primary_container: str

    # Secondary
    secondary: str
    on_secondary: str
    secondary_container: str
    on_secondary_container: str

    # Tertiary
    tertiary: str
    on_tertiary: str
    tertiary_container: str
    on_tertiary_container: str

    # Error
    error: str
    on_error: str
    error_container: str
    on_error_container: str

    # Surfaces & Containers (5-tier M3 tonal elevation hierarchy)
    surface: str
    surface_dim: str
    surface_bright: str
    surface_container_lowest: str
    surface_container_low: str
    surface_container: str
    surface_container_high: str
    surface_container_highest: str
    on_surface: str
    on_surface_variant: str

    # Outlines & Inverse
    outline: str
    outline_variant: str
    inverse_surface: str
    inverse_on_surface: str
    inverse_primary: str
    scrim: str
    shadow: str

    # Derived semantic helpers for VLC Skins2 surfaces
    divider_subtle: str
    window_border: str
    media_stage: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def apply_color_overrides(
    roles: ColorRoles,
    overrides: dict[str, str],
    *,
    mode: ThemeMode = "dark",
) -> ColorRoles:
    """Apply user-supplied per-role hex overrides and recompute derived chrome roles."""
    if not overrides:
        return roles
    data = asdict(roles)
    valid_fields = set(data.keys())
    for key, val in overrides.items():
        if key not in valid_fields:
            raise ValueError(f"Unknown Material 3 color role '{key}'.")
        data[key] = normalize_hex(val)

    is_dark = mode in ("dark", "amoled")
    if "divider_subtle" not in overrides:
        data["divider_subtle"] = blend_over(
            data["surface_container"], data["outline_variant"], 0.45 if is_dark else 0.55
        )
    if "window_border" not in overrides:
        data["window_border"] = blend_over(
            data["surface_container"], data["outline_variant"], 0.65 if is_dark else 0.75
        )
    if "media_stage" not in overrides:
        data["media_stage"] = (
            "#000000" if mode == "amoled" else data["surface_container_lowest"]
        )
    return ColorRoles(**data)


def generate_color_roles(
    seed_hex: str,
    mode: ThemeMode = "dark",
    scheme: SchemeVariant = "tonal-spot",
    contrast: float = 0.0,
) -> ColorRoles:
    """Generate a full Material 3 `ColorRoles` palette using HCT math."""
    norm_seed = normalize_hex(seed_hex)
    if scheme not in _SCHEME_CLASSES:
        valid = ", ".join(_SCHEME_CLASSES)
        raise ValueError(f"Unsupported scheme '{scheme}'. Choose from: {valid}")
    if mode not in ("dark", "light", "amoled"):
        raise ValueError(f"Unsupported mode '{mode}'. Choose from: dark, light, amoled")

    is_dark = mode in ("dark", "amoled")
    clamped_contrast = max(-1.0, min(1.0, float(contrast)))

    hct = Hct.from_int(hex_to_argb(norm_seed))
    scheme_cls = _SCHEME_CLASSES[scheme]
    dyn = scheme_cls(hct, is_dark, clamped_contrast)
    mdc = MaterialDynamicColors()

    def role(attr: str) -> str:
        return argb_to_hex(getattr(mdc, attr).get_argb(dyn))

    surface = role("surface")
    surface_dim = role("surfaceDim")
    surface_bright = role("surfaceBright")
    sc_lowest = role("surfaceContainerLowest")
    sc_low = role("surfaceContainerLow")
    sc_default = role("surfaceContainer")
    sc_high = role("surfaceContainerHigh")
    sc_highest = role("surfaceContainerHighest")
    outline_variant = role("outlineVariant")

    if mode == "amoled":
        # Pure black OLED canvas while preserving tonal elevation step clarity
        surface = "#000000"
        surface_dim = "#000000"
        sc_lowest = "#000000"
        sc_low = blend_over("#000000", sc_low, 0.55)
        sc_default = blend_over("#000000", sc_default, 0.72)
        sc_high = blend_over("#000000", sc_high, 0.85)
        sc_highest = blend_over("#000000", sc_highest, 0.92)

    divider_subtle = blend_over(sc_default, outline_variant, 0.45 if is_dark else 0.55)
    window_border = blend_over(sc_default, outline_variant, 0.65 if is_dark else 0.75)
    media_stage = "#000000" if mode == "amoled" else sc_lowest

    return ColorRoles(
        primary=role("primary"),
        on_primary=role("onPrimary"),
        primary_container=role("primaryContainer"),
        on_primary_container=role("onPrimaryContainer"),
        secondary=role("secondary"),
        on_secondary=role("onSecondary"),
        secondary_container=role("secondaryContainer"),
        on_secondary_container=role("onSecondaryContainer"),
        tertiary=role("tertiary"),
        on_tertiary=role("onTertiary"),
        tertiary_container=role("tertiaryContainer"),
        on_tertiary_container=role("onTertiaryContainer"),
        error=role("error"),
        on_error=role("onError"),
        error_container=role("errorContainer"),
        on_error_container=role("onErrorContainer"),
        surface=surface,
        surface_dim=surface_dim,
        surface_bright=surface_bright,
        surface_container_lowest=sc_lowest,
        surface_container_low=sc_low,
        surface_container=sc_default,
        surface_container_high=sc_high,
        surface_container_highest=sc_highest,
        on_surface=role("onSurface"),
        on_surface_variant=role("onSurfaceVariant"),
        outline=role("outline"),
        outline_variant=outline_variant,
        inverse_surface=role("inverseSurface"),
        inverse_on_surface=role("inverseOnSurface"),
        inverse_primary=role("inversePrimary"),
        scrim=role("scrim"),
        shadow=role("shadow"),
        divider_subtle=divider_subtle,
        window_border=window_border,
        media_stage=media_stage,
    )
