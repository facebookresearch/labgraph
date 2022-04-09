#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import numpy as np

from ..noise_generator import NoiseChannelConfig, NoiseGenerator


def test_generate_noise() -> None:
    """
    Tests that the samples generated from each channel matches the parameters
    specified in their configuration. Since this is noise, only check the bounds
    """

    num_samples = 10

    # Test configurations
    shape = (2,)
    amplitudes = np.array([2.0, 5.0])
    offsets = np.array([1.0, -2.5])
    sample_rate = 1

    config = NoiseChannelConfig(shape, amplitudes, offsets, sample_rate)

    # The generator
    generator = NoiseGenerator(config)

    max_values = np.array([amplitudes * np.ones(shape) + offsets] * num_samples)
    min_values = np.array([offsets] * num_samples)
    # Generate expected values
    values = np.array([generator.next_sample().data for i in range(num_samples)])
    assert values[0].shape == shape
    np.testing.assert_array_less(values, max_values)
    # Note: small delta subtraction is because the generator produces samples on
    # the half open intervals [offsets, amplitudes+offsets)
    np.testing.assert_array_less(min_values - 0.00001, values)
