# Third-Party Notices & Attributions

`material3-vlc` is an original clean-room implementation built from scratch under the MIT License.
It bundles and builds upon the following open-source assets, specifications, and inspirations:

## Bundled Assets

### Material Symbols (Rounded)
- **Source:** Google Material Design Icons (`google/material-design-icons`, packaged via `marella/material-symbols`)
- **Location:** `assets/icons/`
- **License:** Apache License 2.0 (<https://www.apache.org/licenses/LICENSE-2.0>)

### Roboto Fonts
- **Source:** Google Fonts (`googlefonts/roboto-2`)
- **Location:** `assets/fonts/` (`Roboto-Regular.ttf`, `Roboto-Medium.ttf`)
- **License:** Apache License 2.0 (<https://www.apache.org/licenses/LICENSE-2.0>)

### VLC Skins2 DTD (`skin.dtd`)
- **Source:** VideoLAN VLC Media Player 3.0.x (`share/skins2/skin.dtd`)
- **Location:** `assets/schema/skin.dtd`
- **License:** GNU General Public License v2.0 or later (used strictly as a validation schema reference during development/CI; not embedded inside generated MIT code)

## Runtime Libraries

- **materialyoucolor** — Python bindings for Google's Material Color Utilities (HCT / CAM16 / DynamicScheme) (Apache-2.0 / MIT)
- **resvg-py** — Python bindings for the `resvg` SVG renderer (MPL-2.0 / MIT)
- **Pillow** — Python Imaging Library (MIT-CMU)
- **lxml** — XML processing & DTD validation (BSD-3-Clause)

## Design References & Inspiration

- **Material Design 3** (<https://m3.material.io/>) and **Material Web** (<https://github.com/material-components/material-web>)
- **PapirusDevelopmentTeam/materia-vlc** (<https://github.com/PapirusDevelopmentTeam/materia-vlc>) — the original community Material Design VLC skin that inspired this modern Material 3 ground-up reimagining. No source files or binary assets from `materia-vlc` are redistributed in this repository.
