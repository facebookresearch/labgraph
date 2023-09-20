#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import asyncio
import time
import random
from .random_message import RandomMessage
from datetime import datetime
from time import perf_counter

class NoiseGeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int

    
class NoiseGenerator(lg.Node):
    NOISE_GENERATOR_OUTPUT = lg.Topic(RandomMessage)
    config: NoiseGeneratorConfig

    @lg.publisher(NOISE_GENERATOR_OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            start_time = perf_counter()
            timestamp_data = time.time()

            datarate_data = random.random() + 6
            throughput_data = len(str(np.random.rand(self.config.num_features)))
            latency_data = perf_counter() - start_time
           
            yield self.NOISE_GENERATOR_OUTPUT, RandomMessage(
                timestamp=timestamp_data,
                data=np.random.rand(self.config.num_features),

                latency=10.0,
                throughput=throughput_data,
                datarate=datarate_data
            )
            await asyncio.sleep(1 / self.config.sample_rate)

 