
# Import labgraph
import labgraph as lg
# Imports required for this example
from scipy.signal import convolve
import numpy as np
from node import convolve, convolveNode

# A data type used in streaming, see docs: Messages
class InputMessage(lg.Message):
    x: np.ndarray
    h: np.ndarray

class OutputMessage(lg.Message):
    data: np.ndarray

# ================================= NOISE GENERATOR ====================================
# Configuration for NoiseGenerator, see docs: Lifecycles and Configuration
class NoiseGeneratorConfig(lg.Config):
    x: np.ndarray
    h: np.ndarray


# A data source node that generates random noise to a single output topic
class NoiseGenerator(lg.Node):
    OUTPUT = lg.Topic(InputMessage)
    config: NoiseGeneratorConfig 

    # A publisher method that produces data on a single topic
    @lg.publisher(OUTPUT)
    def generate_noise(self):
        yield self.OUTPUT, InputMessage(x=np.array([1, 2, 3, 4]), h=np.array([1, 2, 3]))
       

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
