#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple

from numpy import ndarray

from ..messages.message import TimestampedMessage


@dataclass
class FunctionChannelConfig:
    shape: Tuple[int]


class FunctionGeneratorMessage(TimestampedMessage):
    data: ndarray


class FunctionGenerator(ABC):
    """
    Abstract base class for a function generator.  Derived generators
    should implement logic for generating some function.
    """

    def set_channel_config(self, channel_config: FunctionChannelConfig) -> None:
        """
        Sets the configuration object specifying how data should be generated
        across channels for this generator.

        Args:
            channel_config: The channel configuration object.
        """

        self.channel_config = channel_config

    @abstractmethod
    def next_sample(self) -> FunctionGeneratorMessage:
        """
        Returns the next sample that should be produced in the
        experiment based on the current state information.
        """

        raise NotImplementedError()

    def next_n_samples(self, n: int = 1) -> List[ndarray]:
        """
        Returns the next n samples that should be produced in the
        experiment based on the current state information.

        Args:
            n: The number of samples that should be produced. 1 by default.
        """

        samples = [self.next_sample() for _ in range(n)]

        return samples
