"""Material 3 Shape scale tokens.

Reference: https://m3.material.io/styles/shape/shape-scale-tokens
All values are specified in logical dp and scaled cleanly by the target HiDPI factor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShapeTokens:
    """Material 3 corner radius tokens in physical pixels for a given scale."""

    none: int
    extra_small: int
    small: int
    medium: int
    large: int
    extra_large: int
    full: int

    @classmethod
    def for_scale(cls, scale: float = 1.0) -> ShapeTokens:
        """Compute pixel corner radii from M3 dp tokens at the given scale factor."""
        return cls(
            none=0,
            extra_small=max(1, round(4 * scale)),
            small=max(1, round(8 * scale)),
            medium=max(1, round(12 * scale)),
            large=max(1, round(16 * scale)),
            extra_large=max(1, round(28 * scale)),
            full=9999,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "none": self.none,
            "extraSmall": self.extra_small,
            "small": self.small,
            "medium": self.medium,
            "large": self.large,
            "extraLarge": self.extra_large,
            "full": self.full,
        }
