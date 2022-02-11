#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# For usage see examples/spatial_plot_example.py

import labgraph as lg
import numpy as np
import PyQt5.sip as sip
import pyqtgraph as pg
from dataclasses import asdict, dataclass
from matplotlib import cm
from pyqtgraph.Qt import QtCore
from typing import Any, Dict, Optional

from .common import TIMER_INTERVAL


@dataclass
class SpatialPlotStyle:
    pen: Optional[Any] = None
    pxMode: bool = True
    symbol: str = "o"
    symbolSize: int = 10


@dataclass
class SpatialPlotPoints:
    x: np.ndarray
    y: np.ndarray
    style: SpatialPlotStyle


class SpatialPlotState(lg.State):
    plot: Optional[Any] = None
    subplots: Optional[Dict[str, Any]] = None
    brushes: Optional[Dict[str, np.ndarray]] = None
    timer: Optional[QtCore.QTimer] = None


class SpatialPlotConfig(lg.Config):
    color_map: str
    labels: Dict[str, str]
    points: Dict[str, SpatialPlotPoints]


class SpatialPlot(lg.Node):
    INPUT = lg.Topic(lg.Message)
    state: SpatialPlotState
    config: SpatialPlotConfig

    def setup(self) -> None:
        if not self.is_configured:
            return
        color_map = cm.get_cmap(self.config.color_map)
        color_map._init()
        color_lut = color_map._lut.view(np.ndarray)
        colors = (color_lut * 255).astype(int)
        self._color_map = pg.ColorMap(np.linspace(0.0, 1.0, colors.shape[0]), colors)
        self._np_mkBrush = np.vectorize(pg.mkBrush)

    def update(self) -> None:
        for name, subplot in self.state.subplots.items():
            if name not in self.state.brushes:
                continue
            brushes = self.state.brushes[name]
            try:
                subplot.scatter.setBrush(brushes)
            except RuntimeError:
                if sip.isdeleted(subplot) or sip.isdeleted(subplot.scatter):
                    return
                else:
                    raise

    @lg.subscriber(INPUT)
    def got_message(self, message: lg.Message) -> None:
        if self.state.plot is not None:
            for name in self.config.points:
                values = getattr(message, name)
                colors = self._color_map.map(values, mode="qcolor")
                self.state.brushes[name] = self._np_mkBrush(colors)

    def _add_subplot(self, name: str, points: SpatialPlotPoints) -> None:
        style_dict = asdict(points.style)
        style_dict["name"] = name
        self.state.subplots[name] = self.state.plot.plot(**style_dict)
        self.state.subplots[name].setData(x=points.x, y=points.y)

    def build(self) -> Any:
        self.state.brushes = {}
        self.state.subplots = {}
        self.state.plot = pg.PlotItem()
        self.state.plot.addLegend(offset=(10, -10))
        for position, label in self.config.labels.items():
            self.state.plot.setLabel(position, label)
        for name, points in self.config.points.items():
            self._add_subplot(name, points)
        self.state.timer = QtCore.QTimer()
        self.state.timer.setInterval(TIMER_INTERVAL)
        self.state.timer.timeout.connect(self.update)
        self.state.timer.start()

        return self.state.plot

    def stop(self) -> None:
        self.state.timer.stop()
