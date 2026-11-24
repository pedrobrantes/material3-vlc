"""Cross-platform VLC skins discovery, installation, `vlcrc` activation, and restart helpers.

Important VLC 3.0.x platform path convention (from `win32_factory.cpp` vs `x11_factory.cpp`):
- Windows (native & WSL2): `%APPDATA%\\vlc\\skins`  (NO `2`! Required for "Select skin" menu!)
- Linux / Flatpak:         `~/.local/share/vlc/skins2`
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PlatformKind = Literal["linux", "flatpak", "windows", "windows_wsl", "custom"]

_WSL_MOUNT_RE = re.compile(r"^/mnt/([a-zA-Z])/(.*)$")


@dataclass(frozen=True, slots=True)
class VlcTarget:
    """A detected VLC user configuration and skins target directory."""

    kind: PlatformKind
    skins_dir: Path
    vlcrc_path: Path | None = None


def to_vlc_native_path(path: Path) -> str:
    """Format a filesystem path as VLC expects it (Windows backslash path for `/mnt/<drive>`)."""
    posix = path.as_posix()
    match = _WSL_MOUNT_RE.match(posix)
    if match:
        drive = match.group(1).upper()
        rest = match.group(2).replace("/", "\\")
        return f"{drive}:\\{rest}"
    return str(path)


def _detect_wsl_windows_user_dir() -> Path | None:
    """Resolve the active Windows user profile directory when running under WSL2."""
    try:
        proc = subprocess.run(
            ["cmd.exe", "/c", "echo %USERPROFILE%"],
            cwd="/mnt/c" if Path("/mnt/c").is_dir() else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            check=False,
        )
        raw = proc.stdout.strip().replace("\r", "")
        if len(raw) >= 3 and raw[1:3] == ":\\":
            drive = raw[0].lower()
            rest = raw[3:].replace("\\", "/")
            candidate = Path(f"/mnt/{drive}/{rest}")
            if candidate.is_dir():
                return candidate
    except (OSError, subprocess.SubprocessError):
        pass

    win_users = Path("/mnt/c/Users")
    cur_user = os.environ.get("USER", "")
    if cur_user:
        try:
            direct = win_users / cur_user
            if direct.is_dir():
                return direct
        except OSError:
            pass
    return None


def detect_vlc_targets() -> list[VlcTarget]:
    """Detect active VLC skins and `vlcrc` targets for the current platform."""
    targets: list[VlcTarget] = []
    sys_name = platform.system().lower()

    if sys_name == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata) / "vlc"
            # Win32Factory scans %APPDATA%\vlc\skins (no '2') for the Select Skin menu!
            targets.append(
                VlcTarget(kind="windows", skins_dir=base / "skins", vlcrc_path=base / "vlcrc")
            )
        return targets

    if sys_name == "linux":
        xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        xdg_cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        targets.append(
            VlcTarget(
                kind="linux",
                skins_dir=xdg_data / "vlc" / "skins2",
                vlcrc_path=xdg_cfg / "vlc" / "vlcrc",
            )
        )

        flatpak_base = Path.home() / ".var" / "app" / "org.videolan.VLC"
        if (flatpak_base / "data").exists():
            targets.append(
                VlcTarget(
                    kind="flatpak",
                    skins_dir=flatpak_base / "data" / "vlc" / "skins2",
                    vlcrc_path=flatpak_base / "config" / "vlc" / "vlcrc",
                )
            )

        # WSL2 host Windows VLC target (Win32Factory scans AppData\Roaming\vlc\skins!)
        win_user = _detect_wsl_windows_user_dir()
        if win_user is not None:
            try:
                vlc_roaming = win_user / "AppData" / "Roaming" / "vlc"
                if vlc_roaming.is_dir():
                    targets.append(
                        VlcTarget(
                            kind="windows_wsl",
                            skins_dir=vlc_roaming / "skins",
                            vlcrc_path=vlc_roaming / "vlcrc",
                        )
                    )
            except OSError:
                pass

    return targets


def _update_vlcrc_lines(
    lines: list[str],
    updates: dict[str, str | None],
    section_defaults: dict[str, str],
) -> list[str]:
    """Update key=value entries in `vlcrc` lines in-place, preserving comments and formatting."""
    seen: set[str] = set()
    out: list[str] = []
    key_patterns = {k: re.compile(rf"^#?\s*{re.escape(k)}\s*=.*$") for k in updates}

    for line in lines:
        matched_key: str | None = None
        for key, pat in key_patterns.items():
            if key not in seen and pat.match(line):
                matched_key = key
                break
        if matched_key is not None:
            val = updates[matched_key]
            out.append(f"#{matched_key}=" if val is None else f"{matched_key}={val}")
            seen.add(matched_key)
        else:
            out.append(line)

    for key, val in updates.items():
        if key not in seen and val is not None:
            section = section_defaults.get(key)
            if section:
                out.append("")
                out.append(f"[{section}]")
            out.append(f"{key}={val}")

    return out


def _modify_vlcrc(
    vlcrc_path: Path,
    updates: dict[str, str | None],
    section_defaults: dict[str, str],
) -> Path:
    vlcrc_path.parent.mkdir(parents=True, exist_ok=True)
    newline = (
        "\r\n" if str(vlcrc_path).startswith("/mnt/") or platform.system() == "Windows" else "\n"
    )
    if vlcrc_path.is_file():
        raw_bytes = vlcrc_path.read_bytes()
        if b"\r\n" in raw_bytes:
            newline = "\r\n"
        elif b"\n" in raw_bytes:
            newline = "\n"
        backup_path = vlcrc_path.with_name(f"{vlcrc_path.name}.m3vlc.bak")
        if not backup_path.exists():
            shutil.copy2(vlcrc_path, backup_path)
        lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
    else:
        lines = []

    updated = _update_vlcrc_lines(lines, updates=updates, section_defaults=section_defaults)
    vlcrc_path.write_bytes((newline.join(updated) + newline).encode("utf-8"))
    return vlcrc_path


def activate_skin_in_vlcrc(vlcrc_path: Path, installed_vlt: Path) -> Path:
    """Configure VLC's `vlcrc` to use `skins2` with `installed_vlt`."""
    native_skin = to_vlc_native_path(installed_vlt)
    return _modify_vlcrc(
        vlcrc_path,
        updates={
            "intf": "skins2",
            "skins2-last": native_skin,
            "skins2-config": None,
        },
        section_defaults={
            "intf": "core",
            "skins2-last": "skins2",
        },
    )


