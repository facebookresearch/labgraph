# Import labgraph
import labgraph as lg
# Imports required for this example
from scipy.signal import convolve
import numpy as np

import labgraph as lg
import numpy as np
import pytest
from ...generators.sine_wave_generator import (
    SineWaveChannelConfig,
    SineWaveGenerator,
)

from ..mixer_one_input_node import MixerOneInputConfig, MixerOneInputNode
from ..signal_capture_node import SignalCaptureConfig, SignalCaptureNode
from ..signal_generator_node import SignalGeneratorNode


# A data type used in streaming, see docs: Messages
class InputMessage(lg.Message):
    x: np.ndarray
    h: np.ndarray

class OutputMessage(lg.Message):
    data: np.ndarray


# ================================= CONVOLUTION ===================================


def convolve(x, h):
	y = convolve(x, h)
	return y

class ConvolveNode(lg.Node):
	INPUT = lg.Topic(InputMessage)
	OUTPUT = lg.Topic(OutputMessage)

	def setup(self):
		self.func = convolve

	@lg.subscriber(INPUT)
	@lg.publisher(OUTPUT)

	def convolve_feature(self, message: InputMessage):
		y = self.func(message.x, message.h)
		yield self.OUTPUT, y

# ======================================================================


# class MixerOneInputConfig(lg.Config):
#     # This is an NxM matrix (for M inputs, N outputs)
#     weights: np.ndarray

class ConvolveInputConfig(lg.Config):
    array: np.ndarray
    kernel: np.ndarray


class MyGraphConfig(lg.Config):
    sine_wave_channel_config: SineWaveChannelConfig
    convolve_config: ConvolveInputConfig
    capture_config: SignalCaptureConfig


class MyGraph(lg.Graph):

    sample_source: SignalGeneratorNode
    convolve_node: ConvolveNode
    capture_node: SignalCaptureNode

    def setup(self) -> None:
        self.capture_node.configure(self.config.capture_config)
        self.sample_source.set_generator(
            SineWaveGenerator(self.config.sine_wave_channel_config)
        )
        self.convolve_node.configure(self.config.convolve_config)

    def connections(self) -> lg.Connections:
        return (
            (self.convolve_node.INPUT, self.sample_source.SAMPLE_TOPIC),
            (self.capture_node.SAMPLE_TOPIC, self.mixer_node.OUTPUT),
        )


def test_convolve_input_node() -> None:
    """
    Tests that node convolves correctly, uses numpy arrays and kernel sizes as input
    """

    sample_rate = 1  # Hz
    test_duration = 10  # sec

    # Test configurations
    shape = (2,)
    amplitudes = np.array([5.0, 3.0])
    frequencies = np.array([5, 10])
    phase_shifts = np.array([1.0, 5.0])
    midlines = np.array([3.0, -2.5])

    test_array = [1, 2, 3]
    test_kernel = [2]

    # Generate expected values
    
    expected = convolve(test_array, test_kernel) # use the convolve from the library to generate the expected values

    # Create the graph
    generator_config = SineWaveChannelConfig(
        shape, amplitudes, frequencies, phase_shifts, midlines, sample_rate
    )
    capture_config = SignalCaptureConfig(int(test_duration / sample_rate))
    
    # mixer_weights = np.identity(2)
    # mixer_config = MixerOneInputConfig(mixer_weights)
    
    convolve_input_array = [1, 2, 3]
    convolve_input_kernel = [2]

    convolve_config = ConvolveInputConfig(convolve_input_array, convolve_input_kernel)

    my_graph_config = MyGraphConfig(generator_config, convolve_config, capture_config)

    graph = MyGraph()
    graph.configure(my_graph_config)

    runner = lg.LocalRunner(module=graph)
    runner.run()
    received = np.array(graph.capture_node.samples).T
    np.testing.assert_almost_equal(received, expected)

# 1. test the convolve function
# 2. create the graph and run it
# 3. repeat the same thing for other APIs -- just need to create simple test cases