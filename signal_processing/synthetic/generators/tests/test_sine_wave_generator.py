#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import numpy as np

from ..sine_wave_generator import SineWaveChannelConfig, SineWaveGenerator


def test_generate_sinusoid() -> None:
    """
    Tests that the samples generated from each channel matches the parameters
    specified in their configuration.
    """

    test_clock_frequency = 100  # hz
    test_duration = 300  # sec

    # test configurations
    shape = (2,)
    amplitudes = np.array([5.0, 3.0])
    frequencies = np.array([5, 10])
    phase_shifts = np.array([1.0, 5.0])
    midlines = np.array([3.0, -2.5])
    sample_rate = test_clock_frequency

    config = SineWaveChannelConfig(
        shape, amplitudes, frequencies, phase_shifts, midlines, sample_rate
    )

    # The generator
    generator = SineWaveGenerator(config)

    # Generate expected values
    t_s = np.arange(0, test_duration, 1 / test_clock_frequency)
    angles = np.expand_dims(frequencies, 1) * np.expand_dims(2 * np.pi * t_s, 0)
    angles = angles + np.expand_dims(phase_shifts, 1)
    expected = np.expand_dims(amplitudes, 1) * np.sin(angles) + np.expand_dims(
        midlines, 1
    )

    values = [generator.next_sample().data for t in t_s]
    values = np.array(values).T
    np.testing.assert_almost_equal(values, expected)


if __name__ == "__main__":
  test_generate_sinusoid()
