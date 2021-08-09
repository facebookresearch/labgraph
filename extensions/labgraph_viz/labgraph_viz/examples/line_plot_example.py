#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import labgraph as lg
import numpy as np
import pyqtgraph as pg
import time
from labgraph_viz.plots import LinePlot, LinePlotConfig, Mode
from pyqtgraph.Qt import QtGui
from random import random
from typing import Tuple


# ================================= GENERATORS ===================================

SAMPLE_RATE = 10.0
NUM_FEATURES = 100


# Message for append data
class AppendMessage(lg.Message):
    timestamp: float
    data: float


# Message for update data
class UpdateMessage(lg.Message):
    domain: lg.NumpyType((NUM_FEATURES,), np.int)
    range: lg.NumpyType((NUM_FEATURES,), np.float64)


# Configuration for the generator
# Specify a sample rate and number of features to output
class GeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int


# Generates messages to visualize
class Generator(lg.Node):
    OUTPUT = lg.Topic(AppendMessage)
    OUTPUT_2 = lg.Topic(UpdateMessage)
    config: GeneratorConfig

    @lg.publisher(OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT, AppendMessage(timestamp=time.time(), data=random() * 100)
            await asyncio.sleep(1 / self.config.sample_rate)

    @lg.publisher(OUTPUT_2)
    async def generate_update_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT_2, UpdateMessage(
                domain=np.arange(self.config.num_features),
                range=np.random.rand(self.config.num_features),
            )
            await asyncio.sleep(0.5)


# ======================================= PLOTS =========================================


# This is an example of a custom Window Node.
# It creates a new window, sets some properties of the Window,
# adds some plots and starts the QT application.
class Window(lg.Node):
    PLOT: LinePlot
    PLOT_2: LinePlot

    @lg.main
    def run_plot(self) -> None:
        # Here we are creating a simple pyqtgraph window
        # but you can be more creative!
        win = pg.GraphicsWindow()
        win.addItem(self.PLOT.build())
        win.nextRow()
        win.addItem(self.PLOT_2.build())
        QtGui.QApplication.instance().exec_()

    def cleanup(self) -> None:
        self.PLOT.stop()
        self.PLOT_2.stop()
        QtGui.QApplication.instance().quit()



# This is a simple example of how we can display the LinePlot
# in a custom Window Node.
class SimpleVizGroup(lg.Group):
    INPUT_1 = lg.Topic(AppendMessage)
    INPUT_2 = lg.Topic(UpdateMessage)

    PLOT: LinePlot
    PLOT_2: LinePlot
    WINDOW: Window

    def setup(self) -> None:
        # Provide config to the first LinePlot
        # x_field: Name of the field on the message to provide x-axis data
        # y_field: Name of the field on the message to provide y-axis data
        # mode: APPEND tells the LinePlot to append each message to existing data
        # window_size: LinePlot will display a scrolling window of 20 samples
        self.PLOT.configure(
            LinePlotConfig(
                x_field="timestamp", y_field="data", mode=Mode.APPEND, window_size=20
            )
        )
        # Provide config to the second LinePlot
        # x_field: Name of the field on the message to provide x-axis data
        # y_field: Name of the field on the message to provide y-axis data
        # mode: UPDATE tells the LinePlot to overwrite existing data on each messages
        self.PLOT_2.configure(
            LinePlotConfig(x_field="domain", y_field="range", mode=Mode.UPDATE)
        )
        self.WINDOW.PLOT = self.PLOT
        self.WINDOW.PLOT_2 = self.PLOT_2
    
    # Connect the messages to the corresponding plots
    def connections(self) -> lg.Connections:
        return (
            (self.INPUT_1, self.PLOT.INPUT),
            (self.INPUT_2, self.PLOT_2.INPUT),
        )


# ======================================= DEMO =========================================


# A simple graph that shows how we add our groups and allow them to work together.
class Demo(lg.Graph):
    GENERATOR: Generator
    VIZ: SimpleVizGroup

    def setup(self) -> None:
        # Provide configuration using global constants (but if we wanted to, we could
        # have a configuration object provided to this graph as well).
        self.GENERATOR.configure(
            GeneratorConfig(sample_rate=SAMPLE_RATE, num_features=NUM_FEATURES)
        )

    # Connect the Generator outputs to the plot inputs
    def connections(self) -> lg.Connections:
        return (
            (self.GENERATOR.OUTPUT, self.VIZ.INPUT_1),
            (self.GENERATOR.OUTPUT_2, self.VIZ.INPUT_2),
        )

    # Parallelization: Run Generator and Viz in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.VIZ)


# Entry point: run the Demo graph
if __name__ == "__main__":
    lg.run(Demo)
