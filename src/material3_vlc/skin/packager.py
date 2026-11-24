"""End-to-end Material 3 VLC skin builder and reproducible `.vlt` packager."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from material3_vlc.render.sprites import render_all_skin_assets
from material3_vlc.render.svg import find_assets_dir
from material3_vlc.skin.metrics import SkinMetrics
from material3_vlc.skin.validator import ValidationReport, validate_skin_dir
from material3_vlc.skin.xml_builder import build_theme_xml
from material3_vlc.tokens.theme import DesignTokens, ThemeConfig


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Artifacts produced by compiling a Material 3 VLC skin."""

    tokens: DesignTokens
    metrics: SkinMetrics
    vlt_path: Path
    source_dir: Path | None
    validation: ValidationReport


def _reset_tarinfo(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """Normalize TarInfo metadata so `.vlt` builds are byte-for-byte reproducible."""
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 1704067200  # 2024-01-01T00:00:00Z
    info.mode = 0o755 if info.isdir() else 0o644
    return info


def package_vlt(skin_dir: Path, vlt_path: Path, root_name: str) -> Path:
    """Package `skin_dir` into a deterministic gzip-compressed tar `.vlt` archive.

    VLC Skins2 expects `<root_name>/theme.xml` and `<root_name>/...` inside a `.tar.gz`
    file renamed with the `.vlt` extension.
    """
    vlt_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort all entries deterministically before archiving
    all_files = sorted(p for p in skin_dir.rglob("*") if p.is_file())
    with tarfile.open(vlt_path, mode="w:gz", format=tarfile.USTAR_FORMAT, compresslevel=9) as tar:
        for file_path in all_files:
            rel = file_path.relative_to(skin_dir)
            arcname = f"{root_name}/{rel.as_posix()}"
            tar.add(file_path, arcname=arcname, filter=_reset_tarinfo)

    return vlt_path


def build_skin(
    config: ThemeConfig,
    output_dir: Path,
    *,
    keep_unpacked: bool = False,
    export_tokens: bool = True,
) -> BuildResult:
    """Compile a complete Material 3 VLC `.vlt` skin from a `ThemeConfig`.

    Steps:
    1. Resolve Material 3 HCT color, shape, typography, and elevation tokens.
    2. Compute scaled geometry metrics (`1x`, `1.25x`, `1.5x`, `2x`).
    3. Rasterize Material Symbols icon atlases, M3 Expressive sliders, and surfaces.
    4. Copy bundled Apache-2.0 Roboto TTF fonts.
    5. Generate `theme.xml` and validate against official VLC `skin.dtd` + semantic checks.
    6. Package into a reproducible `<slug>.vlt` archive.
    """
    tokens = DesignTokens.from_config(config)
    metrics = SkinMetrics.for_scale(config.scale)
    output_dir.mkdir(parents=True, exist_ok=True)
    vlt_path = output_dir / f"{config.slug}.vlt"

    fonts_src = find_assets_dir() / "fonts"

    if keep_unpacked:
        work_dir = output_dir / config.slug
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        work_dir = Path(tempfile.mkdtemp(prefix=f"m3vlc-{config.slug}-"))
        cleanup = True

    try:
        # 1. Render PNG bitmaps and sprite sheets
        bitmaps = render_all_skin_assets(tokens, metrics, work_dir / "images")

        # 2. Bundle Apache-2.0 Roboto static TTFs
        fonts_dst = work_dir / "fonts"
        fonts_dst.mkdir(parents=True, exist_ok=True)
        for font_name in ("Roboto-Regular.ttf", "Roboto-Medium.ttf"):
            shutil.copy2(fonts_src / font_name, fonts_dst / font_name)

        # 3. Emit theme.xml (and optional tokens.json metadata for inspection)
        xml_bytes = build_theme_xml(tokens, metrics, bitmaps)
        (work_dir / "theme.xml").write_bytes(xml_bytes)
        if export_tokens:
            (work_dir / "tokens.json").write_text(tokens.to_json() + "\n", encoding="utf-8")

        # 4. Validate strictly before packaging
        report = validate_skin_dir(work_dir)
        if not report.ok:
            joined = "\n  - ".join(report.errors)
            raise RuntimeError(f"Generated skin '{config.slug}' failed validation:\n  - {joined}")

        # 5. Package deterministic .vlt
        package_vlt(work_dir, vlt_path, root_name=config.slug)

        return BuildResult(
            tokens=tokens,
            metrics=metrics,
            vlt_path=vlt_path,
            source_dir=work_dir if keep_unpacked else None,
            validation=report,
        )
    finally:
        if cleanup and work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
