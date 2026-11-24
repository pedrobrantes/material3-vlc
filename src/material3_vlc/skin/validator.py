"""Comprehensive VLC Skins2 validator: official `skin.dtd` + semantic referential checks.

Catches errors before VLC ever loads the `.vlt` archive:
1. XML well-formedness and strict validation against VLC 3.0.x `skin.dtd`
2. Every referenced Bitmap/SubBitmap ID exists (and no duplicate IDs)
3. Every referenced Font ID exists and every declared file exists on disk
4. Every Window/Layout/PopupMenu referenced in actions (`win.show()`, `win.setLayout(id)`) exists
5. Every VLC built-in action & boolean variable matches VLC 3.0.x `interpreter.cpp`
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from material3_vlc.render.svg import find_assets_dir

VALID_BUILTIN_ACTIONS: frozenset[str] = frozenset(
    {
        "none",
        "move",
        "resizeS",
        "resizeE",
        "resizeSE",
        "dialogs.changeSkin()",
        "dialogs.fileSimple()",
        "dialogs.file()",
        "dialogs.directory()",
        "dialogs.disc()",
        "dialogs.net()",
        "dialogs.playlist()",
        "dialogs.messages()",
        "dialogs.prefs()",
        "dialogs.fileInfo()",
        "dialogs.streamingWizard()",
        "dialogs.popup()",
        "dialogs.audioPopup()",
        "dialogs.videoPopup()",
        "dialogs.miscPopup()",
        "dvd.nextTitle()",
        "dvd.previousTitle()",
        "dvd.nextChapter()",
        "dvd.previousChapter()",
        "dvd.rootMenu()",
        "playlist.load()",
        "playlist.save()",
        "playlist.add()",
        "playlist.next()",
        "playlist.previous()",
        "playlist.setRandom(true)",
        "playlist.setRandom(false)",
        "playlist.setLoop(true)",
        "playlist.setLoop(false)",
        "playlist.setRepeat(true)",
        "playlist.setRepeat(false)",
        "playlist.del()",
        "playlist.sort()",
        "vlc.fullscreen()",
        "vlc.play()",
        "vlc.pause()",
        "vlc.stop()",
        "vlc.faster()",
        "vlc.slower()",
        "vlc.mute()",
        "vlc.volumeUp()",
        "vlc.volumeDown()",
        "vlc.minimize()",
        "vlc.onTop()",
        "vlc.snapshot()",
        "vlc.toggleRecord()",
        "vlc.nextFrame()",
        "vlc.quit()",
        "equalizer.enable()",
        "equalizer.disable()",
    }
)

VALID_BUILTIN_BOOLS: frozenset[str] = frozenset(
    {
        "true",
        "false",
        "playlist.isRandom",
        "playlist.isLoop",
        "playlist.isRepeat",
        "playtree.isRandom",
        "playtree.isLoop",
        "playtree.isRepeat",
        "vlc.isPlaying",
        "vlc.isStopped",
        "vlc.isPaused",
        "vlc.isSeekable",
        "vlc.canRecord",
        "vlc.isRecording",
        "vlc.isFullscreen",
        "vlc.hasVout",
        "vlc.hasAudio",
        "vlc.isMute",
        "vlc.isOnTop",
        "dvd.isActive",
        "equalizer.isEnabled",
    }
)

VALID_SLIDER_VALUES: frozenset[str] = frozenset(
    {
        "none",
        "time",
        "volume",
        "equalizer.preamp",
        *(f"equalizer.band({i})" for i in range(10)),
    }
)

_SET_LAYOUT_RE = re.compile(r"^([A-Za-z0-9_.-]+)\.setLayout\(([A-Za-z0-9_.-]+)\)$")
_WIN_METHOD_RE = re.compile(r"^([A-Za-z0-9_.-]+)\.(show|hide|maximize|unmaximize)\(\)$")
_BOOL_TOKEN_RE = re.compile(r"[A-Za-z0-9_.-]+(?:\(\))?")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Result of validating a VLC Skins2 directory."""

    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    bitmap_count: int
    subbitmap_count: int
    window_count: int
    layout_count: int


