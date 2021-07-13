#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import time
from typing import Tuple, Optional

import labgraph as lg
import numpy as np
from scipy import signal
from scipy.stats import gamma
import matplotlib.animation as animation
import matplotlib.axes
import matplotlib.pyplot as plt

# Constants used by nodes
SAMPLE_RATE = 10.0
NUM_FEATURES = 220
WINDOW = 2.0
REFRESH_RATE = 2.0


# Simulation configurations
SAMPLE_SIZE_CYCLE = 30
SAMPLES_REST = 9
ORDER_OF_ZERO_DAUB = 10
PEAK_GAMMA_SHAPE = 6
UNDERSHOOT_GAMMA_SHAPE = 12
TIME_TO_ZERO_HFR = 0.35


class SimulationFunction:
    """
    Simulation functions to generate a cycle (one cycle of the function).
    """

    # Last element is removed to ensure no overlaps between cycles.
    phase_data = np.linspace(-np.pi, np.pi, SAMPLE_SIZE_CYCLE)[:-1]

    # Generate a sine cycle
    def sin_cycle(self):
        return np.sin(self.phase_data)

    # Generate a square cycle
    def square_cycle(self):
        return np.sign(np.sin(self.phase_data))

    # Generate a heartbeat-like cycle using daubechies cycle
    def daub_cycle(self):
        hb = signal.wavelets.daub(ORDER_OF_ZERO_DAUB)
        zero_array = np.zeros(SAMPLES_REST, dtype=float)
        hb_full = np.concatenate([hb, zero_array])
        return hb_full

    # Generate a hemodynamic responses (HRFs) cycle
    def hrf_cycle(self):
        times = np.arange(1, SAMPLE_SIZE_CYCLE)
        peak_values = gamma.pdf(times, PEAK_GAMMA_SHAPE)
        undershoot_values = gamma.pdf(times, UNDERSHOOT_GAMMA_SHAPE)
        values = peak_values - TIME_TO_ZERO_HFR * undershoot_values
        return values / np.max(values)


class SimulationMessage(lg.Message):
    timestamp: np.ndarray
    daub_data: np.ndarray


class GeneratorConfig(lg.Config):
    sample_rate: float  # Rate at which to generate noise
    num_features: int  # Number of features to generate
    window: float  # Window, in seconds, to average over


class SimulationGenerator(lg.Node):
    """
    Generate messages to visualize
    Repeatedly generate cycles using simulation functions.

    Note: Cycle periods of different functions are chosen
    the same in this example.
    """

    OUTPUT = lg.Topic(SimulationMessage)
    config: GeneratorConfig

    @lg.publisher(OUTPUT)
    async def generate_simulation(self) -> lg.AsyncPublisher:
        SF = SimulationFunction()
        daub_base_data = SF.daub_cycle()
        counter = 0
        data_length = len(daub_base_data)

        while True:
            for i in range(data_length):
                daub_base_data_itr = np.concatenate([daub_base_data[i:], daub_base_data[:i]])
                yield self.OUTPUT, SimulationMessage(
                        timestamp=np.array(np.arange(counter*data_length, (counter+1)*data_length), dtype=np.float),
                        daub_data=daub_base_data_itr,
                    )
                await asyncio.sleep(1 / self.config.sample_rate)
                counter += 1


# ======================================= PLOT =========================================


# The state of the Plot: holds the most recent data received, which should be displayed
class PlotState(lg.State):
    data: Optional[np.ndarray] = None
    timestamp: Optional[np.ndarray] = None


# The configuration for the Plot
class PlotConfig(lg.Config):
    refresh_rate: float  # How frequently to refresh the bar graph
    num_bars: int  # The number of bars to display (note this should be == num_features)


# A node that creates a matplotlib bar graph that displays the produced data in
# real-time
class Plot(lg.Node):
    INPUT = lg.Topic(SimulationMessage)
    state: PlotState
    config: PlotConfig

    def setup(self) -> None:
        self.ax: Optional[matplotlib.axes.Axes] = None

    # A subscriber method that simply receives data and updates the node's state
    @lg.subscriber(INPUT)
    def got_message(self, message: SimulationMessage) -> None:
        # This demo wil use heart-beat like signal as an example
        # Other data examples are also available by changing message.daub_data
        self.state.data = message.daub_data
        self.state.timestamp = message.timestamp

    # A main method does not interact with topics, but has its own line of execution -
    # this can be useful for Python libraries that must be run in the main thread. For
    # example, scikit-learn and pyqtgraph are libraries that need the main thread.
    @lg.main
    def run_plot(self) -> None:
        fig = plt.figure()
        self.ax = fig.add_subplot(1, 1, 1)
        #self.ax.set_ylim((0, 1))
        anim = animation.FuncAnimation(  # noqa: F841
            fig, self._animate, interval=1 / self.config.refresh_rate * 1000
        )
        plt.show()
        raise lg.NormalTermination()

    def _animate(self, i: int) -> None:
        if self.ax is None:
            return
        self.ax.clear()
        #self.ax.set_ylim([0, 1])
        #self.ax.bar(range(self.config.num_bars), self.state.data)
        self.ax.plot(self.state.timestamp, self.state.data)


# ======================================= DEMO =========================================


# A graph for the demo in this example. Hooks together the AveragedNoise group
# (containing NoiseGenerator and RollingAverager) and the Plot node.
class Demo(lg.Graph):
    SIMULATIONGENERATOR: SimulationGenerator
    PLOT: Plot

    def setup(self) -> None:
        # Provide configuration using global constants (but if we wanted to, we could
        # have a configuration object provided to this graph as well).
        self.SIMULATIONGENERATOR.configure(
            GeneratorConfig(
                sample_rate=SAMPLE_RATE, num_features=NUM_FEATURES, window=WINDOW
            )
        )
        self.PLOT.configure(
            PlotConfig(refresh_rate=REFRESH_RATE, num_bars=NUM_FEATURES)
        )

    # Connect the AveragedNoise output to the Plot input
    def connections(self) -> lg.Connections:
        return ((self.SIMULATIONGENERATOR.OUTPUT, self.PLOT.INPUT),)

    # Parallelization: Run AveragedNoise and Plot in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.SIMULATIONGENERATOR, self.PLOT)


# Entry point: run the Demo graph
if __name__ == "__main__":
    lg.run(Demo)
