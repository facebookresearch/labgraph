#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from .._cthulhu.clock import ExperimentClock
from ..graphs.node import Node
from .function_generator import FunctionGenerator


class FunctionGeneratorNode(Node):
    """
    A node which generates samples to the graph based on
    user-specified functions.
    """

    def __init__(self) -> None:
        super().__init__()
        self._clock = ExperimentClock()

    def set_generator(self, generator: FunctionGenerator) -> None:
        self._generator = generator
