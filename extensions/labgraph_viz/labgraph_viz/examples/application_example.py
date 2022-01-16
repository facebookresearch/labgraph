#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import labgraph as lg
import numpy as np
import pyqtgraph as pg
import time
from labgraph_viz.application import Application, ApplicationConfig
from labgraph_viz.plots import BarPlot, BarPlotConfig, LinePlot, LinePlotConfig, Mode
from random import random
from typing import Tuple


# ================================= GENERATORS ===================================

SAMPLE_RATE = 10.0
NUM_FEATURES = 100


# Message for bar plot data
class BarPlotMessage(lg.Message):
    domain: lg.NumpyType((NUM_FEATURES + 1,), np.int32)
    range: lg.NumpyType((NUM_FEATURES,), np.float64)


# Message for line plot data
class LinePlotMessage(lg.Message):
    timestamp: float
    data: float


# Configuration for the generator
# Specify a sample rate and number of features to output
class GeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int


# Generates messages to visualize
class Generator(lg.Node):
    BARPLOT_OUTPUT = lg.Topic(BarPlotMessage)
    LINEPLOT_OUTPUT = lg.Topic(LinePlotMessage)
    config: GeneratorConfig

    @lg.publisher(BARPLOT_OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.BARPLOT_OUTPUT, BarPlotMessage(
                domain=np.arange(self.config.num_features + 1, dtype=np.int32),
                range=np.random.rand(self.config.num_features).astype(np.float64),
            )
            await asyncio.sleep(1 / self.config.sample_rate)

    @lg.publisher(LINEPLOT_OUTPUT)
    async def generate__noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.LINEPLOT_OUTPUT, LinePlotMessage(timestamp=time.time(), data=random() * 100)
            await asyncio.sleep(1 / self.config.sample_rate)


# ======================================= PLOTS =========================================

# This is a simple example of how we use the application class
class SimpleVizGroup(lg.Group):
    # Messages
    BAR_PLOT_INPUT = lg.Topic(BarPlotMessage)
    LINE_PLOT_INPUT = lg.Topic(LinePlotMessage)

    # Application
    application: Application

    # Plots
    line_plot: LinePlot
    bar_plot: BarPlot

    def setup(self) -> None:
        # Configure plots
        self.bar_plot.configure(
            BarPlotConfig(
                x_field="domain",
                y_field="range",
                external_timer=True,
            ))
        self.line_plot.configure(
            LinePlotConfig(
                x_field="timestamp",
                y_field="data",
                mode=Mode.APPEND,
                window_size=20,
                external_timer=True,
            )
        )

        # Configure application
        # By enabling external_timer we ensure that the plots are updated
        # in sync
        self.application.configure(
            ApplicationConfig(
                title="A moderately cool application",
                width=640,
                height=1000,
                external_timer=True,
                external_timer_interval=200,
            )
        )

        # Add plots to application
        self.application.plots = [self.line_plot, self.bar_plot]

    # Connect the Generator outputs to the Plot inputs
    def connections(self) -> lg.Connections:
        return (
            (self.BAR_PLOT_INPUT, self.bar_plot.INPUT),
            (self.LINE_PLOT_INPUT, self.line_plot.INPUT),
        )


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
        return (
            (self.GENERATOR.BARPLOT_OUTPUT, self.VIZ.BAR_PLOT_INPUT),
            (self.GENERATOR.LINEPLOT_OUTPUT, self.VIZ.LINE_PLOT_INPUT),
        )

    # Parallelization: Run Generator and Viz in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.VIZ)


# Entry point: run the Demo graph
if __name__ == "__main__":
    lg.run(Demo)
