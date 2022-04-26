#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import time
from .random_message import RandomMessage


class AmplifierConfig(lg.Config):
    out_in_ratio: float


class Amplifier(lg.Node):
    AMPLIFIER_INPUT = lg.Topic(RandomMessage)
    AMPLIFIER_OUTPUT = lg.Topic(RandomMessage)
    config: AmplifierConfig

    def output(self, _in: float) -> float:
        return self.config.out_in_ratio * _in

    @lg.subscriber(AMPLIFIER_INPUT)
    @lg.publisher(AMPLIFIER_OUTPUT)
    async def amplify(self, message: RandomMessage) -> lg.AsyncPublisher:
        current_time = time.time()
        output_data = np.array(
            [self.output(_in) for _in in message.data]
        )
        yield self.AMPLIFIER_OUTPUT, RandomMessage(
            timestamp=current_time, data=output_data
        )
