# Architecture

`material3-vlc` compiles Material 3 tokens, Material Symbols SVGs, and scaled layout metrics into VLC `.vlt` skins (`tar.gz` archives containing `theme.xml`, PNGs, and TTF fonts).

## Pipeline

1. **Tokens (`tokens/`)** — Generates 36 semantic color roles via `materialyoucolor` (HCT), plus shape, typography, and state-layer values. Supports hex seeds, presets, wallpapers, OS theme detection, and per-role overrides.
2. **Metrics (`skin/metrics.py`)** — Computes all window dimensions, paddings, and icon sizes from a single scale factor (`1.0`, `1.25`, `1.5`, `2.0`).
3. **Rendering (`render/`)** — Rasterizes SVGs via `resvg-py`, packs button sprites into `ui_controls.png`, and builds slider strips and window surfaces pre-composited onto their exact opaque container colors.
4. **XML & Packaging (`skin/`)** — Builds `theme.xml` with `lxml`, validates against VLC's `skin.dtd` plus custom ID/action checks, and packs deterministic `.vlt` archives (sorted entries, normalized timestamps and UID/GID).
5. **Preview & Studio (`preview/`, `studio/`)** — Composites PNG screenshots from the generated skin and serves the local palette editor (`m3vlc studio`).
