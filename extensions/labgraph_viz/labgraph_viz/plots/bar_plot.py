#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# For usage see examples/bar_plot_example.py

from dataclasses import dataclass
import labgraph as lg
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from typing import Any, Dict, Optional

from .common import TIMER_INTERVAL


@dataclass
class BarPlotData:
    """
    Holds data for a bar plot
    """
    x: int
    x0: int
    x1: int
    height: int
    width: int


class PlotState(lg.State):
    """
    State for a PlotNode
    plot: The pyqt plot that we are updating
    plot_item: pyqt PlotItem
    data: raw data for the plot
    """
    plot: Optional[Any] = None
    plot_item: Optional[Any] = None
    data: BarPlotData = None


class BarPlotConfig(lg.Config):
    """
    Configuration for a PlotNode
    x_field: The field on incoming messages for data associated with the x axis
    y_field: The field on incoming messages for data associated with the y axis
    style: Pass any plot functions and params to run in style()
    external_timer: Specify whether you are providing an external timer to call update() manually
    """
    x_field: str
    y_field: str
    style: Dict[str, Any] = None
    external_timer: bool = False


class BarPlot(lg.Node):
    """
    PyQTGraph bar plot
    Subscribe to a topic and visualize the data in a bar plot
    """
    INPUT = lg.Topic(lg.Message)
    state: PlotState
    config: BarPlotConfig

    timer: Optional[QtCore.QTimer] = None

    @lg.subscriber(INPUT)
    def got_message(self, message: lg.Message) -> None:
        """
        Receive data from input topic
        and display on plot according to BarPlotConfig
        """
        if self.state.plot is not None:
            x = getattr(message, self.config.x_field)
            height = getattr(message, self.config.y_field)
            x0 = x[:-1]
            x1 = x[1:]
            width = x1[0] - x0[0]
            self.state.data = BarPlotData(x, x0, x1, height, width)

    def update(self) -> None:
        if self.state.data:
            self.state.plot.setOpts(
                x=self.state.data.x,
                x0=self.state.data.x0,
                x1=self.state.data.x1,
                height=self.state.data.height,
                width=self.state.data.width,
            )

    def _style(self) -> None:
        if self.config.style:
            for k, v in self.config.style.items():
                if isinstance(v, str):
                    v = (v,)
                if isinstance(v, dict):
                    getattr(self.state.plot_item, k)(**v)
                else:
                    getattr(self.state.plot_item, k)(*v)

    def build(self) -> Any:
        """
        Creates, stores, and returns a new BarGraphItem
        """
        self.state.plot_item = pg.PlotItem()
        self._style()
        self.state.plot = pg.BarGraphItem(x=[], height=[], width=1)
        self.state.plot_item.addItem(self.state.plot)

        if not self.config.external_timer:
            self.timer = QtCore.QTimer()
            self.timer.setInterval(TIMER_INTERVAL)
            self.timer.start()
            self.timer.timeout.connect(self.update)

        return self.state.plot_item

    def stop(self) -> None:
        self.timer.stop()
