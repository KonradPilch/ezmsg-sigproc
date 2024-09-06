import copy

import numpy as np
from ezmsg.util.messages.axisarray import AxisArray

from ezmsg.sigproc.slicer import slicer, parse_slice

from util import assert_messages_equal


def test_parse_slice():
    assert parse_slice("") == (slice(None),)
    assert parse_slice(":") == (slice(None),)
    assert parse_slice("NONE") == (slice(None),)
    assert parse_slice("none") == (slice(None),)
    assert parse_slice("0") == (0,)
    assert parse_slice("10") == (10,)
    assert parse_slice(":-1") == (slice(None, -1),)
    assert parse_slice("0:3") == (slice(0, 3),)
    assert parse_slice("::2") == (slice(None, None, 2),)
    assert parse_slice("0,1") == (0, 1)
    assert parse_slice("4:64, 68:100") == (slice(4, 64), slice(68, 100))


def test_slicer_generator():
    n_times = 13
    n_chans = 255
    in_dat = np.arange(n_times * n_chans).reshape(n_times, n_chans)
    msg_in = AxisArray(in_dat, dims=["time", "ch"])
    backup = [copy.deepcopy(msg_in)]

    gen = slicer(selection=":2", axis="ch")
    msg_out = gen.send(msg_in)
    assert_messages_equal([msg_in], backup)
    assert msg_out.data.shape == (n_times, 2)
    assert np.array_equal(msg_out.data, in_dat[:, :2])
    assert np.may_share_memory(msg_out.data, in_dat)

    gen = slicer(selection="::3", axis="ch")
    msg_out = gen.send(msg_in)
    assert_messages_equal([msg_in], backup)
    assert msg_out.data.shape == (n_times, n_chans // 3)
    assert np.array_equal(msg_out.data, in_dat[:, ::3])
    assert np.may_share_memory(msg_out.data, in_dat)

    gen = slicer(selection="4:64", axis="ch")
    msg_out = gen.send(msg_in)
    assert_messages_equal([msg_in], backup)
    assert msg_out.data.shape == (n_times, 60)
    assert np.array_equal(msg_out.data, in_dat[:, 4:64])
    assert np.may_share_memory(msg_out.data, in_dat)

    # Discontiguous slices leads to a copy
    gen = slicer(selection="1, 3:5", axis="ch")
    msg_out = gen.send(msg_in)
    assert_messages_equal([msg_in], backup)
    assert np.array_equal(msg_out.data, msg_in.data[:, [1, 3, 4]])
    assert not np.may_share_memory(msg_out.data, in_dat)


def test_slicer_gen_drop_dim():
    n_times = 50
    n_chans = 10
    in_dat = np.arange(n_times * n_chans).reshape(n_times, n_chans)
    msg_in = AxisArray(
        in_dat,
        dims=["time", "ch"],
        axes={
            "time": AxisArray.Axis.TimeAxis(fs=100.0, offset=0.1),
        }
    )
    backup = [copy.deepcopy(msg_in)]

    gen = slicer(selection="5", axis="ch")
    msg_out = gen.send(msg_in)
    assert_messages_equal([msg_in], backup)
    assert msg_out.data.shape == (n_times,)
    assert np.array_equal(msg_out.data, msg_in.data[:, 5])
