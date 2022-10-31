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

import time
import logging
import traceback
import asyncio
import labgraph as lg

from typing import Tuple, List, Union, Optional
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from pose_vis.streams.messages import CaptureResult, ExitSignal
from pose_vis.streams.utils.capture_handler import CaptureHandler, AllCapturesFinished

logger = logging.getLogger(__name__)

class SourceStreamConfig(lg.Config):
    """
    Config for `SourceStream`

    Attributes:
        `sources`: `List[Union[int, str]]` which sources to initialize
        `resolutions`: `List[Tuple[int, int, int]]` resolution per source
        NOTE: `SourceStream` will run at the lowest provided framerate
        `extensions`: `List[PoseVisExtension]` extension instances to be initialized in each source
        `target_framerate`: `int` target framerate for this node to achieve
    """
    sources: List[Union[int, str]]
    resolutions: List[Tuple[int, int, int]]
    extensions: List[PoseVisExtension]
    target_framerate: int

class SourceStreamState(lg.State):
    """
    State for `SourceStream`

    Attributes:
        `handler`: `Optional[CaptureHandler]`
        `perf`: `PerfUtility`
    """
    handler: Optional[CaptureHandler] = None
    perf: PerfUtility = PerfUtility()

class SourceStream(lg.Node):
    """
    Captures frames from all sources and publishes them with a `CaptureResult` message

    Topics:
        `OUTPUT`: publishes `CaptureResult`
        `OUTPUT_EXIT` publishes `ExitSignal`
    """
    OUTPUT = lg.Topic(CaptureResult)
    OUTPUT_EXIT = lg.Topic(ExitSignal)
    config: SourceStreamConfig
    state: SourceStreamState

    def setup(self) -> None:
        self.state.handler = CaptureHandler(self.config.sources, self.config.resolutions, self.config.extensions)

    @lg.publisher(OUTPUT)
    @lg.publisher(OUTPUT_EXIT)
    async def read_sources(self) -> lg.AsyncPublisher:
        has_video_source = False
        
        num_sources = len(self.config.sources)
        for i in range(num_sources):
            if isinstance(self.config.sources[i], str):
                has_video_source = True
        
        self.state.handler.start_workers()

        while True:
            try:
                self.state.perf.update_start()

                result = self.state.handler.get_captures()
                yield self.OUTPUT, CaptureResult(
                    [result[i][0] for i in range(num_sources)],
                    [result[i][1] for i in range(num_sources)])

                if has_video_source:
                    # This gives a more accurate sleep period on Windows without stalling the node
                    # Doesn't seem to hurt on other systems
                    wait_time = self.state.perf.get_remaining_sleep_time(self.config.target_framerate)
                    wait_start = time.perf_counter()
                    while time.perf_counter() - wait_start < wait_time:
                        await asyncio.sleep(0.001)
                else:
                    # When capturing from a device, CV2 VideoCapture will block to keep the configured framerate
                    # a small sleep period keeps the node from stalling
                    await asyncio.sleep(0.002)

                self.state.perf.update_end()
            except Exception as e:
                if not isinstance(e, AllCapturesFinished):
                    logger.critical(traceback.format_exc())
                    logger.critical(" an exception occurred in a source thread or process, exiting")
                else:
                    logger.info(" all captures have finished")
                break
        
        yield self.OUTPUT_EXIT, ExitSignal()

    def cleanup(self) -> None:
        self.state.handler.cleanup()