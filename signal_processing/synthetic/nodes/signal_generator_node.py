#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" Node for a generic signal generator, eg SineWaveGenerator """

import asyncio

import labgraph as lg
from ...messages.generic_signal_sample import SignalSampleMessage
from labgraph.simulations import FunctionGeneratorNode


# This assume we would not be delivering samples at close to 1KHz
PUBLISHER_SLEEP_SECS = 0.001


class SignalGeneratorNode(FunctionGeneratorNode):

    SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)

    def setup(self):
        self._shutdown = asyncio.Event()

    def cleanup(self):
        self._shutdown.set()

    @lg.publisher(SAMPLE_TOPIC)
    async def publish_samples(self) -> lg.AsyncPublisher:
        while not self._shutdown.is_set():
            sample_message = self._generator.next_sample()
            yield self.SAMPLE_TOPIC, SignalSampleMessage(
                timestamp=sample_message.timestamp, sample=sample_message.data
            )
            await asyncio.sleep(PUBLISHER_SLEEP_SECS)
