# Contributing

Pull requests, bug reports, and new palette presets are welcome.

## Setup

With Nix / `devenv`:
```bash
git clone https://github.com/PedroBrantes/material3-vlc.git
cd material3-vlc
direnv allow
uv sync
```

With Python 3.11+ and `uv`:
```bash
git clone https://github.com/PedroBrantes/material3-vlc.git
cd material3-vlc
uv sync
```

## Layout

- `src/material3_vlc/tokens/` — HCT colors, presets, OS sync, shapes, typography
- `src/material3_vlc/render/` — SVG icons, sliders, surfaces, sprite packing
- `src/material3_vlc/skin/` — scaled metrics, `theme.xml` builder, DTD validator, `.vlt` packager, VLC installer
- `src/material3_vlc/studio/` — local palette editor web UI
- `src/material3_vlc/preview/` — PNG layout compositor

## Guidelines

1. Pull all colors from `DesignTokens.colors` rather than hardcoding hex values in renderers or XML.
2. Derive geometry through `SkinMetrics.px()` so `1x`–`2x` scales stay aligned.
3. Only bundle Apache-2.0 / MIT assets (e.g., Material Symbols SVGs).
4. Ensure presets pass WCAG contrast checks (`tests/test_color_tokens.py`) and `skin.dtd` validation.

## Adding a Preset

1. Add a `PresetSpec` entry in `src/material3_vlc/tokens/presets.py`.
2. Check tokens and build previews:
   ```bash
   uv run m3vlc inspect-tokens --preset <slug>
   uv run m3vlc build --preset <slug> --preview
   ```

## Checks

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -v
```

Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.).
