"""Unit tests for VLC skins path conversion and `vlcrc` activation/reset."""

from __future__ import annotations

from pathlib import Path

from material3_vlc.skin.vlc_install import (
    activate_skin_in_vlcrc,
    reset_vlc_to_native_ui,
    to_vlc_native_path,
)


def test_wsl_path_conversion() -> None:
    p = Path("/mnt/c/Users/brantes/AppData/Roaming/vlc/skins/m3-brown-dark.vlt")
    assert to_vlc_native_path(p) == r"C:\Users\brantes\AppData\Roaming\vlc\skins\m3-brown-dark.vlt"
    linux_p = Path("/home/brantes/.local/share/vlc/skins2/m3-brown-dark.vlt")
    assert to_vlc_native_path(linux_p) == str(linux_p)


def test_activate_and_reset_vlcrc_preserves_crlf(tmp_path: Path) -> None:
    vlcrc = tmp_path / "vlcrc"
    original = (
        "[skins2] # Skinnable Interface\r\n"
        "#skins2-last=\r\n"
        "skins2-config=old_layout\r\n"
        "\r\n"
        "[core]\r\n"
        "#intf=\r\n"
    )
    vlcrc.write_bytes(original.encode("utf-8"))
    skin = Path("/mnt/c/Users/brantes/AppData/Roaming/vlc/skins/m3-brown-dark.vlt")

    activate_skin_in_vlcrc(vlcrc, skin)
    assert (tmp_path / "vlcrc.m3vlc.bak").is_file()

    raw = vlcrc.read_bytes()
    assert b"\r\n" in raw
    text = raw.decode("utf-8")
    assert "intf=skins2\r\n" in text
    assert r"skins2-last=C:\Users\brantes\AppData\Roaming\vlc\skins\m3-brown-dark.vlt" in text
    assert "#skins2-config=\r\n" in text

    assert reset_vlc_to_native_ui(vlcrc) is True
    reverted = vlcrc.read_bytes().decode("utf-8")
    assert "#intf=\r\n" in reverted
    assert "intf=skins2" not in reverted


def test_activate_creates_minimal_vlcrc_if_missing(tmp_path: Path) -> None:
    vlcrc = tmp_path / "vlc" / "vlcrc"
    skin = tmp_path / "m3-brown-dark.vlt"
    activate_skin_in_vlcrc(vlcrc, skin)
    text = vlcrc.read_text(encoding="utf-8")
    assert "intf=skins2" in text
    assert f"skins2-last={skin}" in text
