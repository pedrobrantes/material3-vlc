"""Material 3 Tonal Elevation and State Layer specifications.

Reference:
- Elevation: https://m3.material.io/styles/elevation/tokens
- Interaction States: https://m3.material.io/foundations/interaction/states/state-layers
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateLayerTokens:
    """Official Material 3 state layer opacities."""

    hover: float = 0.08
    focus: float = 0.10
    pressed: float = 0.10
    dragged: float = 0.16
    disabled_container: float = 0.12
    disabled_content: float = 0.38


@dataclass(frozen=True, slots=True)
class ElevationTokens:
    """Material 3 elevation levels mapped to semantic surface container roles."""

    level0: str = "surface"
    level1: str = "surfaceContainerLow"
    level2: str = "surfaceContainer"
    level3: str = "surfaceContainerHigh"
    level4: str = "surfaceContainerHigh"
    level5: str = "surfaceContainerHighest"


STATE_LAYERS = StateLayerTokens()
ELEVATION = ElevationTokens()
