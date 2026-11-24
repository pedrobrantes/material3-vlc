"""OS Dynamic Color detection (Material You sync from Wallpaper, Accent, and Dark/Light mode).

Supports:
- Windows 10/11 (native and via WSL2 interop):
  * Desktop wallpaper (`TranscodedWallpaper` / `Control Panel\\Desktop\\WallPaper`)
  * System accent color (`HKCU\\Software\\Microsoft\\Windows\\DWM\\AccentColor`, ABGR DWORD)
  * System theme mode (`AppsUseLightTheme`)
- Linux desktops:
  * Pywal / Matugen (`~/.cache/wal/colors.json`)
  * GNOME (`gsettings` `picture-uri` / `picture-uri-dark` & `color-scheme`)
  * KDE Plasma (`~/.config/kdeglobals` `AccentColor`)
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

from material3_vlc.tokens.color import ThemeMode, extract_seed_from_image, normalize_hex, rgb_to_hex

DynamicSource = Literal["wallpaper", "accent", "auto"]


@dataclass(frozen=True, slots=True)
class SystemThemeSnapshot:
    """Detected host OS appearance state for Material You syncing."""

    seed: str
    mode: ThemeMode
    source_kind: str
    source_detail: str
    fingerprint: str


def decode_windows_abgr(dword: int) -> str:
    """Convert a Windows DWM `AccentColor` DWORD (`0xAABBGGRR`) to `#RRGGBB`."""
    r = dword & 0xFF
    g = (dword >> 8) & 0xFF
    b = (dword >> 16) & 0xFF
    return rgb_to_hex(r, g, b)


def _win_path_to_wsl(win_path: str) -> Path:
    cleaned = win_path.strip().strip('"')
    if len(cleaned) >= 3 and cleaned[1:3] == ":\\" and platform.system().lower() == "linux":
        drive = cleaned[0].lower()
        rest = cleaned[3:].replace("\\", "/")
        return Path(f"/mnt/{drive}/{rest}")
    return Path(cleaned)


def _query_windows_registry_theme() -> tuple[ThemeMode | None, str | None, Path | None]:
    """Read Windows AppsUseLightTheme, DWM AccentColor, and WallPaper via PowerShell."""
    ps_cmd = (
        "$p = Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -ErrorAction SilentlyContinue; "
        "$d = Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\DWM' -ErrorAction SilentlyContinue; "
        "$w = Get-ItemProperty 'HKCU:\\Control Panel\\Desktop' -ErrorAction SilentlyContinue; "
        "Write-Output \"LIGHT=$($p.AppsUseLightTheme)\"; "
        "Write-Output \"ACCENT=$($d.AccentColor)\"; "
        "Write-Output \"WALLPAPER=$($w.WallPaper)\""
    )
    exe = "powershell.exe"
    cwd = "/mnt/c" if platform.system().lower() == "linux" and Path("/mnt/c").is_dir() else None
    try:
        proc = subprocess.run(
            [exe, "-NoProfile", "-Command", ps_cmd],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None, None

    mode: ThemeMode | None = None
    accent: str | None = None
    wallpaper: Path | None = None

    for line in proc.stdout.replace("\r", "").splitlines():
        if line.startswith("LIGHT="):
            val = line.split("=", 1)[1].strip()
            if val == "1":
                mode = "light"
            elif val == "0":
                mode = "dark"
        elif line.startswith("ACCENT="):
            val = line.split("=", 1)[1].strip()
            if val.isdigit():
                accent = decode_windows_abgr(int(val))
        elif line.startswith("WALLPAPER="):
            val = line.split("=", 1)[1].strip()
            if val:
                wp = _win_path_to_wsl(val)
                if wp.is_file():
                    wallpaper = wp

    return mode, accent, wallpaper


def _query_linux_theme() -> tuple[ThemeMode | None, str | None, Path | None]:
    """Probe GNOME, KDE, and pywal/matugen on Linux desktops."""
    mode: ThemeMode | None = None
    accent: str | None = None
    wallpaper: Path | None = None

    # 1. Pywal (~/.cache/wal/colors.json)
    wal_json = Path.home() / ".cache" / "wal" / "colors.json"
    if wal_json.is_file():
        try:
            data = json.loads(wal_json.read_text(encoding="utf-8"))
            wp_str = data.get("wallpaper")
            if isinstance(wp_str, str) and Path(wp_str).is_file():
                wallpaper = Path(wp_str)
            colors = data.get("colors", {})
            if isinstance(colors, dict) and isinstance(colors.get("color4"), str):
                accent = normalize_hex(colors["color4"])
        except (OSError, ValueError):
            pass

    # 2. GNOME gsettings
    try:
        scheme_proc = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if "prefer-dark" in scheme_proc.stdout:
            mode = "dark"
        elif "default" in scheme_proc.stdout or "prefer-light" in scheme_proc.stdout:
            mode = "light"

        uri_key = "picture-uri-dark" if mode == "dark" else "picture-uri"
        wp_proc = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.background", uri_key],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        uri = wp_proc.stdout.strip().strip("'\"")
        if uri.startswith("file://"):
            candidate = Path(unquote(uri.removeprefix("file://")))
            if candidate.is_file():
                wallpaper = candidate
    except (OSError, subprocess.SubprocessError):
        pass

    # 3. KDE Plasma kdeglobals AccentColor
    kdeglobals = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kdeglobals"
    if accent is None and kdeglobals.is_file():
        try:
            text = kdeglobals.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^AccentColor\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", text, re.MULTILINE)
            if m:
                accent = rgb_to_hex(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except OSError:
            pass

    return mode, accent, wallpaper


def _file_fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def detect_system_theme(
    *,
    source: DynamicSource = "auto",
    mode_override: ThemeMode | None = None,
    fallback_seed: str = "#6750A4",
) -> SystemThemeSnapshot:
    """Detect the current host OS dynamic Material You seed color and theme mode."""
    sys_name = platform.system().lower()
    is_wsl = sys_name == "linux" and Path("/mnt/c/Windows").is_dir()

    detected_mode: ThemeMode | None = None
    accent: str | None = None
    wallpaper: Path | None = None

    if sys_name == "windows" or is_wsl:
        detected_mode, accent, wallpaper = _query_windows_registry_theme()
    else:
        detected_mode, accent, wallpaper = _query_linux_theme()

    resolved_mode: ThemeMode = mode_override or detected_mode or "dark"

    if source in ("wallpaper", "auto") and wallpaper is not None:
        seed = extract_seed_from_image(wallpaper, fallback=fallback_seed)
        fp = f"wp:{_file_fingerprint(wallpaper)}:{resolved_mode}"
        return SystemThemeSnapshot(
            seed=seed,
            mode=resolved_mode,
            source_kind="wallpaper",
            source_detail=str(wallpaper),
            fingerprint=fp,
        )

    if source in ("accent", "auto") and accent is not None:
        seed = normalize_hex(accent)
        return SystemThemeSnapshot(
            seed=seed,
            mode=resolved_mode,
            source_kind="accent",
            source_detail=f"OS Accent {seed}",
            fingerprint=f"accent:{seed}:{resolved_mode}",
        )

    norm_fb = normalize_hex(fallback_seed)
    return SystemThemeSnapshot(
        seed=norm_fb,
        mode=resolved_mode,
        source_kind="fallback",
        source_detail=f"Fallback seed {norm_fb}",
        fingerprint=f"fallback:{norm_fb}:{resolved_mode}",
    )
