#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" Simple 1 input mixer node. This takes the input of M channels, and produces
    an output of N channels, using simple matrix mulitplication.
"""

import labgraph as lg
import numpy as np
from ...messages.generic_signal_sample import SignalSampleMessage


class MixerOneInputConfig(lg.Config):
    # This is an NxM matrix (for M inputs, N outputs)
    weights: np.ndarray


class MixerOneInputNode(lg.Node):

    IN_SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)
    OUT_SAMPLE_TOPIC = lg.Topic(SignalSampleMessage)

    @lg.subscriber(IN_SAMPLE_TOPIC)
    @lg.publisher(OUT_SAMPLE_TOPIC)
    async def mix_samples(self, in_sample: SignalSampleMessage) -> lg.AsyncPublisher:
        if in_sample.sample.shape[0] != self.config.weights.shape[1]:
            raise lg.util.LabgraphError("Mismatching input dimensions")
        out_sample = SignalSampleMessage(
            timestamp=in_sample.timestamp,
            sample=np.dot(self.config.weights, in_sample.sample),
        )
        yield self.OUT_SAMPLE_TOPIC, out_sample