def reset_vlc_to_native_ui(vlcrc_path: Path) -> bool:
    """Revert VLC's `vlcrc` back to the native Qt interface (`#intf=`)."""
    if not vlcrc_path.is_file():
        return False
    _modify_vlcrc(vlcrc_path, updates={"intf": None}, section_defaults={})
    return True


def find_vlc_executable() -> tuple[str, list[str]] | None:
    """Locate the VLC binary (`windows_wsl`, `windows`, or `linux`)."""
    sys_name = platform.system().lower()
    if sys_name == "windows":
        candidates = [
            Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe"),
            Path(r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"),
        ]
        for c in candidates:
            if c.is_file():
                return ("windows", [str(c)])
        found = shutil.which("vlc")
        return ("windows", [found]) if found else None

    if sys_name == "linux":
        win_candidates = [
            Path("/mnt/c/Program Files/VideoLAN/VLC/vlc.exe"),
            Path("/mnt/c/Program Files (x86)/VideoLAN/VLC/vlc.exe"),
        ]
        for c in win_candidates:
            if c.is_file():
                return ("windows_wsl", [str(c)])
        found = shutil.which("vlc")
        return ("linux", [found]) if found else None

    return None


def restart_vlc(skin_vlt: Path | None = None) -> tuple[bool, str]:
    """Gracefully terminate any running VLC instance and relaunch it with `skin_vlt`."""
    exe_info = find_vlc_executable()
    if exe_info is None:
        return (False, "VLC executable not found automatically; please restart VLC manually.")

    kind, cmd_base = exe_info
    extra_args: list[str] = []
    if skin_vlt is not None:
        extra_args = ["--intf", "skins2", "--skins2-last", to_vlc_native_path(skin_vlt)]

    if kind in ("windows", "windows_wsl"):
        cwd = "/mnt/c" if kind == "windows_wsl" and Path("/mnt/c").is_dir() else None
        subprocess.run(
            ["taskkill.exe" if kind == "windows_wsl" else "taskkill", "/IM", "vlc.exe", "/F"],
            cwd=cwd,
            capture_output=True,
            timeout=5,
            check=False,
        )
        time.sleep(0.6)
        subprocess.Popen(
            [*cmd_base, *extra_args],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return (True, f"Restarted Windows VLC with {to_vlc_native_path(skin_vlt) if skin_vlt else 'saved skin'}.")

    # Native Linux
    subprocess.run(["pkill", "-x", "vlc"], capture_output=True, timeout=3, check=False)
    time.sleep(0.5)
    subprocess.Popen(
        [*cmd_base, *extra_args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return (True, f"Restarted Linux VLC with {skin_vlt if skin_vlt else 'saved skin'}.")


def install_vlt_to_targets(
    vlt_path: Path,
    *,
    target_dir: Path | None = None,
    activate: bool = False,
) -> list[tuple[VlcTarget, Path, Path | None]]:
    """Copy `vlt_path` into VLC skins directories and optionally activate in `vlcrc`."""
    if not vlt_path.is_file():
        raise FileNotFoundError(f"Skin archive not found: {vlt_path}")

    if target_dir is not None:
        targets = [VlcTarget(kind="custom", skins_dir=target_dir, vlcrc_path=None)]
    else:
        targets = detect_vlc_targets()
        if not targets:
            raise RuntimeError(
                "Could not auto-detect a VLC skins directory. Pass `--target-dir` explicitly."
            )

    results: list[tuple[VlcTarget, Path, Path | None]] = []
    for target in targets:
        target.skins_dir.mkdir(parents=True, exist_ok=True)
        dest_file = target.skins_dir / vlt_path.name
        shutil.copy2(vlt_path, dest_file)

        activated_rc: Path | None = None
        if (
            activate
            and target.vlcrc_path is not None
            and (target.vlcrc_path.is_file() or target.kind in ("windows", "windows_wsl"))
        ):
            activated_rc = activate_skin_in_vlcrc(target.vlcrc_path, dest_file)

        results.append((target, dest_file, activated_rc))
    return results
