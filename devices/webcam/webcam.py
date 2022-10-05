#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import asyncio
import cv2
import time
import labgraph as lg
import numpy as np

from typing import Optional

class VideoFrame(lg.Message):
    """
    Represents a single frame of a video's stream

    @attributes:
        frame: ndarray, a (W, H, 3) shape array of the video's stream, in the blue/green/red color space
        timestamp: float, time of capture
    """

    frame: np.ndarray
    timestamp: float

class WebcamStreamConfig(lg.Config):
    """
    Config for WebcamStream node

    @attributes:
        sample_rate: int, how many times per second to sample the webcam
        device_number: int, which device to initialize
        device_resolution: ndarray, a (2) shaped array of the desired output resolution
    """

    sample_rate: int
    device_number: int
    device_resolution: np.ndarray

class WebcamStreamState(lg.State):
    """
    State for WebcamStream node

    @attributes:
        cap: CV2's VideoCapture object
    """

    cap: Optional[cv2.VideoCapture] = None

class WebcamStream(lg.Node):
    """
    WebcamStream node, publishes VideoFrame at the configured sample rate

    @topics:
        OUTPUT: VideoFrame

    @attributes:
        config: WebcamStreamConfig
        state: WebcamStreamState
    """

    OUTPUT = lg.Topic(VideoFrame)
    config: WebcamStreamConfig
    state: WebcamStreamState

    @lg.publisher(OUTPUT)
    async def read_webcam(self) -> lg.AsyncPublisher:
        while self.state.cap.isOpened():
            start_time_ns = time.time_ns()

            success, frame = self.state.cap.read()
            if success:
                yield self.OUTPUT, VideoFrame(timestamp = time.time(), frame = frame)
            
            target_delta_time_ns = int(1000000000 / self.config.sample_rate)
            actual_delta_time_ns = time.time_ns() - start_time_ns
            sleepTime = float((target_delta_time_ns - actual_delta_time_ns) / 1000000000)
            await asyncio.sleep(0 if sleepTime < 0 else sleepTime)

    def setup(self) -> None:
        self.state.cap = cv2.VideoCapture(self.config.device_number)
        self.state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.device_resolution[0])
        self.state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.device_resolution[1])

    def cleanup(self) -> None:
        self.state.cap.release()