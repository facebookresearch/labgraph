#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np
from typing import Optional
from .random_message import RandomMessage


class SinkState(lg.State):
    data_1: Optional[np.ndarray] = None
    data_2: Optional[np.ndarray] = None
    data_3: Optional[np.ndarray] = None


class Sink(lg.Node):
    INPUT_1 = lg.Topic(RandomMessage)
    INPUT_2 = lg.Topic(RandomMessage)
    INPUT_3 = lg.Topic(RandomMessage)
    state: SinkState

    @lg.subscriber(INPUT_1)
    def got_message(self, message: RandomMessage) -> None:
        self.state.data_1 = message.data

    @lg.subscriber(INPUT_2)
    def got_message_2(self, message: RandomMessage) -> None:
        self.state.data_2 = message.data

    @lg.subscriber(INPUT_3)
    def got_message_3(self, message: RandomMessage) -> None:
        self.state.data_3 = message.data

    @lg.main
    def do_something(self) -> None:
        raise lg.NormalTermination()
