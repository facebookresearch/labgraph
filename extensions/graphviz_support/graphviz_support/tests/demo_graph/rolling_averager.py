#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import time
import random
from typing import List
from dataclasses import field
from .random_message import RandomMessage
from datetime import datetime
from time import perf_counter
from collections import deque 

data = deque()
throughput_data = ""
datarate_data = ""
one_second_must_pass = perf_counter()

class RollingState(lg.State):
    messages: List[RandomMessage] = field(default_factory=list)


class RollingConfig(lg.Config):
    window: float

 
class RollingAverager(lg.Node):
    ROLLING_AVERAGER_INPUT = lg.Topic(RandomMessage)
    ROLLING_AVERAGER_OUTPUT = lg.Topic(RandomMessage)

    state: RollingState
    config: RollingConfig

    

    @lg.subscriber(ROLLING_AVERAGER_INPUT)
    @lg.publisher(ROLLING_AVERAGER_OUTPUT)
    async def average(self, message: RandomMessage) -> lg.AsyncPublisher:
        global data 
        global throughput_data
        global datarate_data
        global one_second_must_pass

        start_time = perf_counter()
        current_time_UTC = str(datetime.utcnow()) + " (UTC)"
        
        self.state.messages.append(message)
        self.state.messages = [
            message
            for message in self.state.messages
            if message.timestamp >= time.time() - self.config.window
        ]
        if len(self.state.messages) == 0:
            return
        all_data = np.stack(
            [message.data for message in self.state.messages]
        )
        mean_data = np.mean(all_data, axis=0)

        data.append(message.data.size * message.data.itemsize)
        if perf_counter() - one_second_must_pass >= 1:
            tempThroughput = 0
            tempDataRate = 0
            for messagedata in data:
                tempThroughput += messagedata
                tempDataRate += 1.0
            throughput_data = str(tempThroughput) + " bytes"
            datarate_data = str(tempDataRate) + " msg/sec"
            data.clear()
            one_second_must_pass = perf_counter()

        latency_data = str(perf_counter() - start_time) + " s"
         
        yield self.ROLLING_AVERAGER_OUTPUT, RandomMessage(
            timestamp=current_time_UTC,
            data=mean_data,

            latency=latency_data,
            throughput=throughput_data,
            datarate=datarate_data
        )
