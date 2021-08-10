#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# For usage see examples/scatter_plot_example.py

import labgraph as lg
import numpy as np
import PyQt5.sip as sip
import pyqtgraph as pg
from dataclasses import asdict, dataclass
from pyqtgraph.Qt import QtCore
from typing import Any, Dict, Optional, Tuple

from .common import TIMER_INTERVAL, AutoRange, AxisRange


@dataclass
class ScatterPlotStyle:
    pen: Optional[Any] = None
    pxMode: bool = True
    symbol: str = "o"
    symbolPen: Optional[Any] = None
    symbolBrush: str = "w"
    symbolSize: int = 10
    name: str = None


class ScatterPlotState(lg.State):
    plot: Optional[Any] = None
    subplots: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Tuple[np.ndarray, np.ndarray]]] = None
    timer: Optional[QtCore.QTimer] = None


class ScatterPlotConfig(lg.Config):
    x_field: str
    y_field: str
    labels: Dict[str, str]
    styles: Dict[str, ScatterPlotStyle]
    x_range: AxisRange = AutoRange()
    y_range: AxisRange = AutoRange()
    y_log_mode: bool = False
    alpha: float = 1.0


class ScatterPlot(lg.Node):
    INPUT = lg.Topic(lg.Message)
    state: ScatterPlotState
    config: ScatterPlotConfig

    def update(self) -> None:
        for name, subplot in self.state.subplots.items():
            if name not in self.state.data:
                continue
            data = self.state.data[name]
            try:
                subplot.clear()
                subplot.setData(x=data[0], y=data[1])
            except RuntimeError:
                if sip.isdeleted(subplot):
                    return
                else:
                    raise

    @lg.subscriber(INPUT)
    def got_message(self, message: lg.Message) -> None:
        if self.state.plot is not None:
            for name in self.config.styles:
                values = getattr(message, name)
                self.state.data[name] = (
                    values[self.config.x_field],
                    values[self.config.y_field],
                )

    def _add_subplot(self, name: str, style: ScatterPlotStyle) -> None:
        style_dict = asdict(style)
        if style_dict["name"] is None:
            style_dict["name"] = name
        self.state.subplots[name] = self.state.plot.plot(**style_dict)
        self.state.subplots[name].setAlpha(self.config.alpha, False)

    def build(self) -> Any:
        self.state.data = {}
        self.state.subplots = {}
        self.state.plot = pg.PlotItem()
        self.state.plot.addLegend(offset=(10, -10))
        if self.config.y_log_mode:
            self.state.plot.setLogMode(y=True)
        if isinstance(self.config.y_range, AutoRange):
            self.state.plot.enableAutoRange(axis="y")
        else:
            self.state.plot.setYRange(*self.config.y_range)
        for position, label in self.config.labels.items():
            self.state.plot.setLabel(position, label)
        for name, style in self.config.styles.items():
            self._add_subplot(name, style)
        self.state.timer = QtCore.QTimer()
        self.state.timer.setInterval(TIMER_INTERVAL)
        self.state.timer.timeout.connect(self.update)
        self.state.timer.start()

        return self.state.plot

    def stop(self) -> None:
        self.state.timer.stop()
