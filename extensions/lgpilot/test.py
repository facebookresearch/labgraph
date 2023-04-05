
# Import labgraph
import labgraph as lg
# Imports required for this example
from scipy.signal import convolve
import numpy as np

# A data type used in streaming, see docs: Messages
class InputMessage(lg.Message):
    x: np.ndarray
    h: np.ndarray

class OutputMessage(lg.Message):
    data: np.ndarray

# ================================= NOISE GENERATOR ====================================
# Configuration for NoiseGenerator, see docs: Lifecycles and Configuration
class NoiseGeneratorConfig(lg.Config):
    #TODO: Is this needed?
    sample_rate: float  # Rate at which to generate noise
    num_features: int  # Number of features to generate


# A data source node that generates random noise to a single output topic
class NoiseGenerator(lg.Node):
    OUTPUT = lg.Topic(InputMessage)
    config: NoiseGeneratorConfig #TODO: Is this needed?

    # A publisher method that produces data on a single topic
    @lg.publisher(OUTPUT)
    def generate_noise(self):
        yield self.OUTPUT, InputMessage(x=np.array([1, 2, 3, 4]), h=np.array([1, 2, 3]))
       

# ================================= CONVOLUTION ===================================


def convolve(x, h):
	y = convolve(x, h)
	return y

class convolveNode(lg.Node):
	INPUT = lg.Topic(InputMessage)
	OUTPUT = lg.Topic(OutputMessage)

	def setup(self):
		self.func = convolve

	@lg.subscriber(INPUT)
	@lg.publisher(OUTPUT)

	def convolve_feature(self, message: InputMessage):
		y = self.func(message.x, message.h)
		yield self.OUTPUT, y

# ================================== CONVOLVED NOISE ====================================


# Configuration for ConvolvedNoise
class ConvolvedNoiseConfig(lg.Config):
    x: np.ndarray
    h: np.ndarray

# A group that combines noise generation and rolling averaging. The output topic
# contains averaged noise. We could just put all three nodes in a graph below, but we
# add this group to demonstrate the grouping functionality.
class AveragedNoise(lg.Group):
    OUTPUT = lg.Topic(OutputMessage)

    #TODO: Is this needed?
    config: AveragedNoiseConfig
    GENERATOR: NoiseGenerator
    CONVOLVENODE: convolveNode

    def connections(self) -> lg.Connections:
        # To produce convolved noise, we connect the noise generator to the convolver
        # Then we "expose" the averager's output as an output of this group
        return (
            (self.GENERATOR.OUTPUT, self.CONVOLVENODE.INPUT),
            (self.CONVOLVENODE.OUTPUT, self.OUTPUT),
        )

    #TODO: What should happen here? 
    def setup(self) -> None:
        # Cascade this group's configuration to its contained nodes
        self.GENERATOR.configure(
            NoiseGeneratorConfig(
                sample_rate=self.config.sample_rate,
                num_features=self.config.num_features,
            )
        )
        self.ROLLING_AVERAGER.configure(RollingConfig(window=self.config.window))
