#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" Simple test for a two input mixer """

import labgraph as lg
import numpy as np
import pytest
from ...generators.sine_wave_generator import (
    SineWaveChannelConfig,
    SineWaveGenerator,
)

from ..mixer_two_input_node import MixerTwoInputConfig, MixerTwoInputNode
from ..signal_capture_node import SignalCaptureConfig, SignalCaptureNode
from ..signal_generator_node import SignalGeneratorNode


class MyGraphConfig(lg.Config):
    sine_wave_channel_config: SineWaveChannelConfig
    mixer_config: MixerTwoInputConfig
    capture_config: SignalCaptureConfig


class MyGraph(lg.Graph):

    sample_source: SignalGeneratorNode
    mixer_node: MixerTwoInputNode
    capture_node: SignalCaptureNode

    def setup(self) -> None:
        self.capture_node.configure(self.config.capture_config)
        self.sample_source.set_generator(
            SineWaveGenerator(self.config.sine_wave_channel_config)
        )
        self.mixer_node.configure(self.config.mixer_config)

    def connections(self) -> lg.Connections:
        return (
            # Note connecting both sides of the mixer to the same input for this test
            (self.mixer_node.IN_LEFT_SAMPLE_TOPIC, self.sample_source.SAMPLE_TOPIC),
            (self.mixer_node.IN_RIGHT_SAMPLE_TOPIC, self.sample_source.SAMPLE_TOPIC),
            (self.capture_node.SAMPLE_TOPIC, self.mixer_node.OUT_SAMPLE_TOPIC),
        )


def test_mixertwo_input_node() -> None:
    """
    Tests that node mixes correctly, uses sine wave as input
    """

    sample_rate = 1  # Hz
    test_duration = 10  # sec

    # Test configurations
    shape = (2,)
    amplitudes = np.array([5.0, 3.0])
    frequencies = np.array([5, 10])
    phase_shifts = np.array([1.0, 5.0])
    midlines = np.array([3.0, -2.5])

    # Generate expected values
    t_s = np.arange(0, test_duration, 1 / sample_rate)
    angles = np.expand_dims(frequencies, 1) * np.expand_dims(2 * np.pi * t_s, 0)
    angles = angles + np.expand_dims(phase_shifts, 1)
    expected = np.expand_dims(amplitudes, 1) * np.sin(angles) + np.expand_dims(
        midlines, 1
    )

    # Create the graph
    generator_config = SineWaveChannelConfig(
        shape, amplitudes, frequencies, phase_shifts, midlines, sample_rate
    )
    capture_config = SignalCaptureConfig(int(test_duration / sample_rate))
    mixer_left_weights = 0.5 * np.identity(2)
    mixer_right_weights = 0.5 * np.identity(2)
    mixer_config = MixerTwoInputConfig(mixer_left_weights, mixer_right_weights)
    my_graph_config = MyGraphConfig(generator_config, mixer_config, capture_config)
    graph = MyGraph()
    graph.configure(my_graph_config)

    runner = lg.LocalRunner(module=graph)
    runner.run()
    received = np.array(graph.capture_node.samples).T
    np.testing.assert_almost_equal(received, expected)
