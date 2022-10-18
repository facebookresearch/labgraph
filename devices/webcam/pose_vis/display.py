#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import time
import labgraph as lg
import numpy as np

from typing import List, Optional
from dataclasses import field
from threading import Lock
from pose_vis.performance_tracking import PerfUtility
from pose_vis.video_stream import ProcessedVideoFrame, StreamMetaData

class DisplayState(lg.State):
    """
    State for Display node

    Attributes:
        `frames`: `List[Optional[np.ndarray]]` aggregation of all running streams' latest frame
        `metadatas`: `List[Optional[StreamMetaData]]` aggregation of all running streams' latest metadata
        `lock`: `Lock` used when accessing `frames` or `metadatas`
        `perf`: `PerfUtility` to measure performance
    
    It is assumed `frames` and `metadatas` will contain `None` before video streams send messages
    """
    frames: List[Optional[np.ndarray]] = field(default_factory = list)
    metadatas: List[Optional[StreamMetaData]] = field(default_factory = list)
    # Initialize this during setup to avoid pickling issues
    lock: Optional[Lock] = None
    perf: PerfUtility = PerfUtility()

class DisplayConfig(lg.Config):
    """
    Config for Display node

    Attributes:
        `num_streams`: `int` the total number of used inputs
        `target_framerate`: `int` target framerate for updating CV2 windows
    """
    num_streams: int
    target_framerate: int

class Display(lg.Node):
    """
    Display, aggregates all stream sources and displays the overlayed frames

    Topics:
        `INPUT0`: `ProcessedVideoFrame`
        `INPUT1`: `ProcessedVideoFrame`
        `INPUT2`: `ProcessedVideoFrame`
        `INPUT3`: `ProcessedVideoFrame`
    
    Attributes:
        `state`: `DisplayState`
        `config`: `DisplayConfig`
    """
    INPUT0 = lg.Topic(ProcessedVideoFrame)
    INPUT1 = lg.Topic(ProcessedVideoFrame)
    INPUT2 = lg.Topic(ProcessedVideoFrame)
    INPUT3 = lg.Topic(ProcessedVideoFrame)
    state: DisplayState
    config: DisplayConfig

    # Async declaration may not be needed here
    async def update_state(self, message: ProcessedVideoFrame) -> None:
        with self.state.lock:
            # Reshape given array into (H, W, 3) for CV2
            self.state.frames[message.metadata.stream_id] = message.overlayed.reshape(message.resolution[1], message.resolution[0], 3)
            self.state.metadatas[message.metadata.stream_id] = message.metadata
    
    @lg.subscriber(INPUT0)
    async def got_input0(self, message: ProcessedVideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT1)
    async def got_input1(self, message: ProcessedVideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT2)
    async def got_input2(self, message: ProcessedVideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT3)
    async def got_input3(self, message: ProcessedVideoFrame) -> None:
        await self.update_state(message)

    def setup(self) -> None:
        # Resize each array to the number of streams
        self.state.frames = [None] * self.config.num_streams
        self.state.metadatas = [None] * self.config.num_streams
        self.state.lock = Lock()

    @lg.main
    def display(self) -> None:
        while True:
            self.state.perf.update_start()

            with self.state.lock:
                for i in range(self.config.num_streams):
                    if self.state.frames[i] is not None:
                        title = f"PoseVis (stream {self.state.metadatas[i].stream_id}, device {self.state.metadatas[i].device_id})"
                        cv2.imshow(title, self.state.frames[i])
                        cv2.setWindowTitle(title, f"{title} stream: {self.state.metadatas[i].actual_framerate}fps, display: {self.state.perf.updates_per_second}fps")

            if cv2.waitKey(1) & 0xFF == 27:
                break

            wait_time = self.state.perf.get_sleep_time_ns(self.state.perf.last_update_start_ns, self.config.target_framerate)
            wait_start = time.time_ns()
            while time.time_ns() - wait_start < wait_time:
                continue

            self.state.perf.update_end()
        
        cv2.destroyAllWindows()
        raise lg.NormalTermination()