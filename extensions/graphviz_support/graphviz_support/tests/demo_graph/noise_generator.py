#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import asyncio
import time
from .random_message import RandomMessage


class NoiseGeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int


class NoiseGenerator(lg.Node):
    NOISE_GENERATOR_OUTPUT = lg.Topic(RandomMessage)
    config: NoiseGeneratorConfig

    @lg.publisher(NOISE_GENERATOR_OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.NOISE_GENERATOR_OUTPUT, RandomMessage(
                timestamp=time.time(),
                data=np.random.rand(self.config.num_features)
            )
            await asyncio.sleep(1 / self.config.sample_rate)
