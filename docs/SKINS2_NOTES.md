# VLC Skins2 Notes

Technical constraints in VLC 3.0.x `skins2` and how this project handles them.

## 1. Opaque Pre-Composited Sprites (`alpha = 255`)

On Windows (`win32_graphics.cpp`), VLC composites button, checkbox, slider, and image PNGs over a black offscreen HDC and blits with a 1-bit `HRGN` mask (`alpha > 0`). Semi-transparent pixels cause dark fringes and jagged edges. All interactive sprites, sliders, and edge resize strips are pre-composited onto their exact opaque container color (`alpha = 255`), eliminating 1-bit artifacts.

## 2. Omitting `width`/`height` on `<Slider>`

In `bezier.cpp`, `Bezier::getWidth()`/`getHeight()` return `max(coord) + 1`. Setting explicit `width`/`height` on `<Slider>` causes `CtrlSliderBg` and `CtrlSliderCursor` to apply mismatched scale factors, stretching tracks and offsetting handles. `<Slider>` elements omit `width`/`height` (checked in `validator.py`).

## 3. Tooltip Font Order

`Builder::build()` runs `addTheme()` before `addFont()`, so `tooltipfont` must be `"defaultfont"` rather than a custom font ID (checked in `validator.py`).

## 4. Handle Gap Cutout on Sliders

`<Slider>` draws `<SliderBackground>` first, then the handle centered on top. Adding a `3dp` margin filled with the bar's background color around the handle cleanly carves the M3 gap at any playback position or window width.

## 5. Startup Layout Order

VLC activates the **last** `<Layout>` inside a `<Window>` on launch, so `main_normal` is declared last in `<Window id="main">`.

## 6. Windows vs Linux Skins Folder

- **Windows:** `Win32Factory` scans `%APPDATA%\vlc\skins\` (no `2`) to populate **Interface → Select Skin**.
- **Linux:** `X11Factory` scans `~/.local/share/vlc/skins2/`.

## 7. Audio/Video Popups While Stopped

`dialogs.audioPopup()` and `dialogs.videoPopup()` render empty menus when no media is loaded. The skin gates them on `not vlc.isStopped` and swaps in fallback `<PopupMenu>` menus when `vlc.isStopped`.

## 8. Platform Limits

- macOS is not supported by VLC `skins2`.
- `CtrlTree` (`Playtree`) uses rectangular `fillRect` for row selection (`skin.dtd` has no `border-radius` or `selimage`).
- `skins2` uses physical pixels, so HiDPI displays use dedicated `1.25x` / `1.5x` / `2x` `.vlt` builds.
