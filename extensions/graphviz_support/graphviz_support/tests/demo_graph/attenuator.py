#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import time
from .random_message import RandomMessage


class AttenuatorConfig(lg.Config):
    attenuation: float


class Attenuator(lg.Node):
    ATTENUATOR_INPUT = lg.Topic(RandomMessage)
    ATTENUATOR_OUTPUT = lg.Topic(RandomMessage)
    config: AttenuatorConfig

    def output(self, _in: float) -> float:
        return pow(10, (self.config.attenuation / 20)) * _in

    @lg.subscriber(ATTENUATOR_INPUT)
    @lg.publisher(ATTENUATOR_OUTPUT)
    async def attenuate(self, message: RandomMessage) -> lg.AsyncPublisher:
        current_time = time.time()
        output_data = np.array(
            [self.output(_in) for _in in message.data]
        )
        yield self.ATTENUATOR_OUTPUT, RandomMessage(
            timestamp=current_time, data=output_data
        )
