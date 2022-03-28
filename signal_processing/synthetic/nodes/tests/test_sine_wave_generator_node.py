#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg
import numpy as np
from ...generators.sine_wave_generator import (
    SineWaveChannelConfig,
    SineWaveGenerator,
)

from ..signal_capture_node import SignalCaptureConfig, SignalCaptureNode
from ..signal_generator_node import SignalGeneratorNode


SHORT_SLEEP_SECS = 0.01


class MyGraphConfig(lg.Config):
    capture_config: SignalCaptureConfig
    sine_wave_channel_config: SineWaveChannelConfig


class MyGraph(lg.Graph):
    # Note any nodes must be defined here, since connections are checked
    # before on creation of the class, i.e., before setup is called
    capture_node: SignalCaptureNode
    sample_source: SignalGeneratorNode

    def setup(self):
        self.capture_node.configure(self.config.capture_config)
        self.sample_source.set_generator(
            SineWaveGenerator(self.config.sine_wave_channel_config)
        )

    def connections(self) -> lg.Connections:
        return ((self.capture_node.SAMPLE_TOPIC, self.sample_source.SAMPLE_TOPIC),)


def test_sine_wave_generator_node() -> None:
    """
    Tests that node configures itself correctly and returns samples from the generator.
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
    my_graph_config = MyGraphConfig(capture_config, generator_config)

    graph = MyGraph()
    graph.configure(my_graph_config)

    runner = lg.LocalRunner(module=graph)
    runner.run()
    received = np.array(graph.capture_node.samples).T
    np.testing.assert_almost_equal(received, expected)
