#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
import time
import random
from .random_message import RandomMessage
from datetime import datetime
from time import perf_counter
from collections import deque 

data = deque()
throughput_data = ""
datarate_data = ""
one_second_must_pass = perf_counter()

class AttenuatorConfig(lg.Config):
    attenuation: float

class CustomMessage(RandomMessage):
    latency: float
  
class Attenuator(lg.Node):
    ATTENUATOR_INPUT = lg.Topic(RandomMessage)
    ATTENUATOR_OUTPUT = lg.Topic(RandomMessage)
    config: AttenuatorConfig

    def output(self, _in: float) -> float:
        return pow(10, (self.config.attenuation / 20)) * _in

    @lg.subscriber(ATTENUATOR_INPUT)
    @lg.publisher(ATTENUATOR_OUTPUT)
    async def attenuate(self, message: RandomMessage) -> lg.AsyncPublisher:
        global data 
        global throughput_data
        global datarate_data
        global one_second_must_pass

        start_time = perf_counter()
        current_time_UCT = str(datetime.utcnow()) + " (UTC)"
        output_data = np.array(
            [self.output(_in) for _in in message.data]
        )

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
        yield self.ATTENUATOR_OUTPUT, RandomMessage(
            timestamp=current_time_UCT, data=output_data, latency=latency_data,throughput=throughput_data, datarate=datarate_data
        )
     

 