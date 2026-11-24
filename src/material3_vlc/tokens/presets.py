"""Curated Material 3 theme presets for releases and CLI builds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresetSpec:
    """Definition of a curated Material 3 skin preset."""

    slug: str
    display_name: str
    family: str
    seed: str
    mode: str  # "dark" | "light" | "amoled"
    scheme: str = "tonal-spot"
    contrast: float = 0.0
    description: str = ""


CURATED_PRESETS: tuple[PresetSpec, ...] = (
    PresetSpec(
        slug="m3-brown-dark",
        display_name="Material 3 Brown Dark",
        family="Brown",
        seed="#795548",
        mode="dark",
        scheme="tonal-spot",
        description="Brown dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-brown-light",
        display_name="Material 3 Brown Light",
        family="Brown",
        seed="#795548",
        mode="light",
        scheme="tonal-spot",
        description="Brown light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-purple-dark",
        display_name="Material 3 Purple Dark",
        family="Purple",
        seed="#6750A4",
        mode="dark",
        scheme="tonal-spot",
        description="Baseline purple dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-purple-light",
        display_name="Material 3 Purple Light",
        family="Purple",
        seed="#6750A4",
        mode="light",
        scheme="tonal-spot",
        description="Baseline purple light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-red-dark",
        display_name="Material 3 Red Dark",
        family="Red",
        seed="#D32F2F",
        mode="dark",
        scheme="tonal-spot",
        description="Red dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-red-light",
        display_name="Material 3 Red Light",
        family="Red",
        seed="#D32F2F",
        mode="light",
        scheme="tonal-spot",
        description="Red light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-blue-dark",
        display_name="Material 3 Blue Dark",
        family="Blue",
        seed="#1A73E8",
        mode="dark",
        scheme="tonal-spot",
        description="Blue dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-blue-light",
        display_name="Material 3 Blue Light",
        family="Blue",
        seed="#1A73E8",
        mode="light",
        scheme="tonal-spot",
        description="Blue light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-yellow-dark",
        display_name="Material 3 Yellow Dark",
        family="Yellow",
        seed="#C99700",
        mode="dark",
        scheme="tonal-spot",
        description="Yellow dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-yellow-light",
        display_name="Material 3 Yellow Light",
        family="Yellow",
        seed="#C99700",
        mode="light",
        scheme="tonal-spot",
        description="Yellow light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-green-dark",
        display_name="Material 3 Green Dark",
        family="Green",
        seed="#146C2E",
        mode="dark",
        scheme="tonal-spot",
        description="Green dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-green-light",
        display_name="Material 3 Green Light",
        family="Green",
        seed="#146C2E",
        mode="light",
        scheme="tonal-spot",
        description="Green light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-pink-dark",
        display_name="Material 3 Pink Dark",
        family="Pink",
        seed="#D81B60",
        mode="dark",
        scheme="tonal-spot",
        description="Pink dark (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-pink-light",
        display_name="Material 3 Pink Light",
        family="Pink",
        seed="#D81B60",
        mode="light",
        scheme="tonal-spot",
        description="Pink light (tonal-spot)",
    ),
    PresetSpec(
        slug="m3-orange-dark",
        display_name="Material 3 Orange Dark",
        family="Orange",
        seed="#FF8800",
        mode="dark",
        scheme="expressive",
        description="VLC orange dark (expressive)",
    ),
    PresetSpec(
        slug="m3-orange-light",
        display_name="Material 3 Orange Light",
        family="Orange",
        seed="#FF8800",
        mode="light",
        scheme="expressive",
        description="VLC orange light (expressive)",
    ),
    PresetSpec(
        slug="m3-black-amoled",
        display_name="Material 3 Black AMOLED",
        family="Black",
        seed="#808080",
        mode="amoled",
        scheme="monochrome",
        description="Pure black OLED (monochrome)",
    ),
    PresetSpec(
        slug="m3-black-dark",
        display_name="Material 3 Black Dark",
        family="Black",
        seed="#808080",
        mode="dark",
        scheme="monochrome",
        description="Charcoal dark (monochrome)",
    ),
    PresetSpec(
        slug="m3-white-light",
        display_name="Material 3 White Light",
        family="White",
        seed="#808080",
        mode="light",
        scheme="monochrome",
        description="Minimalist light (monochrome)",
    ),
)

_CANONICAL_BY_SLUG: dict[str, PresetSpec] = {p.slug: p for p in CURATED_PRESETS}

_LEGACY_ALIASES: dict[str, str] = {
    "m3-baseline-dark": "m3-purple-dark",
    "m3-baseline-light": "m3-purple-light",
    "m3-baseline-amoled": "m3-black-amoled",
    "m3-brown-amoled": "m3-brown-dark",
    "m3-ocean-dark": "m3-blue-dark",
    "m3-ocean-light": "m3-blue-light",
    "m3-vlc-orange-dark": "m3-orange-dark",
    "m3-vlc-orange-light": "m3-orange-light",
    "m3-emerald-dark": "m3-green-dark",
    "m3-rose-dark": "m3-red-dark",
    "m3-monochrome-dark": "m3-black-dark",
}

PRESET_BY_SLUG: dict[str, PresetSpec] = {
    **_CANONICAL_BY_SLUG,
    **{alias: _CANONICAL_BY_SLUG[target] for alias, target in _LEGACY_ALIASES.items()},
}
