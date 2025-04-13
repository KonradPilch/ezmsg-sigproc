import numpy as np
from ezmsg.util.messages.axisarray import AxisArray
from ezmsg.util.messages.util import replace

from ..base import BaseTransformer, BaseTransformerUnit, processor_settings


@processor_settings
class ClipSettings:
    a_min: float
    """Lower clip bound."""

    a_max: float
    """Upper clip bound."""


class ClipTransformer(BaseTransformer[ClipSettings, AxisArray, AxisArray]):
    def _process(self, message: AxisArray) -> AxisArray:
        return replace(
            message,
            data=np.clip(message.data, self.settings.a_min, self.settings.a_max),
        )


class Clip(BaseTransformerUnit[ClipSettings, AxisArray, AxisArray, ClipTransformer]):
    SETTINGS = ClipSettings


def clip(a_min: float, a_max: float) -> ClipTransformer:
    """
    Clips the data to be within the specified range. See :obj:`np.clip` for more details.

    Args:
        a_min: Lower clip bound
        a_max: Upper clip bound

    Returns: :obj:`ClipTransformer`.

    """
    return ClipTransformer(ClipSettings(a_min=a_min, a_max=a_max))
