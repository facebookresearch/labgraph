#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest

import numpy as np

from ..detrend import detrend_and_offset


class DetrendTest(unittest.TestCase):
    def test_detrend_and_offset_positive_trend(self):
        # signal is sine wave of different frequency
        t = np.arange(0, 1, 0.01)
        signal = np.vstack([np.cos(2 * np.pi * 5 * t), np.cos(2 * np.pi * 10 * t)]).T

        # Add DC offset
        signal_with_offset = signal + 1

        # Add linear trend, positive trend
        linear_trend = t.reshape((-1, 1))

        # composite signal
        composite_signal = signal_with_offset + linear_trend

        # No need to fix negative because positive trend
        signal_detrend_and_offset = detrend_and_offset(
            composite_signal, fix_negative=False
        )

        # close to only 1 decimal place because
        # detrend accumulates error due to least-square fit
        np.testing.assert_array_almost_equal(
            signal_detrend_and_offset,
            signal + np.mean(composite_signal, axis=0),
            decimal=1,
        )

    def test_detrend_and_offset_negative_trend(self):
        # signal is sine wave of different frequency
        t = np.arange(0, 1, 0.01)
        signal = np.vstack([np.cos(2 * np.pi * 5 * t), np.cos(2 * np.pi * 10 * t)]).T

        # Add DC offset
        signal_with_offset = signal + 1

        # Add linear trend, positive trend
        linear_trend = -t.reshape((-1, 1))

        # composite signal
        composite_signal = signal_with_offset + linear_trend

        # No need to fix negative because positive trend
        signal_detrend_and_offset = detrend_and_offset(
            composite_signal, fix_negative=False
        )

        np.testing.assert_array_almost_equal(
            signal_detrend_and_offset,
            signal + np.mean(composite_signal, axis=0),
            decimal=1,
        )

        # now fix negative values and make sure that's correct
        signal_detrend_and_offset_fix_negative = detrend_and_offset(
            composite_signal, fix_negative=True
        )
        self.assertTrue(np.all(signal_detrend_and_offset_fix_negative >= 0))
