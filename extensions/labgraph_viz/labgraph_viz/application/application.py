#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List

import labgraph as lg
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class ApplicationConfig(lg.Config):
    """
    Config for PyQtApplication
    title: Title for pyqt window
    width: Width of pyqt window
    height: Height of pyqt window
    external_timer: Enable/disable external timer
    external_timer_interval: Override timer interval
    """
    title: str
    width: int
    height: int
    external_timer: bool
    external_timer_interval: int = 33


class Application(lg.Node):
    """
    Creates a pyqt application with a window + plots
    """
    config: ApplicationConfig
    plots: List[lg.Node]

    @lg.main
    def run_plot(self) -> None:
        self.app = QtGui.QApplication([])

        self.setup_window()

        if self.config.external_timer:
            self.timer = QtCore.QTimer()
            self.timer.setInterval(self.config.external_timer_interval)
            self.timer.start()
            self.timer.timeout.connect(self.update)

        self.app.exec_()

        if self.config.external_timer:
            self.timer.stop()
        else:
            for plot in self.plots:
                plot.stop()

    # Using a very simple layout
    # You can subclass and override this method to use another layout
    def setup_window(self) -> None:
        # Window
        self.win = pg.GraphicsWindow()
        self.win.resize(self.config.width, self.config.height)
        self.win.setWindowTitle(self.config.title)

        # Plots
        for plot in self.plots:
            self.win.addItem(plot.build())
            self.win.nextRow()

    def cleanup(self) -> None:
        self.app.quit()

    def update(self) -> None:
        for plot in self.plots:
            plot.update()
