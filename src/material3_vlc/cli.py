"""Command-line interface (`m3vlc`) for building, inspecting, validating, and installing skins."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

from material3_vlc import __version__
from material3_vlc.preview.compositor import render_skin_previews
from material3_vlc.skin.packager import build_skin
from material3_vlc.skin.validator import validate_skin_dir
from material3_vlc.skin.vlc_install import (
    VlcTarget,
    detect_vlc_targets,
    install_vlt_to_targets,
    reset_vlc_to_native_ui,
    restart_vlc,
    to_vlc_native_path,
)
from material3_vlc.studio.server import run_studio
from material3_vlc.tokens.color import (
    CONTRAST_LEVELS,
    SchemeVariant,
    ThemeMode,
    contrast_ratio,
    normalize_hex,
)
from material3_vlc.tokens.dynamic import DynamicSource, detect_system_theme
from material3_vlc.tokens.presets import CURATED_PRESETS
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig

SCHEME_CHOICES: tuple[SchemeVariant, ...] = (
    "tonal-spot",
    "expressive",
    "vibrant",
    "content",
    "fidelity",
    "monochrome",
    "neutral",
    "fruit-salad",
    "rainbow",
)
MODE_CHOICES: tuple[ThemeMode, ...] = ("dark", "light", "amoled")


def _parse_contrast(value: str) -> float:
    low = value.strip().lower()
    if low in CONTRAST_LEVELS:
        return CONTRAST_LEVELS[low]
    try:
        num = float(low)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid contrast '{value}'. Use standard, medium, high, or a float in [-1.0, 1.0]."
        ) from exc
    if not -1.0 <= num <= 1.0:
        raise argparse.ArgumentTypeError(f"Contrast must be in [-1.0, 1.0], got {num}.")
    return num


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "m3-custom"


def _parse_color_overrides(items: list[str] | None) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid --override '{item}'. Expected format: role=#RRGGBB (e.g. primary=#FF8800)."
            )
        role, hex_val = item.split("=", 1)
        role = role.strip()
        if not role:
            raise argparse.ArgumentTypeError(f"Empty color role in --override '{item}'.")
        overrides[role] = normalize_hex(hex_val)
    return overrides


def detect_vlc_skins_dirs() -> list[Path]:
    """Detect active user VLC skins installation directories."""
    return [t.skins_dir for t in detect_vlc_targets()]


def install_vlt(
    vlt_path: Path, target_dir: Path | None = None, *, activate: bool = False
) -> list[Path]:
    """Install a compiled `.vlt` skin into VLC's skins directory (or a custom directory)."""
    installed = install_vlt_to_targets(vlt_path, target_dir=target_dir, activate=activate)
    return [dest for _target, dest, _rc in installed]


def _resolve_config_from_args(args: argparse.Namespace) -> ThemeConfig:
    overrides = _parse_color_overrides(getattr(args, "override", None))
    if args.preset:
        base = ThemeConfig.from_preset(args.preset, scale=args.scale)
        # Allow CLI overrides on top of a preset
        return ThemeConfig(
            name=args.name or base.name,
            slug=args.slug or base.slug,
            seed=normalize_hex(args.seed) if args.seed else base.seed,
            mode=args.mode or base.mode,
            scheme=args.scheme or base.scheme,
            contrast=args.contrast if args.contrast is not None else base.contrast,
            scale=args.scale,
            color_overrides=overrides,
        )

    mode: ThemeMode = args.mode or "dark"
    contrast = args.contrast if args.contrast is not None else 0.0
    scale: float = args.scale

    if args.wallpaper:
        scheme: SchemeVariant = args.scheme or "content"
        stem = Path(args.wallpaper).stem
        scale_suffix = "" if abs(scale - 1.0) < 1e-6 else f"-{scale:g}x"
        slug = args.slug or f"m3-{_slugify(stem)}-{mode}{scale_suffix}"
        name = args.name or f"Material 3 {stem.title()} ({mode.title()})"
        cfg = ThemeConfig.from_wallpaper(
            args.wallpaper,
            name=name,
            slug=slug,
            mode=mode,
            scheme=scheme,
            contrast=contrast,
            scale=scale,
        )
        if overrides:
            return ThemeConfig(
                name=cfg.name,
                slug=cfg.slug,
                seed=cfg.seed,
                mode=cfg.mode,
                scheme=cfg.scheme,
                contrast=cfg.contrast,
                scale=cfg.scale,
                color_overrides=overrides,
            )
        return cfg

    seed = normalize_hex(args.seed or "#6750A4")
    scheme = args.scheme or "tonal-spot"
    scale_suffix = "" if abs(scale - 1.0) < 1e-6 else f"-{scale:g}x"
    slug = args.slug or f"m3-{seed[1:].lower()}-{mode}{scale_suffix}"
    name = args.name or f"Material 3 Custom {seed} ({mode.title()})"
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


