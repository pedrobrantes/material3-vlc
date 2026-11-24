"""Unit tests for Material 3 Theme Studio and per-role color overrides."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from material3_vlc.studio.server import make_studio_handler
from material3_vlc.tokens.color import apply_color_overrides, generate_color_roles
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig


def test_color_overrides_replace_individual_roles() -> None:
    base = generate_color_roles("#795548", mode="dark", scheme="tonal-spot")
    overridden = apply_color_overrides(
        base,
        {
            "primary": "#FFB74D",
            "surface_container": "#2B1E1A",
        },
    )
    assert overridden.primary == "#FFB74D"
    assert overridden.surface_container == "#2B1E1A"
    assert overridden.on_primary == base.on_primary

    with pytest.raises(ValueError, match="Unknown Material 3 color role"):
        apply_color_overrides(base, {"not_a_real_role": "#FFFFFF"})

    cfg = ThemeConfig(
        name="Custom Brown",
        slug="m3-custom-brown",
        seed="#795548",
        mode="dark",
        color_overrides={"primary": "#FFB74D"},
    )
    tokens = DesignTokens.from_config(cfg)
    assert tokens.colors.primary == "#FFB74D"


def _http_json(url: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"} if req_data is not None else {}
    req = urllib.request.Request(url, data=req_data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return dict(json.loads(resp.read().decode("utf-8")))


def test_studio_http_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_studio_handler(tmp_path))
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. HTML landing page uses embedded Material Symbols SVGs, M3 sliders, and zero emojis/lyrics
        with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
            html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "Material 3 VLC Theme Studio" in html
            assert 'class="m3-slider"' in html
            assert 'viewBox="0 -960 960 960"' in html
            assert "Synced Lyrics" not in html
            # Accessibility & responsive containment guarantees
            assert 'class="skip-link"' in html
            assert 'role="radiogroup"' in html
            assert 'aria-live="polite"' in html
            assert "prefers-reduced-motion" in html
            assert ":focus-visible" in html
            assert "repeat(auto-fill, minmax(94px, 1fr))" in html
            # Ensure no pictographic emojis leaked into Studio HTML
            for ch in ("🎛", "📌", "📂", "🎧", "💬", "🔀", "🔁", "🔊", "🎨"):
                assert ch not in html

        # 2. Presets catalog covers all 10 required release color families
        presets_res = _http_json(f"{base_url}/api/presets")
        families = {p["family"] for p in presets_res["presets"]}
        assert families == {
            "Brown",
            "Red",
            "Blue",
            "Yellow",
            "Green",
            "Pink",
            "Purple",
            "Orange",
            "Black",
            "White",
        }

        # 3. Live token preview with per-role override
        tok_res = _http_json(
            f"{base_url}/api/tokens",
            {
                "seed": "#795548",
                "mode": "dark",
                "scheme": "tonal-spot",
                "overrides": {"primary": "#FF9800"},
            },
        )
        assert tok_res["tokens"]["color"]["primary"] == "#FF9800"
        assert len(tok_res["contrast"]) >= 4

        # 4. Build & Apply endpoint (mocking install so user's real VLC config is untouched)
        def fake_install(vlt_path: Path, *, activate: bool = False) -> list[tuple[Any, Path, Any]]:
            dest = tmp_path / "skins" / vlt_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(vlt_path.read_bytes())
            return [(None, dest, None)]

        monkeypatch.setattr("material3_vlc.studio.server.install_vlt_to_targets", fake_install)
        apply_res = _http_json(
            f"{base_url}/api/apply",
            {
                "seed": "#795548",
                "mode": "dark",
                "scheme": "tonal-spot",
                "slug": "m3-studio-test",
                "overrides": {"primary": "#FFB74D"},
                "activate": True,
                "restart": False,
            },
        )
        assert apply_res["ok"] is True
        assert (tmp_path / "m3-studio-test.vlt").is_file()
        assert (tmp_path / "skins" / "m3-studio-test.vlt").is_file()
    finally:
        server.shutdown()
        server.server_close()
