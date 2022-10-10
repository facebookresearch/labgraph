#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import time
import labgraph as lg
import numpy as np

from typing import Optional, Tuple

from pose_vis.performance_tracking import PerfUtility

class VideoFrame(lg.Message):
    frame: lg.NumpyDynamicType
    timestamp: float
    device_id: int
    frame_index: int
    stream_id: int
    update_time_ms: int
    updates_per_second: int

class ReadyMessage(lg.Message):
    pass

class SynchronizedCameraStreamConfig(lg.Config):
    device_id: int
    stream_id: int
    device_resolution: Tuple[int, int]

class SynchronizedCameraStreamState(lg.State):
    cap: Optional[cv2.VideoCapture] = None
    is_ready: bool = True
    frame_index: int = 0
    perf: PerfUtility = PerfUtility()

class SynchronizedCameraStream(lg.Node):
    OUTPUT = lg.Topic(VideoFrame)
    INPUT = lg.Topic(ReadyMessage)
    config: SynchronizedCameraStreamConfig
    state: SynchronizedCameraStreamState

    @lg.publisher(OUTPUT)
    @lg.subscriber(INPUT)
    async def read_camera(self, message: ReadyMessage) -> lg.AsyncPublisher:
        start_time_ns = time.time_ns()

        error = False
        cap_state = self.state.cap.isOpened() if self.state.cap else False

        if cap_state:
            success, frame = self.state.cap.read()
            if success:
                try:
                    yield self.OUTPUT, VideoFrame(
                        timestamp = time.time(),
                        frame = frame,
                        device_id = self.config.device_id,
                        stream_id = self.config.stream_id,
                        frame_index = self.state.frame_index,
                        update_time_ms = PerfUtility.ns_to_ms(time.time_ns() - start_time_ns),
                        updates_per_second = self.state.perf.updates_per_second)
                except cv2.error:
                    error = True
            else:
                error = True
            
            if error:
                self.state.cap.release()
                print("SynchronizedCameraStream: device {} capture has encountered an error and has been closed".format(self.config.device_id))
        
        if not cap_state or error:
            yield self.OUTPUT, VideoFrame(
                timestamp = time.time(),
                frame = np.zeros(shape = (self.config.device_resolution[1], self.config.device_resolution[0], 3), dtype = np.uint8),
                device_id = self.config.device_id,
                stream_id = self.config.stream_id,
                frame_index = self.state.frame_index,
                update_time_ms = PerfUtility.ns_to_ms(time.time_ns() - start_time_ns),
                updates_per_second = self.state.perf.updates_per_second)
        
        self.state.frame_index += 1
        self.state.perf.update_end()
        self.state.perf.update_start()

    def setup(self) -> None:
        self.state.cap = cv2.VideoCapture(self.config.device_id)
        if self.state.cap and self.state.cap.isOpened():
            self.state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.device_resolution[0])
            self.state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.device_resolution[1])
        else:
            print("SynchronizedCameraStream: device {} does not exist".format(self.config.device_id))

    def cleanup(self) -> None:
        if self.state.cap and self.state.cap.isOpened():
            self.state.cap.release()