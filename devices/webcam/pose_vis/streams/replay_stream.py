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
import asyncio
import labgraph as lg

from pose_vis.streams.messages import CaptureResult, ExitSignal
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from typing import Optional, List
from labgraph.loggers.hdf5.reader import HDF5Reader

logger = logging.getLogger(__name__)

class ReplayStreamConfig(lg.Config):
    """
    Config for ReplayStream

    Attributes:
        `extensions`: `List[PoseVisExtension]` extension objects to be executed on each frame
        `log_path`: `str` absolute path to log file
    """
    extensions: List[PoseVisExtension]
    log_path: str

class ReplayStreamState(lg.State):
    """
    State for ReplayStream

    Attributes:
        `perf`: `PerfUtility` utility to track frames per second
        `reader`: `Optional[HDF5Reader]` log file reader utility
    """
    # Using optional here as LabGraph expects state attributes to be initialized
    # We create and assign these objects during setup
    perf: PerfUtility = PerfUtility()
    reader: Optional[HDF5Reader] = None

class ReplayStream(lg.Node):
    """
    Replays log files

    Topics:
        `OUTPUT`: `CaptureResult`
    
    Attributes:
        `config`: `LogStreamConfig`
        `state`: `LogStreamState`
    """
    OUTPUT = lg.Topic(CaptureResult)
    OUTPUT_EXIT = lg.Topic(ExitSignal)
    config: ReplayStreamConfig
    state: ReplayStreamState

    @lg.publisher(OUTPUT)
    @lg.publisher(OUTPUT_EXIT)
    async def read_log(self) -> lg.AsyncPublisher:
        num_captures = len(self.state.reader.logs["captures"])
        for i in range(num_captures):
            self.state.perf.update_start()

            # TODO: run extensions if enabled
            capture: CaptureResult = self.state.reader.logs["captures"][i]
            yield self.OUTPUT, capture

            await asyncio.sleep(capture.stream_time)

            self.state.perf.update_end()

        logger.info(" log replay finished")
        yield self.OUTPUT_EXIT, ExitSignal()

    def setup(self) -> None:
        logger.info(f" reading log: {self.config.log_path}")
        self.state.reader = HDF5Reader(self.config.log_path, {"captures": CaptureResult})

    def cleanup(self) -> None:
        pass