def _cmd_presets(_args: argparse.Namespace) -> int:
    print(f"{'SLUG':<24} {'MODE':<8} {'SCHEME':<12} {'SEED':<9} DESCRIPTION")
    print("-" * 88)
    for p in CURATED_PRESETS:
        print(f"{p.slug:<24} {p.mode:<8} {p.scheme:<12} {p.seed:<9} {p.description}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    cfg = _resolve_config_from_args(args)
    out_dir = Path(args.out)
    need_unpacked = bool(args.keep_unpacked or args.preview)

    res = build_skin(cfg, out_dir, keep_unpacked=need_unpacked)
    size_kb = res.vlt_path.stat().st_size / 1024.0
    print(
        f"Built {res.vlt_path} ({size_kb:.1f} KiB) | "
        f"seed={res.tokens.config.seed} mode={cfg.mode} scheme={cfg.scheme} scale={cfg.scale:g}x | "
        f"DTD=OK ({res.validation.bitmap_count} bitmaps, {res.validation.subbitmap_count} sprites, "
        f"{res.validation.window_count} windows, {res.validation.layout_count} layouts)"
    )

    if args.preview and res.source_dir is not None:
        preview_dir = Path(args.preview_dir) if args.preview_dir else (out_dir / "previews")
        previews = render_skin_previews(res.source_dir, res.tokens, preview_dir)
        print(f"Rendered {len(previews)} previews in {preview_dir}:")
        for key, p in previews.items():
            print(f"  - {key}: {p}")
        if not args.keep_unpacked and res.source_dir.exists():
            shutil.rmtree(res.source_dir, ignore_errors=True)

    if args.install or args.activate or args.restart:
        do_activate = bool(args.activate or args.restart)
        results = install_vlt_to_targets(res.vlt_path, activate=do_activate)
        _print_install_summary(results, activated=do_activate)
        if args.restart and results:
            _ok, msg = restart_vlc(results[-1][1])
            print(msg)

    return 0


def _cmd_build_all(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    scales: list[float] = args.scales or [1.0]
    checksums: list[str] = []

    for scale in scales:
        for preset in CURATED_PRESETS:
            cfg = ThemeConfig.from_preset(preset.slug, scale=scale)
            res = build_skin(cfg, out_dir, keep_unpacked=False)
            digest = hashlib.sha256(res.vlt_path.read_bytes()).hexdigest()
            checksums.append(f"{digest}  {res.vlt_path.name}")
            size_kb = res.vlt_path.stat().st_size / 1024.0
            print(f"  [OK] {res.vlt_path.name:<34} {size_kb:6.1f} KiB")

    sums_path = out_dir / "SHA256SUMS.txt"
    sums_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"\nBuilt {len(checksums)} skins in {out_dir} (checksums: {sums_path})")
    return 0


def _cmd_inspect_tokens(args: argparse.Namespace) -> int:
    cfg = _resolve_config_from_args(args)
    tokens = DesignTokens.from_config(cfg)
    if args.json:
        print(tokens.to_json())
        return 0

    c = tokens.colors
    print(f"Theme: {cfg.name} ({cfg.slug})")
    print(
        f"Seed: {cfg.seed} | Mode: {cfg.mode} | Scheme: {cfg.scheme} | "
        f"Contrast: {cfg.contrast:+.1f} | Scale: {cfg.scale:g}x\n"
    )
    print("Key Material 3 Color Roles:")
    for key in (
        "primary",
        "on_primary",
        "primary_container",
        "on_primary_container",
        "secondary_container",
        "on_secondary_container",
        "surface",
        "surface_container_lowest",
        "surface_container_low",
        "surface_container",
        "surface_container_high",
        "surface_container_highest",
        "on_surface",
        "on_surface_variant",
        "outline",
        "outline_variant",
        "error",
        "error_container",
    ):
        print(f"  {key:<28} {getattr(c, key)}")

    print("\nWCAG 2.1 Contrast Checks:")
    pairs = [
        ("onPrimary / primary", c.on_primary, c.primary),
        ("onSurface / surfaceContainer", c.on_surface, c.surface_container),
        ("onSurfaceVariant / surfaceContainer", c.on_surface_variant, c.surface_container),
        ("onSecondaryContainer / secondaryContainer", c.on_secondary_container, c.secondary_container),
        ("primary / surfaceContainer", c.primary, c.surface_container),
    ]
    for label, fg, bg in pairs:
        cr = contrast_ratio(fg, bg)
        grade = "AAA" if cr >= 7.0 else ("AA" if cr >= 4.5 else ("AA-Large" if cr >= 3.0 else "FAIL"))
        print(f"  {label:<44} {cr:5.2f}:1  [{grade}]")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if target.is_dir():
        report = validate_skin_dir(target)
    elif target.is_file():
        with tempfile.TemporaryDirectory(prefix="m3vlc-validate-") as tmp:
            with tarfile.open(target, "r:*") as tar:
                tar.extractall(tmp, filter="data")
            # Locate extracted directory containing theme.xml
            matches = list(Path(tmp).rglob("theme.xml"))
            if not matches:
                print(f"FAIL: No theme.xml found inside {target}", file=sys.stderr)
                return 1
            report = validate_skin_dir(matches[0].parent)
    else:
        print(f"FAIL: Target does not exist: {target}", file=sys.stderr)
        return 1

    if report.ok:
        print(
            f"VALID: {target} ({report.bitmap_count} bitmaps, {report.subbitmap_count} subbitmaps, "
            f"{report.window_count} windows, {report.layout_count} layouts)"
        )
        for w in report.warnings:
            print(f"  WARN: {w}")
        return 0

    print(f"INVALID: {target} ({len(report.errors)} errors)", file=sys.stderr)
    for err in report.errors:
        print(f"  ERROR: {err}", file=sys.stderr)
    return 1


def _print_install_summary(
    results: list[tuple[VlcTarget, Path, Path | None]], *, activated: bool
) -> None:
    native_paths: list[str] = []
    activated_rcs: list[Path] = []
    for _target, dest, rc in results:
        native = to_vlc_native_path(dest)
        native_paths.append(native)
        print(f"Installed skin -> {dest}")
        if native != str(dest):
            print(f"  Windows path -> {native}")
        if rc is not None:
            activated_rcs.append(rc)

    if activated and activated_rcs:
        print("\nActivated skin automatically in VLC config:")
        for rc in activated_rcs:
            print(f"  Updated {rc} (backup saved as {rc.name}.m3vlc.bak)")
        print("Restart VLC (close any running VLC window first) to apply the Material 3 skin.")
        print("To switch back to VLC's default Qt UI anytime, run: m3vlc reset-ui")
        return

    sample_path = native_paths[-1] if native_paths else "<path-to-skin.vlt>"
    print("\nTo activate in VLC:")
    print("  Option 1 (Automatic — close VLC first):")
    print("    Re-run with `--activate` to set `intf=skins2` and `skins2-last` in `vlcrc`.")
    print("  Option 2 (Manual via VLC Preferences):")
    print("    1. Open VLC -> Tools -> Preferences (Ctrl+P)")
    print("    2. Interface -> Look and feel -> Use custom skin")
    print(f"    3. Under 'Skin resource file', click Choose... and select:\n       {sample_path}")
    print("    4. Click Save and restart VLC.")
    print("    (Tip: once Skins2 mode is active, right-click VLC -> Interface -> Select Skin")
    print("     to hot-switch between all .vlt skins installed in VLC's skins folder!)")
    print("  Option 3 (Quick one-shot test without changing preferences):")
    print(f'    vlc --intf skins2 --skins2-last "{sample_path}"')
    print("  Option 4 (Visual Material 3 Theme Studio with per-color pickers & 1-click VLC restart):")
    print("    m3vlc studio")


def _cmd_install(args: argparse.Namespace) -> int:
    target_dir = Path(args.target_dir) if args.target_dir else None
    do_activate = bool(args.activate or args.restart)
    results = install_vlt_to_targets(
        Path(args.vlt), target_dir=target_dir, activate=do_activate
    )
    _print_install_summary(results, activated=do_activate)
    if args.restart and results:
        _ok, msg = restart_vlc(results[-1][1])
        print(msg)
    return 0


def _cmd_reset_ui(_args: argparse.Namespace) -> int:
    reverted = 0
    for target in detect_vlc_targets():
        if target.vlcrc_path is not None and reset_vlc_to_native_ui(target.vlcrc_path):
            print(f"Reverted to native VLC UI -> {target.vlcrc_path}")
            reverted += 1
    if reverted == 0:
        print("No existing vlcrc files found to revert.")
    else:
        print("Restart VLC to return to the native Qt interface.")
    return 0


def _cmd_install_all(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    scales: list[float] = args.scales or [1.0]
    target_dir = Path(args.target_dir) if args.target_dir else None
    installed_count = 0
    activated_dest: Path | None = None

    for scale in scales:
        for preset in CURATED_PRESETS:
            cfg = ThemeConfig.from_preset(preset.slug, scale=scale)
            res = build_skin(cfg, out_dir, keep_unpacked=False)
            should_activate = bool(args.activate_preset and cfg.slug == args.activate_preset)
            results = install_vlt_to_targets(
                res.vlt_path, target_dir=target_dir, activate=should_activate
            )
            if should_activate and results:
                activated_dest = results[-1][1]
            tag = " [ACTIVE]" if should_activate else ""
            print(f"  [INSTALLED] {res.vlt_path.name}{tag}")
            installed_count += 1

    print(f"\nInstalled {installed_count} Material 3 skins into VLC's skins folder!")
    print("You can now hot-switch palettes LIVE inside VLC via:")
    print("  - Control Center (tune icon) -> Switch Theme / Palette (palette icon), OR")
    print("  - Right-click VLC -> Interface -> Select Skin")
    print("Or launch the interactive per-color Material 3 Theme Studio:")
    print("  - m3vlc studio")
    if args.restart and activated_dest is not None:
        _ok, msg = restart_vlc(activated_dest)
        print(msg)
    return 0


def _cmd_studio(args: argparse.Namespace) -> int:
    return run_studio(
        host=args.host,
        port=args.port,
        output_dir=Path(args.out),
        open_browser=not bool(args.no_browser),
    )


def _sync_once(args: argparse.Namespace, last_fp: str | None) -> str:
    source: DynamicSource = args.source
    mode_override: ThemeMode | None = None if args.mode == "auto" else args.mode
    snap = detect_system_theme(source=source, mode_override=mode_override)
    if snap.fingerprint == last_fp:
        return snap.fingerprint

    scale: float = args.scale
    scale_suffix = "" if abs(scale - 1.0) < 1e-6 else f"-{scale:g}x"
    slug = args.slug or f"m3-dynamic{scale_suffix}"
    cfg = ThemeConfig(
        name=f"Material 3 Dynamic ({snap.mode.title()} {snap.seed})",
        slug=slug,
        seed=snap.seed,
        mode=snap.mode,
        scheme=args.scheme,
        contrast=args.contrast,
        scale=scale,
    )
    out_dir = Path(args.out)
    need_unpacked = bool(args.preview)
    res = build_skin(cfg, out_dir, keep_unpacked=need_unpacked)
    print(
        f"[SYNC] source={snap.source_kind} ({snap.source_detail}) -> "
        f"seed={snap.seed} mode={snap.mode} scheme={cfg.scheme} -> {res.vlt_path}"
    )

    if args.preview and res.source_dir is not None:
        preview_dir = out_dir / "previews"
        render_skin_previews(res.source_dir, res.tokens, preview_dir)
        shutil.rmtree(res.source_dir, ignore_errors=True)

    results = install_vlt_to_targets(
        res.vlt_path, activate=bool(args.activate or args.restart)
    )
    if last_fp is None:
        _print_install_summary(results, activated=bool(args.activate or args.restart))
    else:
        for _target, dest, _rc in results:
            print(f"  Updated -> {to_vlc_native_path(dest)}")
    if args.restart and results:
        _ok, msg = restart_vlc(results[-1][1])
        print(msg)
    return snap.fingerprint


def _cmd_sync(args: argparse.Namespace) -> int:
    last_fp = _sync_once(args, None)
    if not args.watch:
        return 0

    interval = max(1.0, float(args.interval))
    print(f"\nWatching OS wallpaper/theme changes every {interval:g}s (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(interval)
            last_fp = _sync_once(args, last_fp)
    except KeyboardInterrupt:
        print("\nStopped dynamic color sync watcher.")
    return 0


def _add_theme_selection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--preset", help="Curated preset slug (run `m3vlc presets` to list).")
    parser.add_argument("--seed", help="Custom Material 3 seed color in #RRGGBB format.")
    parser.add_argument("--wallpaper", help="Extract dynamic Material You seed color from an image.")
    parser.add_argument("--mode", choices=MODE_CHOICES, help="Color theme mode (dark, light, amoled).")
    parser.add_argument("--scheme", choices=SCHEME_CHOICES, help="Material 3 HCT scheme variant.")
    parser.add_argument(
        "--contrast",
        type=_parse_contrast,
        default=None,
        help="Contrast level: standard (0.0), medium (0.5), high (1.0), or float in [-1.0, 1.0].",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="HiDPI scale factor (e.g. 1.0, 1.25, 1.5, 2.0). Default: 1.0.",
    )
    parser.add_argument("--name", help="Override human-readable theme display name.")
    parser.add_argument("--slug", help="Override output filename slug (without .vlt).")
    parser.add_argument(
        "--override",
        action="append",
        metavar="ROLE=#HEX",
        help="Override a specific Material 3 color role (repeatable, e.g. --override primary=#FFB74D).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="m3vlc",
        description="Material 3 (Material You) design-token skin engine for VLC Media Player.",
    )
    parser.add_argument("--version", action="version", version=f"material3-vlc {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_presets = sub.add_parser("presets", help="List curated Material 3 skin presets.")
    p_presets.set_defaults(func=_cmd_presets)

    p_build = sub.add_parser("build", help="Build a single Material 3 `.vlt` skin.")
    _add_theme_selection_args(p_build)
    p_build.add_argument("-o", "--out", default="dist", help="Output directory (default: dist).")
    p_build.add_argument("--keep-unpacked", action="store_true", help="Keep unpacked source directory.")
    p_build.add_argument("--preview", action="store_true", help="Render PNG mockups of all layouts.")
    p_build.add_argument("--preview-dir", help="Custom output directory for rendered previews.")
    p_build.add_argument(
        "--install", action="store_true", help="Copy the compiled `.vlt` into VLC's skins folder."
    )
    p_build.add_argument(
        "--activate",
        action="store_true",
        help="Install AND activate the skin in VLC's `vlcrc`.",
    )
    p_build.add_argument(
        "--restart",
        action="store_true",
        help="Install, activate in `vlcrc`, and automatically restart VLC with the new skin.",
    )
    p_build.set_defaults(func=_cmd_build)

    p_all = sub.add_parser("build-all", help="Build all curated preset `.vlt` skins + SHA256SUMS.")
    p_all.add_argument("-o", "--out", default="dist", help="Output directory (default: dist).")
    p_all.add_argument(
        "--scales",
        type=float,
        nargs="+",
        default=[1.0],
        help="One or more HiDPI scales to build (e.g. --scales 1.0 2.0).",
    )
    p_all.set_defaults(func=_cmd_build_all)

    p_tokens = sub.add_parser("inspect-tokens", help="Inspect generated Material 3 tokens & contrast.")
    _add_theme_selection_args(p_tokens)
    p_tokens.add_argument("--json", action="store_true", help="Emit complete tokens as JSON.")
    p_tokens.set_defaults(func=_cmd_inspect_tokens)

    p_val = sub.add_parser("validate", help="Validate an unpacked skin dir or `.vlt` archive.")
    p_val.add_argument("target", help="Path to a skin directory or `.vlt` file.")
    p_val.set_defaults(func=_cmd_validate)

    p_inst = sub.add_parser("install", help="Install a `.vlt` file into VLC's skins directory.")
    p_inst.add_argument("vlt", help="Path to the `.vlt` file to install.")
    p_inst.add_argument("--target-dir", help="Override destination skins directory.")
    p_inst.add_argument(
        "--activate",
        action="store_true",
        help="Also set `intf=skins2` and `skins2-last` in VLC's `vlcrc`.",
    )
    p_inst.add_argument(
        "--restart",
        action="store_true",
        help="Activate and restart VLC automatically with the installed skin.",
    )
    p_inst.set_defaults(func=_cmd_install)

    p_reset = sub.add_parser("reset-ui", help="Revert VLC's `vlcrc` back to the native Qt interface.")
    p_reset.set_defaults(func=_cmd_reset_ui)

    p_inst_all = sub.add_parser(
        "install-all",
        help="Build and install ALL curated presets into VLC for live palette switching.",
    )
    p_inst_all.add_argument("-o", "--out", default="dist", help="Output directory (default: dist).")
    p_inst_all.add_argument(
        "--scales",
        type=float,
        nargs="+",
        default=[1.0],
        help="One or more HiDPI scales to build and install.",
    )
    p_inst_all.add_argument("--target-dir", help="Override destination skins directory.")
    p_inst_all.add_argument(
        "--activate-preset",
        help="Preset slug to activate in VLC `vlcrc` after installing all palettes (e.g. m3-brown-dark).",
    )
    p_inst_all.add_argument(
        "--restart",
        action="store_true",
        help="Restart VLC automatically after activating `--activate-preset`.",
    )
    p_inst_all.set_defaults(func=_cmd_install_all)

    p_studio = sub.add_parser(
        "studio",
        help="Launch the local Material 3 Theme Studio (per-role color pickers & 1-click VLC restart).",
    )
    p_studio.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    p_studio.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765).")
    p_studio.add_argument("-o", "--out", default="dist", help="Output directory for built skins.")
    p_studio.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the Studio URL in the default browser.",
    )
    p_studio.set_defaults(func=_cmd_studio)

    p_sync = sub.add_parser(
        "sync",
        help="Sync Material You Dynamic Colors from your OS wallpaper/accent & Dark/Light mode.",
    )
    p_sync.add_argument(
        "--source",
        choices=("auto", "wallpaper", "accent"),
        default="auto",
        help="Dynamic color source: desktop wallpaper, OS accent, or auto (default: auto).",
    )
    p_sync.add_argument(
        "--mode",
        choices=("auto", "dark", "light", "amoled"),
        default="auto",
        help="Theme mode: auto-detect from OS, or force dark/light/amoled (default: auto).",
    )
    p_sync.add_argument(
        "--scheme",
        choices=SCHEME_CHOICES,
        default="content",
        help="Material 3 HCT harmony scheme (default: content).",
    )
    p_sync.add_argument(
        "--contrast",
        type=_parse_contrast,
        default=0.0,
        help="Contrast level: standard, medium, high, or float in [-1.0, 1.0].",
    )
    p_sync.add_argument("--scale", type=float, default=1.0, help="HiDPI scale factor (default: 1.0).")
    p_sync.add_argument("--slug", help="Custom output slug (default: m3-dynamic).")
    p_sync.add_argument("-o", "--out", default="dist", help="Output directory (default: dist).")
    p_sync.add_argument("--preview", action="store_true", help="Also render preview PNGs.")
    p_sync.add_argument(
        "--activate",
        action="store_true",
        help="Activate `m3-dynamic.vlt` in VLC's `vlcrc`.",
    )
    p_sync.add_argument(
        "--restart",
        action="store_true",
        help="Activate and automatically restart VLC whenever the dynamic skin is rebuilt.",
    )
    p_sync.add_argument(
        "--watch",
        action="store_true",
        help="Continuously watch OS wallpaper/theme changes and rebuild automatically.",
    )
    p_sync.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds when `--watch` is active (default: 5).",
    )
    p_sync.set_defaults(func=_cmd_sync)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
