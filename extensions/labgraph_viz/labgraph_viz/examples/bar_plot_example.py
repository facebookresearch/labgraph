#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import labgraph as lg
import numpy as np
import pyqtgraph as pg
from labgraph_viz.plots import BarPlot, BarPlotConfig
from typing import Tuple
from pyqtgraph.Qt import QtGui


# ================================= GENERATORS ===================================

SAMPLE_RATE = 10.0
NUM_FEATURES = 100


# Message for bar plot data
class RandomMessage(lg.Message):
    domain: lg.NumpyType((NUM_FEATURES + 1,), np.int32)
    range: lg.NumpyType((NUM_FEATURES,), np.float64)


# Configuration for the generator
# Specify a sample rate and number of features to output
class GeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int


# Generate RandomMessages to visualize
class Generator(lg.Node):
    OUTPUT = lg.Topic(RandomMessage)
    config: GeneratorConfig

    @lg.publisher(OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT, RandomMessage(
                domain=np.arange(self.config.num_features + 1),
                range=np.random.rand(self.config.num_features),
            )
            await asyncio.sleep(1 / self.config.sample_rate)


# ======================================= PLOTS =========================================

# This is an example of a custom Window Node.
# It creates a new window, sets some properties of the Window,
# adds a plot and starts the QT application.
class Window(lg.Node):
    PLOT: BarPlot

    @lg.main
    def run_plot(self) -> None:
        win = pg.GraphicsWindow()
        win.addItem(self.PLOT.build())
        QtGui.QApplication.instance().exec_()

    def cleanup(self) -> None:
        self.PLOT.stop()
        QtGui.QApplication.instance().quit()


# This is a simple example of how we can display the BarPlot
# in a custom Window Node.
class SimpleVizGroup(lg.Group):
    INPUT = lg.Topic(RandomMessage)

    PLOT: BarPlot
    WINDOW: Window

    def setup(self) -> None:
        # Provide config to the BarPlot
        # x_field: Name of the field on the message to provide x-axis data
        # y_field: Name of the field on the message to provide y-axis data
        # style: Specify pyqtgraph style fields, in this case setLabels
        self.PLOT.configure(
            BarPlotConfig(
                x_field="domain",
                y_field="range",
                style={
                    "setLabels": {
                        "title": "A really cool title",
                        "left": "I'm a label on the left!",
                        "bottom": "I'm a label on the bottom!",
                    }
                },
            )
        )
        self.WINDOW.PLOT = self.PLOT

    # Connect the message to plot input
    def connections(self) -> lg.Connections:
        return ((self.INPUT, self.PLOT.INPUT),)


# ======================================= DEMO =========================================

# A simple graph showing how we can add our group
class Demo(lg.Graph):
    GENERATOR: Generator
    VIZ: SimpleVizGroup

    def setup(self) -> None:
        # Provide configuration using global constants (but if we wanted to, we could
        # have a configuration object provided to this graph as well).
        self.GENERATOR.configure(
            GeneratorConfig(sample_rate=SAMPLE_RATE, num_features=NUM_FEATURES)
        )

    # Connect the Generator outputs to the Plot inputs
    def connections(self) -> lg.Connections:
        return ((self.GENERATOR.OUTPUT, self.VIZ.INPUT),)

    # Parallelization: Run Generator and Viz in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.VIZ)


# Entry point: run the Demo graph
if __name__ == "__main__":
    lg.run(Demo)
