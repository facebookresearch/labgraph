#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from dataclasses import dataclass

import numpy as np
from labgraph.simulations import (
    FunctionChannelConfig,
    FunctionGenerator,
    FunctionGeneratorMessage,
)


@dataclass
class SineWaveChannelConfig(FunctionChannelConfig):
    """
    Configuration variables describing the samples produced by this generator.

    Args:
        - amplitudes: The amplitude of the sinusoid.
        - frequencies: The frequency of the sinusoid.
        - phase_shifts: The phase shift for this sinusoid, in rads.
        - midlines: The midline of the sinusoid.
        - sample_rate: the sample rate.
    """

    amplitudes: np.ndarray
    frequencies: np.ndarray
    phase_shifts: np.ndarray
    midlines: np.ndarray
    sample_rate: float

    def __post_init__(self) -> None:
        assert (
            self.amplitudes.shape
            == self.frequencies.shape
            == self.phase_shifts.shape
            == self.midlines.shape
        )
        assert self.sample_rate > 0.0


class SineWaveGenerator(FunctionGenerator):
    """
    Generator which produces a continuous sinusoid on each channel at the amplitude,
    frequency, phase shift, and midline specified by each channel's
    SineWaveChannelConfig object in this generator's config.
    """

    def __init__(self, config: SineWaveChannelConfig) -> None:
        """Passing the config in __init__ seems easier than separately calling
        set_config on the object afterwards. Also means I can avoid the
        check for a valid config in the next_sample function
        """
        super().__init__()
        self.set_channel_config(config)
        # This is time, which starts at zero
        self._time = np.zeros(self.channel_config.shape)

    def next_sample(self) -> FunctionGeneratorMessage:
        # Calculate output of the set of sine waves
        angles = self.channel_config.frequencies * 2 * np.pi * self._time
        angles = angles + self.channel_config.phase_shifts
        sample = (
            self.channel_config.amplitudes * np.sin(angles)
            + self.channel_config.midlines
        )
        sample_message = FunctionGeneratorMessage(self._time.flatten()[0], sample)
        # Update time
        self._time += 1 / self.channel_config.sample_rate
        return sample_message