def validate_skin_dir(skin_dir: Path, dtd_path: Path | None = None) -> ValidationReport:
    """Validate `skin_dir/theme.xml` against official `skin.dtd` and semantic Skins2 rules."""
    errors: list[str] = []
    warnings: list[str] = []

    xml_path = skin_dir / "theme.xml"
    if not xml_path.is_file():
        return ValidationReport(
            ok=False,
            errors=(f"Missing theme.xml in {skin_dir}",),
            warnings=(),
            bitmap_count=0,
            subbitmap_count=0,
            window_count=0,
            layout_count=0,
        )

    dtd_file = dtd_path or (find_assets_dir() / "schema" / "skin.dtd")
    dtd = etree.DTD(str(dtd_file))

    parser = etree.XMLParser(load_dtd=False, no_network=True, remove_comments=True)
    try:
        tree = etree.parse(str(xml_path), parser)
    except etree.XMLSyntaxError as exc:
        return ValidationReport(
            ok=False,
            errors=(f"XML syntax error: {exc}",),
            warnings=(),
            bitmap_count=0,
            subbitmap_count=0,
            window_count=0,
            layout_count=0,
        )

    root = tree.getroot()
    if not dtd.validate(root):
        for entry in dtd.error_log:
            errors.append(f"DTD line {entry.line}: {entry.message}")

    # Collect declared symbols
    bitmap_ids: set[str] = set()
    font_ids: set[str] = {"defaultfont"}
    window_ids: set[str] = set()
    layout_ids: set[str] = set()
    popup_ids: set[str] = set()
    control_ids: set[str] = set()

    bitmap_count = 0
    subbitmap_count = 0

    for bmp in root.findall("Bitmap"):
        bitmap_count += 1
        bid = bmp.get("id", "")
        bfile = bmp.get("file", "")
        if bid in bitmap_ids:
            errors.append(f"Duplicate Bitmap id '{bid}'")
        bitmap_ids.add(bid)
        if not (skin_dir / bfile).is_file():
            errors.append(f"Bitmap '{bid}' references missing file '{bfile}'")
        for sub in bmp.findall("SubBitmap"):
            subbitmap_count += 1
            sid = sub.get("id", "")
            if sid in bitmap_ids:
                errors.append(f"Duplicate SubBitmap id '{sid}'")
            bitmap_ids.add(sid)

    for font in root.findall("Font"):
        fid = font.get("id", "")
        ffile = font.get("file", "")
        if fid in font_ids:
            errors.append(f"Duplicate Font id '{fid}'")
        font_ids.add(fid)
        if not (skin_dir / ffile).is_file():
            errors.append(f"Font '{fid}' references missing file '{ffile}'")

    for popup in root.findall("PopupMenu"):
        pid = popup.get("id", "")
        if pid in popup_ids:
            errors.append(f"Duplicate PopupMenu id '{pid}'")
        popup_ids.add(pid)

    for win in root.findall("Window"):
        wid = win.get("id", "")
        if wid in window_ids:
            errors.append(f"Duplicate Window id '{wid}'")
        window_ids.add(wid)
        for lay in win.findall("Layout"):
            lid = lay.get("id", "")
            if lid in layout_ids:
                errors.append(f"Duplicate Layout id '{lid}'")
            layout_ids.add(lid)

    def check_bmp_ref(el: etree._Element, attr: str, allow_none: bool = True) -> None:
        val = el.get(attr)
        if val is None:
            return
        if allow_none and val == "none":
            return
        if val not in bitmap_ids:
            errors.append(
                f"<{el.tag!s} id='{el.get('id', '')}'> {attr}='{val}' not found in Bitmaps"
            )

    def check_action(el: etree._Element, attr: str) -> None:
        raw = el.get(attr)
        if not raw or raw == "none":
            return
        for part in [p.strip() for p in raw.split(";") if p.strip()]:
            if part in VALID_BUILTIN_ACTIONS:
                continue
            m_set = _SET_LAYOUT_RE.match(part)
            if m_set:
                w_ref, l_ref = m_set.group(1), m_set.group(2)
                if w_ref not in window_ids:
                    errors.append(f"Action '{part}' references unknown Window '{w_ref}'")
                if l_ref not in layout_ids:
                    errors.append(f"Action '{part}' references unknown Layout '{l_ref}'")
                continue
            m_win = _WIN_METHOD_RE.match(part)
            if m_win:
                target, method = m_win.group(1), m_win.group(2)
                if method == "show" and target in popup_ids:
                    continue
                if target not in window_ids:
                    errors.append(f"Action '{part}' references unknown Window/Popup '{target}'")
                continue
            errors.append(f"Unknown Skins2 action '{part}' on <{el.tag!s} id='{el.get('id', '')}'>")

    def check_bool(el: etree._Element, attr: str) -> None:
        expr = el.get(attr)
        if not expr:
            return
        for tok in _BOOL_TOKEN_RE.findall(expr):
            if tok in ("and", "or", "not") or tok in VALID_BUILTIN_BOOLS:
                continue
            if tok.endswith(".isVisible"):
                w_ref = tok.removesuffix(".isVisible")
                if w_ref not in window_ids:
                    errors.append(f"Boolean '{tok}' references unknown Window '{w_ref}'")
                continue
            if tok.endswith(".isMaximized()") or tok.endswith(".isMaximized"):
                w_ref = tok.split(".isMaximized")[0]
                if w_ref not in window_ids:
                    errors.append(f"Boolean '{tok}' references unknown Window '{w_ref}'")
                continue
            if tok.endswith(".isActive"):
                l_ref = tok.removesuffix(".isActive")
                if l_ref not in layout_ids:
                    errors.append(f"Boolean '{tok}' references unknown Layout '{l_ref}'")
                continue
            errors.append(f"Unknown boolean variable '{tok}' in {attr}='{expr}'")

    # Traverse every element for referential & semantic integrity
    for el in root.iter():
        tag = el.tag
        if tag in ("Image", "Button", "Checkbox", "Slider", "Text", "Playtree", "Video", "Panel"):
            cid = el.get("id")
            if cid and cid != "none":
                if cid in control_ids:
                    warnings.append(f"Duplicate control id '{cid}'")
                control_ids.add(cid)
            check_bool(el, "visible")

        if tag == "Image":
            check_bmp_ref(el, "image", allow_none=False)
            check_action(el, "action")
            check_action(el, "action2")
        elif tag == "Button":
            check_bmp_ref(el, "up", allow_none=False)
            check_bmp_ref(el, "over")
            check_bmp_ref(el, "down")
            check_action(el, "action")
        elif tag == "Checkbox":
            for a in ("up1", "up2"):
                check_bmp_ref(el, a, allow_none=False)
            for a in ("over1", "down1", "over2", "down2"):
                check_bmp_ref(el, a)
            check_bool(el, "state")
            check_action(el, "action1")
            check_action(el, "action2")
        elif tag == "Slider":
            check_bmp_ref(el, "up", allow_none=False)
            check_bmp_ref(el, "over")
            check_bmp_ref(el, "down")
            val = el.get("value", "none")
            if val not in VALID_SLIDER_VALUES:
                errors.append(f"Slider '{el.get('id', '')}' has unknown value '{val}'")
            if el.get("width") is not None or el.get("height") is not None:
                errors.append(
                    f"Slider '{el.get('id', '')}' must omit explicit width/height "
                    "(VLC Bezier::getHeight() distorts slider scaling when width/height are set)"
                )
        elif tag == "SliderBackground":
            check_bmp_ref(el, "image", allow_none=False)
        elif tag == "Text":
            fid = el.get("font", "")
            if fid not in font_ids:
                errors.append(f"Text '{el.get('id', '')}' references unknown font '{fid}'")
        elif tag == "Playtree":
            fid = el.get("font", "")
            if fid not in font_ids:
                errors.append(f"Playtree '{el.get('id', '')}' references unknown font '{fid}'")
            for a in ("bgimage", "itemimage", "openimage", "closedimage"):
                check_bmp_ref(el, a)
        elif tag == "MenuItem":
            check_action(el, "action")

    # Verify required tooltipfont (VLC Builder loads Theme before custom Fonts)
    tf = root.get("tooltipfont", "defaultfont")
    if tf != "defaultfont":
        errors.append(
            f"Theme tooltipfont='{tf}' must be 'defaultfont' (VLC invokes addTheme before addFont)"
        )

    return ValidationReport(
        ok=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        bitmap_count=bitmap_count,
        subbitmap_count=subbitmap_count,
        window_count=len(window_ids),
        layout_count=len(layout_ids),
    )
