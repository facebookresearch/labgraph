#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import time
import labgraph as lg
import numpy as np

from typing import List, Optional, Dict
from dataclasses import field
from threading import Lock
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.performance_utility import PerfUtility
from pose_vis.streams.messages import VideoFrame, StreamMetaData, ExtensionResults

class DisplayState(lg.State):
    """
    State for Display node

    Attributes:
        `frames`: `List[Optional[np.ndarray]]` aggregation of all running streams' latest frame
        `metadatas`: `List[Optional[StreamMetaData]]` aggregation of all running streams' latest metadata
        `extension_results`: `List[Optional[ExtensionResults]]` aggregation of all running streams' latest extension results
        `lock`: `Lock` used when accessing `frames` or `metadatas`
        `perf`: `PerfUtility` to measure performance
    
    It is assumed `frames` and `metadatas` will contain `None` before video streams send messages
    """
    frames: List[Optional[np.ndarray]] = field(default_factory = list)
    metadatas: List[Optional[StreamMetaData]] = field(default_factory = list)
    extension_results: List[Optional[ExtensionResults]] = field(default_factory = list)
    # Initialize this during setup to avoid pickling issues
    lock: Optional[Lock] = None
    perf: PerfUtility = PerfUtility()

class DisplayConfig(lg.Config):
    """
    Config for Display node

    Attributes:
        `num_streams`: `int` the total number of used inputs
        `target_framerate`: `int` target framerate for updating CV2 windows
        `extension_types`: `Dict[str, type]` type lookup for enabled extensions
    """
    num_streams: int
    target_framerate: int
    extension_types: Dict[str, type]

class Display(lg.Node):
    """
    Display, aggregates all stream sources, draws overlays, and presents them

    Topics:
        `INPUT_FRAMES0`: `VideoFrame`
        `INPUT_FRAMES1`: `VideoFrame`
        `INPUT_FRAMES2`: `VideoFrame`
        `INPUT_FRAMES3`: `VideoFrame`
        `INPUT_EXTS0`: `ExtensionResults`
        `INPUT_EXTS1`: `ExtensionResults`
        `INPUT_EXTS2`: `ExtensionResults`
        `INPUT_EXTS3`: `ExtensionResults`
    
    Attributes:
        `state`: `DisplayState`
        `config`: `DisplayConfig`
    """
    INPUT_FRAMES0 = lg.Topic(VideoFrame)
    INPUT_FRAMES1 = lg.Topic(VideoFrame)
    INPUT_FRAMES2 = lg.Topic(VideoFrame)
    INPUT_FRAMES3 = lg.Topic(VideoFrame)
    INPUT_EXTS0 = lg.Topic(ExtensionResults)
    INPUT_EXTS1 = lg.Topic(ExtensionResults)
    INPUT_EXTS2 = lg.Topic(ExtensionResults)
    INPUT_EXTS3 = lg.Topic(ExtensionResults)
    state: DisplayState
    config: DisplayConfig

    # Async declaration may not be needed here
    async def update_frames(self, message: VideoFrame) -> None:
        with self.state.lock:
            # Reshape given array into (H, W, 3) for CV2
            self.state.frames[message.metadata.stream_id] = message.frame.reshape(message.resolution[1], message.resolution[0], 3)
            self.state.metadatas[message.metadata.stream_id] = message.metadata
    
    @lg.subscriber(INPUT_FRAMES0)
    async def got_frame0(self, message: VideoFrame) -> None:
        await self.update_frames(message)
    
    @lg.subscriber(INPUT_FRAMES1)
    async def got_frame1(self, message: VideoFrame) -> None:
        await self.update_frames(message)
    
    @lg.subscriber(INPUT_FRAMES2)
    async def got_frame2(self, message: VideoFrame) -> None:
        await self.update_frames(message)
    
    @lg.subscriber(INPUT_FRAMES3)
    async def got_frame3(self, message: VideoFrame) -> None:
        await self.update_frames(message)
    
    async def update_exts(self, message: ExtensionResults) -> None:
        with self.state.lock:
            self.state.extension_results[message.metadata.stream_id] = message.results
    
    @lg.subscriber(INPUT_EXTS0)
    async def got_ext0(self, message: ExtensionResults) -> None:
        await self.update_exts(message)
    
    @lg.subscriber(INPUT_EXTS1)
    async def got_ext1(self, message: ExtensionResults) -> None:
        await self.update_exts(message)
    
    @lg.subscriber(INPUT_EXTS2)
    async def got_ext2(self, message: ExtensionResults) -> None:
        await self.update_exts(message)
    
    @lg.subscriber(INPUT_EXTS3)
    async def got_ext3(self, message: ExtensionResults) -> None:
        await self.update_exts(message)

    def setup(self) -> None:
        # Resize each array to the number of streams
        self.state.frames = [None] * self.config.num_streams
        self.state.metadatas = [None] * self.config.num_streams
        self.state.extension_results = [None] * self.config.num_streams
        self.state.lock = Lock()

    @lg.main
    def display(self) -> None:
        while True:
            self.state.perf.update_start()

            with self.state.lock:
                for i in range(self.config.num_streams):
                    if self.state.frames[i] is not None:
                        title = f"PoseVis (stream {self.state.metadatas[i].stream_id}, device {self.state.metadatas[i].device_id})"
                        frame = self.state.frames[i]
                        ext_results = self.state.extension_results[i]
                        if ext_results is not None:
                            for key in ext_results:
                                _type: PoseVisExtension = self.config.extension_types[key]
                                _type.draw_overlay(frame, self.state.metadatas[i], ExtensionResult(data = ext_results[key]))
                        cv2.imshow(title, frame)
                        cv2.setWindowTitle(title, f"{title} stream: {self.state.metadatas[i].actual_framerate}fps, display: {self.state.perf.updates_per_second}fps")

            if cv2.waitKey(1) & 0xFF == 27:
                break

            wait_time = self.state.perf.get_remaining_sleep_time(self.config.target_framerate)
            wait_start = time.perf_counter()
            while time.perf_counter() - wait_start < wait_time:
                continue

            self.state.perf.update_end()
        
        cv2.destroyAllWindows()
        raise lg.NormalTermination()