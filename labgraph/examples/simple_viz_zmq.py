#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# Built-in imports
import asyncio
from labgraph.zmq_node.zmq_message import ZMQMessage
from labgraph.zmq_node.zmq_poller_node import ZMQPollerConfig
import time
from dataclasses import field
from typing import Any, List, Optional, Tuple

# Import labgraph
import labgraph as lg

from labgraph.zmq_node import ZMQPollerNode

# Imports required for this example
import matplotlib.animation as animation
import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np


# Constants used by nodes
NUM_FEATURES = 100
WINDOW = 2.0
REFRESH_RATE = 2.0
ENDPOINT = "tcp://localhost:5555"  # For ZMQ
TOPIC = "randomstream"  # For ZMQ


# A data type used in streaming, see docs: Messages
class RandomMessage(lg.Message):
    timestamp: float
    data: np.ndarray

# ================================= ZMQ deserializer ==================================

# A shim to feed ZMQ data to the rolling averager
class ZMQDeserializer(lg.Node):
    INPUT = lg.Topic(ZMQMessage)
    OUTPUT = lg.Topic(RandomMessage)

    # Take the raw data and reify it to a RandomMessage
    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def deserialize(self, message: ZMQMessage) -> lg.AsyncPublisher:
        yield self.OUTPUT, RandomMessage(timestamp=time.time(), data=np.frombuffer(message.data))


# ================================= ROLLING AVERAGER ===================================

# The state of the RollingAverager node: holds windowed messages
class RollingState(lg.State):
    messages: List[RandomMessage] = field(default_factory=list)


# Configuration for RollingAverager
class RollingConfig(lg.Config):
    window: float  # Window, in seconds, to average over


# A transformer node that accepts some data on an input topic and averages that data
# over the configured window to its output topic
class RollingAverager(lg.Node):
    INPUT = lg.Topic(RandomMessage)
    OUTPUT = lg.Topic(RandomMessage)

    state: RollingState
    config: RollingConfig

    # A transformer method that transforms data from one topic into another
    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def average(self, message: RandomMessage) -> lg.AsyncPublisher:
        current_time = time.time()
        self.state.messages.append(message)
        self.state.messages = [
            message
            for message in self.state.messages
            if message.timestamp >= current_time - self.config.window
        ]
        if len(self.state.messages) == 0:
            return
        all_data = np.stack([message.data for message in self.state.messages])
        mean_data = np.mean(all_data, axis=0)
        yield self.OUTPUT, RandomMessage(timestamp=current_time, data=mean_data)


# ================================== AVERAGED NOISE ====================================


# Configuration for AveragedNoise
class AveragedNoiseConfig(lg.Config):
    num_features: int  # Number of features to generate
    window: float  # Window, in seconds, to average over
    read_addr: str
    zmq_topic: str
    poll_time: float


# A group that combines noise generation and rolling averaging. The output topic
# contains averaged noise. We could just put all three nodes in a graph below, but we
# add this group to demonstrate the grouping functionality.
class AveragedNoise(lg.Group):
    OUTPUT = lg.Topic(RandomMessage)

    config: AveragedNoiseConfig
    ZMQ: ZMQPollerNode
    ZMQ_DESERIALIZER: ZMQDeserializer
    ROLLING_AVERAGER: RollingAverager

    def connections(self) -> lg.Connections:
        # To produce averaged noise, we connect the noise generator to the averager
        # Then we "expose" the averager's output as an output of this group
        return (
            (self.ZMQ.topic, self.ZMQ_DESERIALIZER.INPUT),
            (self.ZMQ_DESERIALIZER.OUTPUT, self.ROLLING_AVERAGER.INPUT),
            (self.ROLLING_AVERAGER.OUTPUT, self.OUTPUT),
        )

    def setup(self) -> None:
        # Cascade this group's configuration to its contained nodes
        self.ZMQ.configure(
            ZMQPollerConfig(
                read_addr=self.config.read_addr,
                zmq_topic=self.config.zmq_topic,
                poll_time=self.config.poll_time
            )
        )
        self.ROLLING_AVERAGER.configure(RollingConfig(window=self.config.window))


# ======================================= PLOT =========================================


# The state of the Plot: holds the most recent data received, which should be displayed
class PlotState(lg.State):
    data: Optional[np.ndarray] = None


# The configuration for the Plot
class PlotConfig(lg.Config):
    refresh_rate: float  # How frequently to refresh the bar graph
    num_bars: int  # The number of bars to display (note this should be == num_features)


# A node that creates a matplotlib bar graph that displays the produced data in
# real-time
class Plot(lg.Node):
    INPUT = lg.Topic(RandomMessage)
    state: PlotState
    config: PlotConfig

    def setup(self) -> None:
        self.ax: Optional[matplotlib.axes.Axes] = None

    # A subscriber method that simply receives data and updates the node's state
    @lg.subscriber(INPUT)
    def got_message(self, message: RandomMessage) -> None:
        self.state.data = message.data

    # A main method does not interact with topics, but has its own line of execution -
    # this can be useful for Python libraries that must be run in the main thread. For
    # example, scikit-learn and pyqtgraph are libraries that need the main thread.
    @lg.main
    def run_plot(self) -> None:
        fig = plt.figure()
        self.ax = fig.add_subplot(1, 1, 1)
        self.ax.set_ylim((0, 1))
        anim = animation.FuncAnimation(  # noqa: F841
            fig, self._animate, interval=1 / self.config.refresh_rate * 1000
        )
        plt.show()
        raise lg.NormalTermination()

    def _animate(self, i: int) -> None:
        if self.ax is None or self.state.data is None:
            return
        self.ax.clear()
        self.ax.set_ylim([0, 1])
        self.ax.bar(range(self.config.num_bars), self.state.data)


# ======================================= DEMO =========================================


# A graph for the demo in this example. Hooks together the AveragedNoise group
# (containing NoiseGenerator and RollingAverager) and the Plot node.
class Demo(lg.Graph):
    AVERAGED_NOISE: AveragedNoise
    PLOT: Plot

    def setup(self) -> None:
        # Provide configuration using global constants (but if we wanted to, we could
        # have a configuration object provided to this graph as well).
        self.AVERAGED_NOISE.configure(
            AveragedNoiseConfig(
                num_features=NUM_FEATURES, window=WINDOW,
                read_addr=ENDPOINT, zmq_topic=TOPIC, poll_time=1.0
            )
        )
        self.PLOT.configure(
            PlotConfig(refresh_rate=REFRESH_RATE, num_bars=NUM_FEATURES)
        )

    # Connect the AveragedNoise output to the Plot input
    def connections(self) -> lg.Connections:
        return ((self.AVERAGED_NOISE.OUTPUT, self.PLOT.INPUT),)

    # Parallelization: Run AveragedNoise and Plot in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.AVERAGED_NOISE, self.PLOT)


# Entry point: run the Demo graph
# This demo does the same thing as simple_viz.py, but uses a zmq source (zmq_source.py) rather
# than a hardcoded source.
if __name__ == "__main__":
    print("Initializing ZMQ demo - please run zmq_source.py in another terminal.")
    lg.run(Demo)
