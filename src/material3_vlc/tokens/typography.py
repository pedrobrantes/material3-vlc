"""Material 3 Typescale tokens mapped to VLC Skins2 FreeType fonts.

Reference: https://m3.material.io/styles/typography/type-scale-tokens
VLC Skins2 uses FreeType2 static TTF files (`Roboto-Regular.ttf`, `Roboto-Medium.ttf`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FontSpec:
    """A single VLC Skins2 `<Font>` declaration derived from an M3 typescale role."""

    id: str
    file: str
    size: int
    role: str
    weight: int


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    """Complete typography ramp for Material 3 VLC layouts."""

    title_large: FontSpec
    title_medium: FontSpec
    title_small: FontSpec
    body_medium: FontSpec
    body_small: FontSpec
    label_large: FontSpec
    label_medium: FontSpec
    label_small: FontSpec

    @classmethod
    def for_scale(cls, scale: float = 1.0) -> TypographyTokens:
        """Compute scaled font sizes (FreeType pixel heights) from M3 typescale."""

        def sz(dp: int) -> int:
            return max(8, round(dp * scale))

        return cls(
            title_large=FontSpec(
                id="font_title_large",
                file="fonts/Roboto-Medium.ttf",
                size=sz(18),
                role="titleLarge",
                weight=500,
            ),
            title_medium=FontSpec(
                id="font_title_medium",
                file="fonts/Roboto-Medium.ttf",
                size=sz(14),
                role="titleMedium",
                weight=500,
            ),
            title_small=FontSpec(
                id="font_title_small",
                file="fonts/Roboto-Medium.ttf",
                size=sz(13),
                role="titleSmall",
                weight=500,
            ),
            body_medium=FontSpec(
                id="font_body_medium",
                file="fonts/Roboto-Regular.ttf",
                size=sz(13),
                role="bodyMedium",
                weight=400,
            ),
            body_small=FontSpec(
                id="font_body_small",
                file="fonts/Roboto-Regular.ttf",
                size=sz(12),
                role="bodySmall",
                weight=400,
            ),
            label_large=FontSpec(
                id="font_label_large",
                file="fonts/Roboto-Medium.ttf",
                size=sz(12),
                role="labelLarge",
                weight=500,
            ),
            label_medium=FontSpec(
                id="font_label_medium",
                file="fonts/Roboto-Medium.ttf",
                size=sz(11),
                role="labelMedium",
                weight=500,
            ),
            label_small=FontSpec(
                id="font_label_small",
                file="fonts/Roboto-Regular.ttf",
                size=sz(10),
                role="labelSmall",
                weight=400,
            ),
        )

    def all_fonts(self) -> tuple[FontSpec, ...]:
        return (
            self.title_large,
            self.title_medium,
            self.title_small,
            self.body_medium,
            self.body_small,
            self.label_large,
            self.label_medium,
            self.label_small,
        )

    def to_dict(self) -> dict[str, dict[str, str | int]]:
        return {
            f.role: {"id": f.id, "file": f.file, "size": f.size, "weight": f.weight}
            for f in self.all_fonts()
        }
