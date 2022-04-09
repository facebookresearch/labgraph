#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" Simple 2 input mixer node. This takes two inputs of potentially different sizes,
    weights them and then sums them to form an output.
"""
import asyncio
import queue

import labgraph as lg
import numpy as np
from ...messages.generic_signal_sample import SignalSampleMessage


SHORT_SLEEP_SECS = 0.001


class MixerTwoInputConfig(lg.Config):
    # These are NxL and NxR matrices (for L,R inputs, same dimension N outputs)
    left_weights: np.ndarray
    right_weights: np.ndarray


class MixerTwoInputNode(lg.Node):

    IN_LEFT_SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)
    IN_RIGHT_SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)
    OUT_SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)

    def setup(self) -> None:
        # Check the weights are correctly dimensioned to be summed on output
        if self.config.left_weights.shape[0] != self.config.right_weights.shape[0]:
            raise ValueError("Mismatch in left-right output dimensions")
        self._left_in = queue.Queue()
        self._right_in = queue.Queue()
        self._shutdown = asyncio.Event()

    def cleanup(self) -> None:
        self._shutdown.set()

    @lg.subscriber(IN_LEFT_SAMPLE_TOPIC)
    def left_input(self, in_sample: SignalSampleMessage) -> None:
        # Check in the input dimensions against left weights
        if in_sample.sample.shape[0] != self.config.left_weights.shape[1]:
            raise ValueError("Mismatch in left input dimension")
        self._left_in.put(in_sample)

    @lg.subscriber(IN_RIGHT_SAMPLE_TOPIC)
    def right_input(self, in_sample: SignalSampleMessage) -> None:
        # Check in the input dimensions against right weights
        if in_sample.sample.shape[0] != self.config.right_weights.shape[1]:
            raise ValueError("Mismatch in right input dimension")
        self._right_in.put(in_sample)

    @lg.publisher(OUT_SAMPLE_TOPIC)
    async def mix_samples(self) -> lg.AsyncPublisher:
        while not self._shutdown.is_set():
            while self._left_in.empty() or self._right_in.empty():
                await asyncio.sleep(SHORT_SLEEP_SECS)
            left = self._left_in.get()
            right = self._right_in.get()
            mixed_output = np.dot(self.config.left_weights, left.sample) + np.dot(
                self.config.right_weights, right.sample
            )
            # I am just using the left timetamp for this, since I don't
            # know what else makes sense!
            out_sample = SignalSampleMessage(
                timestamp=left.timestamp, sample=mixed_output
            )
            yield self.OUT_SAMPLE_TOPIC, out_sample
