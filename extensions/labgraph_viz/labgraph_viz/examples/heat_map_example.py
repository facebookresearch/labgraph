#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import labgraph as lg
import numpy as np
import pyqtgraph as pg
from labgraph_viz.plots import ColorMap, ColorMapConfig, HeatMap, HeatMapConfig
from pyqtgraph.Qt import QtCore, QtGui
from random import random
from typing import Tuple


# ================================= GENERATORS ===================================

SAMPLE_RATE = 10.0
NUM_FEATURES = 1024


# Message for heat map data
class HeatMapMessage(lg.Message):
    channel_map: lg.NumpyDynamicType()
    data: np.ndarray


# Configuration for the generator
# Specify a sample rate and number of features to output
class GeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int


# Generates messages to visualize
class Generator(lg.Node):
    OUTPUT = lg.Topic(HeatMapMessage)
    config: GeneratorConfig

    @lg.publisher(OUTPUT)
    async def generate_update_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT, HeatMapMessage(
                channel_map=np.arange(self.config.num_features),
                data=np.random.rand(self.config.num_features),
            )
            await asyncio.sleep(0.5)


# ======================================= PLOTS =========================================


class Window(lg.Node):
    # Plots
    HEATMAP: HeatMap
    COLOR_MAP: ColorMap

    @lg.main
    def run_plot(self) -> None:
        # Add plots to window
        win = pg.GraphicsWindow()
        win.resize(650, 600)
        view_box = win.addViewBox()
        view_box.invertY()
        view_box.addItem(self.HEATMAP.build())
        color_bar = self.COLOR_MAP.build()
        color_bar.setFixedWidth(50)
        win.addItem(color_bar)

        # Timer to update both plots together
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.start()
        self.timer.timeout.connect(self.update)

        QtGui.QApplication.instance().exec_()

        self.timer.stop()
        self.COLOR_MAP.stop()
        self.HEATMAP.stop()

    def update(self) -> None:
        self.COLOR_MAP.update()
        self.HEATMAP.update()

    def cleanup(self) -> None:
        QtGui.QApplication.instance().quit()


# This is a simple example of how we can display the HeatMap
# and ColorMap in the same window together
class SimpleVizGroup(lg.Group):
    INPUT = lg.Topic(HeatMapMessage)

    HEATMAP: HeatMap
    COLOR_MAP: ColorMap
    WINDOW: Window

    def setup(self) -> None:
        self.HEATMAP.configure(
            HeatMapConfig(
                data="data",
                channel_map="channel_map",
                shape=((32, 32)),
                external_timer=True,
            )
        )
        self.COLOR_MAP.configure(
            ColorMapConfig(
                data="data",
                channel_map="channel_map",
                shape=((32, 32)),
                external_timer=True,
            )
        )
        self.WINDOW.HEATMAP = self.HEATMAP
        self.WINDOW.COLOR_MAP = self.COLOR_MAP

    # Connect the message to both the heat map and color map
    def connections(self) -> lg.Connections:
        return (
            (self.INPUT, self.HEATMAP.INPUT),
            (self.INPUT, self.COLOR_MAP.INPUT),
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

    # Connect the Generator outputs to the Plot inputs
    def connections(self) -> lg.Connections:
        return (
            (self.GENERATOR.OUTPUT, self.VIZ.INPUT),
            (self.GENERATOR.OUTPUT, self.VIZ.INPUT),
        )

    # Parallelization: Run Generator and Viz in separate processes
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.VIZ)


# Entry point: run the Demo graph
if __name__ == "__main__":
    lg.run(Demo)
