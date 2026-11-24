"""Local HTTP server for the Material 3 VLC Theme Studio palette editor."""

from __future__ import annotations

import json
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from material3_vlc.skin.packager import build_skin
from material3_vlc.skin.vlc_install import (
    install_vlt_to_targets,
    restart_vlc,
    to_vlc_native_path,
)
from material3_vlc.studio.ui import build_studio_html
from material3_vlc.tokens.color import (
    SchemeVariant,
    ThemeMode,
    contrast_ratio,
    generate_color_roles,
    normalize_hex,
)
from material3_vlc.tokens.dynamic import detect_system_theme
from material3_vlc.tokens.presets import CURATED_PRESETS
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig


def _contrast_summary(tokens: DesignTokens) -> list[dict[str, Any]]:
    c = tokens.colors
    pairs = [
        ("onPrimary / primary", c.on_primary, c.primary),
        ("onSurface / controls", c.on_surface, c.surface_container),
        ("onSurfaceVariant / controls", c.on_surface_variant, c.surface_container),
        ("active pill", c.on_secondary_container, c.secondary_container),
        ("primary / controls", c.primary, c.surface_container),
    ]
    out: list[dict[str, Any]] = []
    for label, fg, bg in pairs:
        ratio = contrast_ratio(fg, bg)
        grade = "AAA" if ratio >= 7.0 else ("AA" if ratio >= 4.5 else ("AA-Large" if ratio >= 3.0 else "FAIL"))
        out.append({"label": label, "ratio": round(ratio, 2), "grade": grade})
    return out


def _config_from_payload(payload: dict[str, Any]) -> ThemeConfig:
    seed = normalize_hex(str(payload.get("seed", "#795548")))
    mode: ThemeMode = payload.get("mode", "dark")
    scheme: SchemeVariant = payload.get("scheme", "tonal-spot")
    contrast = float(payload.get("contrast", 0.0))
    scale = float(payload.get("scale", 1.0))
    name = str(payload.get("name") or f"Material 3 Custom ({seed})").strip()
    slug = str(payload.get("slug") or "m3-custom").strip().replace(" ", "-").lower()
    raw_overrides = payload.get("overrides") or {}
    overrides = {
        str(k): normalize_hex(str(v))
        for k, v in raw_overrides.items()
        if isinstance(k, str) and isinstance(v, str)
    }
    return ThemeConfig(
        name=name,
        slug=slug,
        seed=seed,
        mode=mode,
        scheme=scheme,
        contrast=contrast,
        scale=scale,
        color_overrides=overrides,
    )


def make_studio_handler(output_dir: Path) -> type[BaseHTTPRequestHandler]:
    """Build a request handler bound to `output_dir` for `.vlt` compilation."""

    class StudioHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return  # Keep terminal output crisp

        def _send_json(self, data: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            parsed = json.loads(raw.decode("utf-8"))
            return dict(parsed) if isinstance(parsed, dict) else {}

        def do_GET(self) -> None:
            path = urllib.parse.urlparse(self.path).path

            if path in ("/", "/index.html"):
                body = build_studio_html().encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/api/presets":
                self._send_json(
                    {
                        "presets": [
                            {
                                "slug": p.slug,
                                "display_name": p.display_name,
                                "family": p.family,
                                "seed": p.seed,
                                "mode": p.mode,
                                "scheme": p.scheme,
                                "contrast": p.contrast,
                                "description": p.description,
                            }
                            for p in CURATED_PRESETS
                        ]
                    }
                )
                return

            if path == "/api/sync-os":
                snap = detect_system_theme(source="auto")
                self._send_json(
                    {
                        "seed": snap.seed,
                        "mode": snap.mode,
                        "source_kind": snap.source_kind,
                        "source_detail": snap.source_detail,
                    }
                )
                return

            self._send_json({"error": f"Not found: {path}"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            path = urllib.parse.urlparse(self.path).path
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json({"error": f"Invalid JSON: {exc}"}, status=HTTPStatus.BAD_REQUEST)
                return

            if path == "/api/tokens":
                try:
                    cfg = _config_from_payload(payload)
                    base_roles = generate_color_roles(
                        cfg.seed, mode=cfg.mode, scheme=cfg.scheme, contrast=cfg.contrast
                    )
                    tokens = DesignTokens.from_config(cfg)
                    self._send_json(
                        {
                            "tokens": tokens.to_dict(),
                            "base_color": base_roles.to_dict(),
                            "contrast": _contrast_summary(tokens),
                        }
                    )
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            if path == "/api/apply":
                try:
                    cfg = _config_from_payload(payload)
                    res = build_skin(cfg, output_dir, keep_unpacked=False)
                    activate = bool(payload.get("activate", True))
                    do_restart = bool(payload.get("restart", False))
                    installed = install_vlt_to_targets(res.vlt_path, activate=activate)
                    primary_dest = installed[-1][1] if installed else res.vlt_path

                    msg = f"Built & installed {res.vlt_path.name} -> {to_vlc_native_path(primary_dest)}"
                    restarted = False
                    if do_restart:
                        restarted, r_msg = restart_vlc(primary_dest)
                        msg = f"{msg} | {r_msg}"

                    self._send_json(
                        {
                            "ok": True,
                            "vlt_path": str(res.vlt_path),
                            "installed_native": to_vlc_native_path(primary_dest),
                            "restarted": restarted,
                            "message": msg,
                        }
                    )
                except Exception as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            self._send_json({"error": f"Not found: {path}"}, status=HTTPStatus.NOT_FOUND)

    return StudioHandler


def run_studio(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    output_dir: Path = Path("dist"),
    open_browser: bool = True,
) -> int:
    """Launch the local Material 3 Theme Studio palette editor web app."""
    output_dir.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), make_studio_handler(output_dir))
    url = f"http://{host}:{server.server_port}"
    print(f"Material 3 VLC Theme Studio running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped Material 3 VLC Theme Studio.")
    finally:
        server.server_close()
    return 0
