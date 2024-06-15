from dataclasses import replace
import typing

import numpy as np
import ezmsg.core as ez
from ezmsg.util.messages.axisarray import AxisArray, slice_along_axis
from ezmsg.util.generator import consumer, GenAxisArray


"""
Slicer:Select a subset of data along a particular axis.
"""


def parse_slice(s: str) -> typing.Tuple[typing.Union[slice, int], ...]:
    """
    Parses a string representation of a slice and returns a tuple of slice objects.

    - "" -> slice(None, None, None)  (take all)
    - ":" -> slice(None, None, None)
    - '"none"` (case-insensitive) -> slice(None, None, None)
    - "{start}:{stop}" or {start}:{stop}:{step} -> slice(start, stop, step)
    - "5" (or any integer) -> (5,). Take only that item.
        applying this to a ndarray or AxisArray will drop the dimension.
    - A comma-separated list of the above -> a tuple of slices | ints

    Args:
        s: The string representation of the slice.

    Returns:
        A tuple of slice objects and/or ints.
    """
    if s.lower() in ["", ":", "none"]:
        return (slice(None),)
    if "," not in s:
        parts = [part.strip() for part in s.split(":")]
        if len(parts) == 1:
            return (int(parts[0]),)
        return (slice(*(int(part.strip()) if part else None for part in parts)),)
    l = [parse_slice(_) for _ in s.split(",")]
    return tuple([item for sublist in l for item in sublist])


@consumer
def slicer(
    selection: str = "", axis: typing.Optional[str] = None
) -> typing.Generator[AxisArray, AxisArray, None]:
    axis_arr_in = AxisArray(np.array([]), dims=[""])
    axis_arr_out = AxisArray(np.array([]), dims=[""])
    _slice = None
    b_change_dims = False
    new_axis = None  # Will hold updated metadata

    while True:
        axis_arr_in = yield axis_arr_out

        if axis is None:
            axis = axis_arr_in.dims[-1]
        axis_idx = axis_arr_in.get_axis_idx(axis)

        if _slice is None:
            # Calculate the slice
            _slices = parse_slice(selection)
            if len(_slices) == 1:
                _slice = _slices[0]
                b_change_dims = isinstance(_slice, int)  # If we drop the sliced dimension
            else:
                # Multiple slices, but this cannot be done in a single step, so we convert the slices
                #  to a discontinuous set of integer indexes.
                indices = np.arange(axis_arr_in.data.shape[axis_idx])
                indices = np.hstack([indices[_] for _ in _slices])
                _slice = np.s_[indices]
            # Create the output axis.
            if (axis in axis_arr_in.axes
                    and hasattr(axis_arr_in.axes[axis], "labels")
                    and len(axis_arr_in.axes[axis].labels) > 0):
                new_labels = axis_arr_in.axes[axis].labels[_slice]
                new_axis = replace(
                    axis_arr_in.axes[axis],
                    labels=new_labels
                )

        replace_kwargs = {}
        if b_change_dims:
            # Dropping the target axis
            replace_kwargs["dims"] = [_ for dim_ix, _ in enumerate(axis_arr_in.dims) if dim_ix != axis_idx]
            replace_kwargs["axes"] = {k: v for k, v in axis_arr_in.axes.items() if k != axis}
        elif new_axis is not None:
            replace_kwargs["axes"] = {k: (v if k != axis else new_axis) for k, v in axis_arr_in.axes.items()}
        axis_arr_out = replace(
            axis_arr_in,
            data=slice_along_axis(axis_arr_in.data, _slice, axis_idx),
            **replace_kwargs
        )


class SlicerSettings(ez.Settings):
    selection: str = ""
    axis: typing.Optional[str] = None


class Slicer(GenAxisArray):
    SETTINGS: SlicerSettings

    def construct_generator(self):
        self.STATE.gen = slicer(
            selection=self.SETTINGS.selection, axis=self.SETTINGS.axis
        )
