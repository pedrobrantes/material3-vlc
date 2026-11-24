# Design System Mapping

How Material 3 tokens (`m3.material.io`) map onto VLC `skins2` widgets.

## Surface Elevation

- `surfaceContainerLowest` — video / album art stage (`#000000` in AMOLED mode)
- `surfaceContainerLow` — top app bar and playlist side sheet
- `surfaceContainer` — bottom control bar, compact mini-player, equalizer background
- `surfaceContainerHigh` — fullscreen HUD, control center cards, album art placeholder, about dialog
- `surfaceContainerHighest` — inactive slider tracks and unchecked switch track

## State Layers

Foreground (`on-*`) color blended over the button's container:

| State | Opacity |
| --- | --- |
| Resting (`up`) | `0%` |
| Hover (`over`) | `8%` |
| Pressed (`down`) | `10%–12%` |
| Active drag | `16%` |

## Components

- **Play/Pause FAB:** `primary` container with `onPrimary` icon; full pill when paused, rounded squircle (`shape.medium`) while playing.
- **Sliders:** `6dp` rounded track (`primary` fill + stop dot) with a `4dp` vertical pill handle (`2.5dp` pressed) and a surface-matched margin that creates the M3 handle gap.
- **Equalizer:** `52×32dp` M3 switch and 10-band + preamp vertical sliders centered on `0 dB`.
- **Icons:** Material Symbols Rounded (weight 400, Apache-2.0). Active toggles switch to filled tonal pills (`secondaryContainer` / `onSecondaryContainer`). Window close buttons follow the active theme palette.

## Contrast Checks

`tests/test_color_tokens.py` verifies all curated presets against WCAG 2.1:
- `onPrimary / primary` ≥ `4.5:1`
- `onSurface / surfaceContainer` and `surfaceContainerLow` ≥ `7.0:1`
- `onSurfaceVariant / surfaceContainer` ≥ `4.5:1`
- `onSecondaryContainer / secondaryContainer` ≥ `4.5:1`
- `primary / surfaceContainer` ≥ `3.0:1`
