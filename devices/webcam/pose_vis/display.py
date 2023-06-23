#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

# Windows-specific performance tuning
import os
if os.name == "nt":
    # Improve sleep timer resolution for this process on Windows
    # https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod
    import ctypes
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)

import logging
import time
import labgraph as lg

from typing import Optional, Dict
from pose_vis.performance_utility import PerfUtility
from pose_vis.streams.messages import CaptureResult, ExitSignal
from pose_vis.display_handler import DisplayHandler

logger = logging.getLogger(__name__)

class DisplayConfig(lg.Config):
    """
    Config for Display node

    Attributes:
        `target_framerate`: `int` target framerate for updating CV2 windows
        `stats_history_size`: `int` how many frame stats to remember
        `extension_types`: `Dict[str, type]` type lookup for enabled extensions
    """
    target_framerate: int
    stats_history_size: int
    extension_types: Dict[str, type]

class DisplayState(lg.State):
    """
    State for Display node

    Attributes:
        `handler`: `DisplayHandler`
        `running`: `bool`
        `perf`: `PerfUtility`
    """
    handler: Optional[DisplayHandler] = None
    running: bool = True
    perf: PerfUtility = PerfUtility()

class Display(lg.Node):
    """
    Draws overlays and presents them

    Topics:
        `INPUT`: `CaptureResult`
    
    Attributes:
        `state`: `DisplayState`
        `config`: `DisplayConfig`
    """
    INPUT = lg.Topic(CaptureResult)
    INPUT_EXIT_STREAM = lg.Topic(ExitSignal)
    INPUT_EXIT_USER = lg.Topic(ExitSignal)
    state: DisplayState
    config: DisplayConfig

    def setup(self) -> None:
        self.state.handler = DisplayHandler(self.config.stats_history_size, self.config.extension_types)
        self.state.handler.register_key_callback(self.on_key)

    @lg.subscriber(INPUT)
    async def update(self, message: CaptureResult) -> None:
        self.state.handler.update_frames(message.captures[:], message.extensions[:])

    @lg.subscriber(INPUT_EXIT_STREAM)
    async def on_exit_stream(self, _: ExitSignal) -> None:
        self.state.running = False
    
    @lg.subscriber(INPUT_EXIT_USER)
    async def on_exit_user(self, _: ExitSignal) -> None:
        self.state.running = False

    def on_key(self, key: int) -> None:
        if key == 27:
            self.state.running = False

    @lg.main
    def display(self) -> None:
        while self.state.running:
            self.state.perf.update_start()
            self.state.handler.update_windows(self.state.perf.updates_per_second)
            time.sleep(self.state.perf.get_remaining_sleep_time(self.config.target_framerate))
            self.state.perf.update_end()

        raise lg.NormalTermination()
    
    def cleanup(self):
        self.state.handler.cleanup()