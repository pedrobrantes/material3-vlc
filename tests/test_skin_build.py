"""End-to-end tests for XML generation, DTD validation, `.vlt` packaging, and previews."""

from __future__ import annotations

import tarfile
from pathlib import Path

from material3_vlc.preview.compositor import render_skin_previews
from material3_vlc.skin.packager import build_skin
from material3_vlc.skin.validator import validate_skin_dir
from material3_vlc.tokens.theme import ThemeConfig


def test_build_and_validate_dark_skin(tmp_path: Path) -> None:
    cfg = ThemeConfig.from_preset("m3-brown-dark")
    res = build_skin(cfg, tmp_path, keep_unpacked=True)

    assert res.validation.ok, f"Validation failed: {res.validation.errors}"
    assert res.validation.errors == ()
    assert res.validation.window_count == 5
    assert res.validation.layout_count == 7
    assert res.vlt_path.is_file()
    assert res.source_dir is not None

    # Inspect .vlt archive structure (must be valid tar.gz with <slug>/theme.xml)
    with tarfile.open(res.vlt_path, "r:gz") as tar:
        names = tar.getnames()
    assert f"{cfg.slug}/theme.xml" in names
    assert f"{cfg.slug}/fonts/Roboto-Regular.ttf" in names
    assert f"{cfg.slug}/fonts/Roboto-Medium.ttf" in names
    assert f"{cfg.slug}/images/ui_controls.png" in names

    # Every SubBitmap in ui_controls.png must be 100% opaque (alpha=255) for crisp Win32 BitBlt
    from lxml import etree
    from PIL import Image

    root = etree.parse(str(res.source_dir / "theme.xml")).getroot()
    with Image.open(res.source_dir / "images" / "ui_controls.png") as atlas:
        rgba = atlas.convert("RGBA")
        bmp_el = root.find("./Bitmap[@id='ui_controls']")
        assert bmp_el is not None
        for sub in bmp_el.findall("SubBitmap"):
            sx, sy = int(sub.get("x", "0")), int(sub.get("y", "0"))
            sw, sh = int(sub.get("width", "0")), int(sub.get("height", "0"))
            tile = rgba.crop((sx, sy, sx + sw, sy + sh))
            assert min(p[3] for p in tile.get_flattened_data()) == 255, (
                f"SubBitmap {sub.get('id')} has transparent pixels (causes Win32 1-bit jagged edges)"
            )

    # Render full visual preview suite
    previews = render_skin_previews(res.source_dir, res.tokens, tmp_path / "previews")
    assert set(previews.keys()) == {
        "main",
        "playlist",
        "compact",
        "equalizer",
        "tools",
        "fullscreen",
        "about",
        "showcase",
    }
    for p in previews.values():
        assert p.is_file() and p.stat().st_size > 1024


def test_build_light_and_amoled_and_hidpi(tmp_path: Path) -> None:
    for slug, scale in [
        ("m3-brown-light", 1.0),
        ("m3-black-amoled", 1.0),
        ("m3-white-light", 1.0),
        ("m3-orange-dark", 1.5),
    ]:
        cfg = ThemeConfig.from_preset(slug, scale=scale)
        res = build_skin(cfg, tmp_path)
        assert res.validation.ok
        assert res.vlt_path.is_file()


def test_reproducible_vlt_bytes(tmp_path: Path) -> None:
    cfg = ThemeConfig.from_preset("m3-black-dark")
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    r1 = build_skin(cfg, out1)
    r2 = build_skin(cfg, out2)
    # Deterministic timestamps/uid/gid/sort produce identical archive contents
    with tarfile.open(r1.vlt_path, "r:gz") as t1, tarfile.open(r2.vlt_path, "r:gz") as t2:
        assert t1.getnames() == t2.getnames()
        for m1, m2 in zip(t1.getmembers(), t2.getmembers(), strict=True):
            assert m1.mtime == m2.mtime
            assert m1.uid == m2.uid == 0


def test_validator_catches_broken_xml(tmp_path: Path) -> None:
    bad_dir = tmp_path / "broken"
    bad_dir.mkdir()
    (bad_dir / "theme.xml").write_text(
        '<!DOCTYPE Theme PUBLIC "-//VideoLAN//DTD VLC Skins V2.0//EN" "skin.dtd">'
        '<Theme version="2.0"><ThemeInfo name="Bad"/>'
        '<Window id="main"><Layout id="l1" width="100" height="100">'
        '<Button id="b1" up="missing_bmp" action="invalid.action()"/>'
        "</Layout></Window></Theme>",
        encoding="utf-8",
    )
    report = validate_skin_dir(bad_dir)
    assert not report.ok
    assert any("missing_bmp" in e for e in report.errors)
    assert any("invalid.action()" in e for e in report.errors)
