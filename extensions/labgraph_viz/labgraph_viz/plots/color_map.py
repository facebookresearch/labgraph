#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# For usage see examples/heat_map_example.py

from typing import Any, Optional, Tuple

import labgraph as lg
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
from pyqtgraph.Qt import QtCore, QtWidgets

from .common import TIMER_INTERVAL


class ColorMapGraphicsObject(QtWidgets.QGraphicsObject):
    scale_axis_signal = QtCore.pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.scale_axis_signal.connect(self.scale_axis)

    @QtCore.pyqtSlot(object, object)
    def scale_axis(self, plot, data):
        axis = plot.getAxis("right")
        axis.setScale(np.max(data) / 255)


class ColorMapState(lg.State):
    """
    State for a ColorMap
    data: The data for the colormap
    plot: The pyqt plot that we are updating
    color_map: The data for the color map
    timer: Timer to update plot
    """
    data: np.ndarray = None
    plot: Optional[Any] = None
    color_map: np.ndarray = None
    timer: Optional[QtCore.QTimer] = None


class ColorMapConfig(lg.Config):
    """
    Configuration for a ColorMap
    data: The field on incoming messages for data associated with the data
    shape: The shape of the data to visualize
    color_map: The name of the color map to use
    external_timer: Specify whether you are providing an external timer to call update() manually
    """
    data: str = None
    channel_map: str = None
    shape: Tuple[int, int] = None
    color_map: str = "jet"
    external_timer: bool = False


class ColorMap(lg.Node):
    """
    PyQTGraph color map
    Subscribe to a topic and visualize the color map as a bar
    """
    INPUT = lg.Topic(lg.Message)

    config: ColorMapConfig
    state: ColorMapState

    color_map_bar_graphics_object = ColorMapGraphicsObject()

    def update(self) -> None:
        if self.state.plot is not None and self.state.data is not None:
            self.color_map_bar_graphics_object.scale_axis_signal.emit(
                self.state.plot,
                self.state.data,
            )

    @lg.subscriber(INPUT)
    def got_message(self, message: lg.Message) -> None:
        """
        Receive data from input topic
        and display on plot according to ColorMapconfig
        """
        data = getattr(message, self.config.data)
        # Assuming data is 1d and shape is 2d
        if self.config.shape[0] * self.config.shape[1] != len(data):
            new_data = np.zeros(self.config.shape[0] * self.config.shape[1])
            channel_map = getattr(message, self.config.channel_map)
            for i, d in enumerate(data):
                new_data[channel_map[i]] = d
            self.state.data = new_data.reshape(self.config.shape)

    def setup(self) -> None:
        # matplotlib color map
        cm_cmap = cm.get_cmap(name=self.config.color_map)
        cm_cmap._init()
        # Convert matplotlib colormap from 0-1 to 0-255 for Qt
        color_lut = (cm_cmap._lut * 255).view(np.ndarray)[:, :3]

        self.state.color_map = np.repeat(color_lut, 16, axis=0).reshape(
            (color_lut.shape[0], 16, 3)
        )
        # Make the color bar vertical
        self.state.color_map = np.rot90(self.state.color_map, axes=(0, 1))

    def build(self) -> Any:
        """
        Wait until this method is called to build the plot
        """
        self.state.plot = pg.PlotItem()
        self.state.plot.addItem(pg.ImageItem(self.state.color_map))
        # Show y axis on right side
        self.state.plot.hideAxis("bottom")
        self.state.plot.hideAxis("left")
        self.state.plot.showAxis("right")

        if not self.config.external_timer:
            self.state.timer = QtCore.QTimer()
            self.state.timer.setInterval(TIMER_INTERVAL)
            self.state.timer.start()
            self.state.timer.timeout.connect(self.update)

        return self.state.plot

    def stop(self) -> None:
        if not self.config.external_timer:
            self.state.timer.stop()
