#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" This is a simple node to capture SignalSampleMessage's useful for testing.
    NOTE: This needs to run in the same process as the test for this to work,
    since you need to be able to directly access memory from the capture node
"""

import asyncio
from typing import List

import labgraph as lg
from ...messages.generic_signal_sample import SignalSampleMessage


class SignalCaptureConfig(lg.Config):
    num_capture: int


class SignalCaptureNode(lg.Node):
    """Node that captures a number of messages, and then terminates"""

    SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)

    def setup(self):
        self._shutdown = asyncio.Event()
        self._samples: List[SignalSampleMessage] = []

    @lg.subscriber(SAMPLE_TOPIC)
    def sample_sink(self, message: SignalSampleMessage) -> None:
        if not self._shutdown.is_set():
            self._samples.append(message.sample)
            if len(self._samples) >= self.config.num_capture:
                self._shutdown.set()
                raise lg.NormalTermination()

    @property
    def samples(self):
        return self._samples
