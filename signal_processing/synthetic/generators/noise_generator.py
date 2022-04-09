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
class NoiseChannelConfig(FunctionChannelConfig):
    """
    Configuration variables describing the samples produced by this generator.
    Noise is generated
    Args:
        - amplitudes: The amplitude of the noise
        - offsets: the offset of the noise
        - sample_rate: the sample rate.
    """

    amplitudes: np.ndarray
    offsets: np.ndarray
    sample_rate: float

    def __post_init__(self) -> None:
        assert self.shape == self.amplitudes.shape == self.offsets.shape


class NoiseGenerator(FunctionGenerator):
    """
    Generator which produces a uniformly distributed random noise on each channel.
    Ammplitude and offset of the noise is controlled by the configuration.
    """

    def __init__(self, config: NoiseChannelConfig) -> None:
        """Passing the config in __init__ seems easier than separately calling
        set_config on the object afterwards. Also means I can avoid the
        check for a valid config in the next_sample function
        """
        super().__init__()
        self.set_channel_config(config)
        self._time = 0.0

    def next_sample(self) -> np.ndarray:
        sample = (
            self.channel_config.amplitudes * np.random.random(self.channel_config.shape)
            + self.channel_config.offsets
        )
        sample_message = FunctionGeneratorMessage(self._time, sample)
        # Update time
        self._time += 1 / self.channel_config.sample_rate
        return sample_message
