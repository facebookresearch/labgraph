#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, Dict, Optional, Tuple

import labgraph as lg
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
from pyqtgraph.Qt import QtCore

from .common import TIMER_INTERVAL


class HeatMapState(lg.State):
    """
    State for a HeatMap
    plot: The pyqt plot that we are updating
    data: The data for the heatmap
    """
    plot: Optional[Any] = None
    data: np.ndarray = None
    timer: Optional[QtCore.QTimer] = None


class HeatMapConfig(lg.Config):
    """
    Configuration for a HeatMap
    data: The field on incoming messages for data
    channel_map: The field on the incoming messages for channel_map
    style: Pass any plot functions and params to run in style()
    shape: The shape of the data to visualize
    color_map: The name of the color map to use
    external_timer: Specify whether you are providing an external timer to call update() manually
    """
    data: str = None
    channel_map: str = None
    style: Dict[str, Any] = None
    shape: Tuple[int, int] = None
    color_map: str = "jet"
    external_timer: bool = False


class HeatMap(lg.Node):
    """
    PyQTGraph heat map plot
    Subscribe to a topic and visualize the data in a heat map
    """
    INPUT = lg.Topic(lg.Message)

    state: HeatMapState

    def update(self) -> None:
        if self.state.plot is not None and self.state.data is not None:
            self.update_color_map()
            self.state.plot.setImage(self.state.data)

    @lg.subscriber(INPUT)
    def got_message(self, message: lg.Message) -> None:
        """
        Receive data from input topic
        and display on plot according to HeatMapConfig
        """
        if self.state.plot is not None:
            data = getattr(message, self.config.data)
            # Assuming data is 1d and shape is 2d
            if self.config.shape[0] * self.config.shape[1] != len(data):
                new_data = np.zeros(self.config.shape[0] * self.config.shape[1])
                channel_map = getattr(message, self.config.channel_map)
                for i, d in enumerate(data):
                    new_data[channel_map[i]] = d
                data = new_data
            self.state.data = data.reshape(self.config.shape)

    def update_color_map(self) -> None:
        self.max = np.max(self.state.data)
        # matplotlib color map
        cm_cmap = cm.get_cmap(name=self.config.color_map)
        cm_cmap._init()
        # Convert matplotlib colormap from 0-1 to 0-255 for Qt
        color_lut = (cm_cmap._lut * 255).view(np.ndarray)[:, :3]
        color_lut[0] = [0, 0, 0]  # Lowest value should always be black
        self.state.plot.setLookupTable(color_lut)

    def style(self) -> None:
        """
        Call any style functions for the HeatMap
        """
        if self.config.style:
            for k, v in self.config.style.items():
                if isinstance(v, str):
                    v = (v,)
                if isinstance(v, dict):
                    getattr(self.state.plot, k)(**v)
                else:
                    getattr(self.state.plot, k)(*v)

    def build(self) -> Any:
        """
        Creates, stores, and returns a new ImageItem
        """
        self.state.plot = pg.ImageItem()
        self.style()

        if not self.config.external_timer:
            self.state.timer = QtCore.QTimer()
            self.state.timer.setInterval(TIMER_INTERVAL)
            self.state.timer.start()
            self.state.timer.timeout.connect(self.update)

        return self.state.plot

    def stop(self) -> None:
        self.state.timer.stop()
