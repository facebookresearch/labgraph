#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging

import labgraph as lg
import numpy as np
import pytest
from ..logmean_node import (
    LogmeanNode,
    LogMeanNodeConfig,
)
from ....messages.generic_signal_sample import SignalSampleMessage


def build_test_signal(
    n_time: int = 1000,
    n_channels: int = 6,
    power_scaler: float = 1e-10,
) -> np.ndarray:
    if n_channels < 5:
        logging.info("build_test_signal requires at least 5 channels, setting to 5")
        n_channels = 5

    signals = np.random.rand(n_time, n_channels) * power_scaler
    # Set first channel to all 0
    signals[:, 0] = 0
    # Set second channel to all negative
    signals[:, 1] = -signals[:, 1]
    # Set third channel first sample to 0
    signals[0, 2] = 0
    # Set fourth channel first sample to negative
    signals[0, 3] = -signals[0, 3]
    # Set 10% of samples in signals[1:, 2:] to 0 or negative (5% and 5%)
    indices = list(np.ndindex(signals[1:, 2:].shape))  # each index is offset by (1, 2)
    np.random.shuffle(indices)  # shuffle inplace
    for (row, col) in indices[0 : len(indices) // 20]:
        signals[row + 1, col + 2] = 0
    for (row, col) in indices[len(indices) // 20 : len(indices) // 10]:
        signals[row + 1, col + 2] = -signals[row + 1, col + 2]
    return signals


def get_correct_logmean_signal(signals: np.ndarray) -> np.ndarray:
    output = np.copy(signals)

    for ch in range(signals.shape[1]):
        sub_value = np.nan
        for i in range(signals.shape[0]):
            if signals[i, ch] > 0:
                output[i, ch] = -np.log10(signals[i, ch])
                sub_value = signals[i, ch]

            elif signals[i, ch] <= 0:
                output[i, ch] = 0 if np.isnan(sub_value) else -np.log10(sub_value)

    return output


def test_logmean_node_pass_through() -> None:
    test_signals = build_test_signal()
    timestamps = np.arange(len(test_signals)) * 0.1

    test_harness = lg.NodeTestHarness(LogmeanNode)
    messages = [
        SignalSampleMessage(timestamp=timestamps[i], sample=test_signals[i, :])
        for i in range(len(test_signals))
    ]
    with test_harness.get_node(config=LogMeanNodeConfig(pass_through=True)) as node:
        for i in range(0, len(messages)):
            result = lg.run_async(node.get_logmean, args=(messages[i],))
            assert result is not None
            np.testing.assert_array_equal(result[0][1].sample, test_signals[i, :])


def test_logmean_node() -> None:
    test_signals = build_test_signal()
    correct_signals = get_correct_logmean_signal(test_signals)
    timestamps = np.arange(len(test_signals)) * 0.1

    test_harness = lg.NodeTestHarness(LogmeanNode)
    messages = [
        SignalSampleMessage(timestamp=timestamps[i], sample=test_signals[i, :])
        for i in range(len(test_signals))
    ]
    with test_harness.get_node(config=LogMeanNodeConfig(pass_through=False)) as node:
        for i in range(0, len(messages)):
            result = lg.run_async(node.get_logmean, args=(messages[i],))
            assert result is not None
            # almost because log imprecision
            np.testing.assert_array_almost_equal(
                result[0][1].sample, correct_signals[i, :]
            )
