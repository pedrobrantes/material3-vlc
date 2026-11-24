<div align="center">

<img src="docs/assets/hero-banner.svg" alt="Material 3 VLC" width="100%"/>

<br/><br/>

[![Releases](https://img.shields.io/badge/Download-Releases-764635?style=for-the-badge&logo=github&logoColor=FFDCD0)](https://github.com/PedroBrantes/material3-vlc/releases)
[![VLC 3.x](https://img.shields.io/badge/VLC_3.x-Windows_%26_Linux-FF8800?style=for-the-badge&logo=vlcmediaplayer&logoColor=FFFFFF)](https://www.videolan.org/vlc/skins.php)
[![License: MIT](https://img.shields.io/badge/License-MIT-146C2E?style=for-the-badge)](LICENSE)

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/brantes)
[![Patreon](https://img.shields.io/badge/Patreon-Support-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://patreon.com/brantes)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/PedroBrantes)

<p>
  Material 3 skins for VLC Media Player, generated from HCT color tokens.<br/>
  Includes 10 pre-built color palettes (Dark, Light, AMOLED), 1x &amp; 2x HiDPI builds, OS wallpaper color sync, and a local palette editor.
</p>

<p>
  <a href="#screenshots">Screenshots</a> ·
  <a href="#palettes">Palettes</a> ·
  <a href="#install">Install</a> ·
  <a href="#theme-studio">Theme Studio</a> ·
  <a href="#dynamic-colors">Dynamic Colors</a> ·
  <a href="#support">Support</a>
</p>

</div>

---

## Screenshots

### Brown Dark (`m3-brown-dark`)
<p align="center">
  <img src="docs/previews/m3-brown-dark-showcase.png" alt="Material 3 Brown Dark" width="960"/>
</p>

### Brown Light (`m3-brown-light`)
<p align="center">
  <img src="docs/previews/m3-brown-light-showcase.png" alt="Material 3 Brown Light" width="960"/>
</p>

### Video Playback & Fullscreen HUD
<p align="center">
  <img src="docs/previews/m3-purple-dark-main.png" alt="Video Playback" width="820"/>
</p>
<p align="center">
  <img src="docs/previews/m3-purple-dark-fullscreen.png" alt="Fullscreen Controller HUD" width="820"/>
</p>

### Other Palettes
| Purple Dark (`m3-purple-dark`) | Orange Dark (`m3-orange-dark`) |
| :---: | :---: |
| <img src="docs/previews/m3-purple-dark-showcase.png" alt="Purple Dark" width="460"/> | <img src="docs/previews/m3-orange-dark-showcase.png" alt="Orange Dark" width="460"/> |

| Blue Dark (`m3-blue-dark`) | White Light (`m3-white-light`) |
| :---: | :---: |
| <img src="docs/previews/m3-blue-dark-showcase.png" alt="Blue Dark" width="460"/> | <img src="docs/previews/m3-white-light-showcase.png" alt="White Light" width="460"/> |

---

## Palettes

Pre-built `.vlt` files for all 10 color families (in `1x` and `2x` HiDPI) are attached to every [GitHub Release](https://github.com/PedroBrantes/material3-vlc/releases).

<p align="center">
  <img src="docs/assets/palette-strip.svg" alt="Available color palettes" width="100%"/>
</p>

| Color | Dark / AMOLED | Light | Seed |
| :--- | :--- | :--- | :---: |
| **Brown** | `m3-brown-dark.vlt` | `m3-brown-light.vlt` | `#795548` |
| **Red** | `m3-red-dark.vlt` | `m3-red-light.vlt` | `#D32F2F` |
| **Blue** | `m3-blue-dark.vlt` | `m3-blue-light.vlt` | `#1A73E8` |
| **Yellow** | `m3-yellow-dark.vlt` | `m3-yellow-light.vlt` | `#C99700` |
| **Green** | `m3-green-dark.vlt` | `m3-green-light.vlt` | `#146C2E` |
| **Pink** | `m3-pink-dark.vlt` | `m3-pink-light.vlt` | `#D81B60` |
| **Purple** | `m3-purple-dark.vlt` | `m3-purple-light.vlt` | `#6750A4` |
| **Orange** | `m3-orange-dark.vlt` | `m3-orange-light.vlt` | `#FF8800` |
| **Black** | `m3-black-amoled.vlt` / `m3-black-dark.vlt` | — | `#808080` |
| **White** | — | `m3-white-light.vlt` | `#808080` |

---

## Features

- **Layouts:** Main player, docked playlist side sheet, compact mini-player, 10-band equalizer, control center, floating fullscreen HUD, and about dialog.
- **Controls:** Morphing Play/Pause FAB, seek and volume sliders with M3 handle gap, 3-state repeat toggle, DVD bar, audio/subtitle menus, and theme-matched window controls.
- **HiDPI:** Vector-rendered at `1x`, `1.25x`, `1.5x`, or `2x` with surface-matched sprites (no jagged Win32 1-bit edges).
- **Color Engine:** HCT color roles (`materialyoucolor`), Dark / Light / AMOLED modes, contrast presets, and automated WCAG AA/AAA + VLC `skin.dtd` checks.

---

## Install

> VLC `skins2` works on **Windows** and **Linux** (not supported on macOS).

### Manual (no Python needed)
1. Download the `.vlt` file(s) from [Releases](https://github.com/PedroBrantes/material3-vlc/releases).
2. Copy them to VLC's skins folder:
   - **Windows:** `%APPDATA%\vlc\skins\` (`Win + R` → `%APPDATA%\vlc\skins`)
     *Use `skins` (not `skins2`) on Windows so every theme appears under Interface → Select Skin.*
   - **Linux:** `~/.local/share/vlc/skins2/` (Debian/Ubuntu: `sudo apt install vlc-plugin-skins2`; Arch: `sudo pacman -S vlc-gui-skins2`)
3. In VLC, open **Tools → Preferences** (`Ctrl + P`) → **Interface → Look and feel** → **Use custom skin**.
4. Pick your `.vlt` file under **Skin resource file**, click **Save**, and restart VLC.

Once active, right-click VLC → **Interface → Select Skin** (or use the palette button in the Control Center) to switch themes.

### CLI
Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/PedroBrantes/material3-vlc.git
cd material3-vlc
uv sync

# Build and install all 19 presets, activate Brown Dark, and restart VLC
uv run m3vlc install-all --activate-preset m3-brown-dark --restart

# Revert back to VLC's default Qt UI
uv run m3vlc reset-ui
```

---

## Theme Studio

Launch the local browser UI to tweak individual color roles and apply directly to VLC:

```bash
uv run m3vlc studio
```

- Quick swatches for all 10 color families + Dark / Light / AMOLED toggle
- Individual color pickers for 17 Material 3 roles with live contrast ratios
- One-click OS wallpaper sync and **Save, Apply & Restart VLC**

---

## Dynamic Colors

Generate a skin from your current desktop wallpaper, system accent, or any hex seed:

```bash
# Sync from active Windows/Linux wallpaper and OS theme
uv run m3vlc sync --activate --restart

# Sync from OS accent color
uv run m3vlc sync --source accent --mode dark --restart

# Watch for wallpaper/theme changes
uv run m3vlc sync --watch --interval 5

# Custom seed or image with optional per-role overrides
uv run m3vlc build --seed "#795548" --mode dark --override primary=#FFB74D --restart
uv run m3vlc build --wallpaper ~/Pictures/wallpaper.jpg --mode dark --restart
```

---

## Support

This project is MIT licensed. If you'd like to support development:

<div align="center">

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Donate-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/brantes)
[![Patreon](https://img.shields.io/badge/Patreon-Support-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://patreon.com/brantes)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub-Sponsor-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/PedroBrantes)
[![Issues](https://img.shields.io/badge/GitHub-Issues-6750A4?style=for-the-badge&logo=github&logoColor=white)](https://github.com/PedroBrantes/material3-vlc/issues)

</div>

---

## Docs & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and PR guidelines.

- [Architecture](docs/ARCHITECTURE.md)
- [Design System Mapping](docs/DESIGN_SYSTEM.md)
- [VLC Skins2 Notes](docs/SKINS2_NOTES.md)
- [Roadmap](docs/ROADMAP.md)

## License & Credits

- Code & skins: [MIT](LICENSE)
- Icons: [Material Symbols Rounded](https://fonts.google.com/icons) (Apache-2.0)
- Font: [Roboto](https://github.com/googlefonts/roboto-2) (Apache-2.0)
- Third-party notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Inspired by [`PapirusDevelopmentTeam/materia-vlc`](https://github.com/PapirusDevelopmentTeam/materia-vlc)
