"""CLI tests for `m3vlc`."""

from __future__ import annotations

import json
from pathlib import Path

from material3_vlc.cli import main


def test_cli_presets(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["presets"]) == 0
    out = capsys.readouterr().out
    assert "m3-brown-dark" in out
    assert "m3-purple-dark" in out
    assert "m3-orange-dark" in out
    assert "m3-black-amoled" in out
    assert "m3-white-light" in out


def test_cli_inspect_tokens_json(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["inspect-tokens", "--seed", "#1A73E8", "--mode", "dark", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["meta"]["seed"] == "#1A73E8"
    assert "surface_container" in data["color"]


def test_cli_build_validate_and_install(tmp_path: Path) -> None:
    out_dir = tmp_path / "dist"
    install_dir = tmp_path / "vlc_skins"
    assert main(["build", "--preset", "m3-brown-dark", "--out", str(out_dir)]) == 0
    vlt = out_dir / "m3-brown-dark.vlt"
    assert vlt.is_file()

    assert main(["validate", str(vlt)]) == 0
    assert main(["install", str(vlt), "--target-dir", str(install_dir)]) == 0
    assert (install_dir / "m3-brown-dark.vlt").is_file()
