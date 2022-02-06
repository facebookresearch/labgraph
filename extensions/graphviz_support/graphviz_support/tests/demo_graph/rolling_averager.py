#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import time
from typing import List
from dataclasses import field
from .random_message import RandomMessage


class RollingState(lg.State):
    messages: List[RandomMessage] = field(default_factory=list)


class RollingConfig(lg.Config):
    window: float


class RollingAverager(lg.Node):
    INPUT = lg.Topic(RandomMessage)
    OUTPUT = lg.Topic(RandomMessage)

    state: RollingState
    config: RollingConfig

    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def average(self, message: RandomMessage) -> lg.AsyncPublisher:
        current_time = time.time()
        self.state.messages.append(message)
        self.state.messages = [
            message
            for message in self.state.messages
            if message.timestamp >= current_time - self.config.window
        ]
        if len(self.state.messages) == 0:
            return
        all_data = np.stack(
            [message.data for message in self.state.messages]
        )
        mean_data = np.mean(all_data, axis=0)
        yield self.OUTPUT, RandomMessage(
            timestamp=current_time,
            data=mean_data
        )
