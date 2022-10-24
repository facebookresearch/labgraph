#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import asyncio
import cv2
import labgraph as lg
import numpy as np
import time

from pose_vis.streams.messages import VideoFrame, StreamMetaData, ExtensionResults
from pose_vis.frame_processor import FrameProcessor
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

class CameraStreamConfig(lg.Config):
    """
    Config for CameraStream

    Attributes:
        `device_id`: `int` the device id to initialize
        `stream_id`: `int` the id for this stream
        `device_resolution`: `Tuple[int, int, int]` image width, height, and framerate
        `extensions`: `List[PoseVisExtension]` extension objects to be executed on each frame
    """
    device_id: int
    stream_id: int
    device_resolution: Tuple[int, int, int]
    extensions: List[PoseVisExtension]

class CameraStreamState(lg.State):
    """
    State for CameraStream

    Attributes:
        `cap`: `cv2.VideoCapture` interfaces with camera devices
        `metadata`: `StreamMetaData` utility class sent with ProcessedVideoFrame messages
        `device_resolution`: `np.ndarray` array generated from config value of the same name
        `perf`: `PerfUtility` utility to track frames per second
        `frame_index`: `int` current frame index since startup
        `frame_processor`: `FrameProcessor` handles extension execution
    """
    # Using optional here as LabGraph expects state attributes to be initialized
    # We create and assign these objects during setup
    cap: Optional[cv2.VideoCapture] = None
    metadata: Optional[StreamMetaData] = None
    device_resolution: Optional[np.ndarray] = None
    perf: PerfUtility = PerfUtility()
    frame_index: int = 0
    frame_processor: Optional[FrameProcessor] = None

class CameraStream(lg.Node):
    """
    CameraStream node, captures an image from configured device on a loop, runs the image through each configured extension, and outputs the results

    Topics:
        `OUTPUT_FRAMES`: `VideoFrame`
        `OUTPUT_EXTENSIONS`: `ExtensionResults`
    
    Attributes:
        `config`: `CameraStreamConfig`
        `state`: `CameraStreamState`
    """
    OUTPUT_FRAMES = lg.Topic(VideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(ExtensionResults)
    config: CameraStreamConfig
    state: CameraStreamState

    @lg.publisher(OUTPUT_FRAMES)
    @lg.publisher(OUTPUT_EXTENSIONS)
    async def read_camera(self) -> lg.AsyncPublisher:
        while True:
            self.state.perf.update_start()

            error = False
            cap_state = self.state.cap.isOpened() if self.state.cap else False

            frame: np.ndarray
            timestamp: float
            if cap_state:
                try:
                    success, frame = self.state.cap.read()
                    timestamp = time.time()
                    if not success:
                        error = True
                except cv2.error:
                    error = True

                if error:
                    self.state.cap.release()
                    logger.warning(" device {} capture has encountered an error and has been closed".format(self.config.device_id))
            
            if not cap_state or error:
                # Give a blank image if there's an issue with the device, instead of crashing
                # CV2 uses H x W
                frame = np.zeros(shape = (self.config.device_resolution[1], self.config.device_resolution[0], 3), dtype = np.uint8)
                timestamp = time.time()
            
            # Flatten the images since we don't know their sizes until runtime or data will be stripped when logging
            # https://github.com/facebookresearch/labgraph/issues/20
            yield self.OUTPUT_FRAMES, VideoFrame(frame = frame.reshape(-1),
                timestamp = timestamp,
                resolution = self.state.device_resolution,
                frame_index = self.state.frame_index,
                metadata = self.state.metadata)

            ext_results = self.state.frame_processor.process_frame(frame, self.state.metadata)
            yield self.OUTPUT_EXTENSIONS, ExtensionResults(results = ext_results,
                timestamp = time.time(),
                frame_index = self.state.frame_index,
                metadata = self.state.metadata)

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(self.state.perf.get_remaining_sleep_time(self.config.device_resolution[2]))
            self.state.perf.update_end()

    def setup(self) -> None:
        logger.info(f" opening device id: {self.config.device_id}")
        self.state.cap = cv2.VideoCapture(self.config.device_id)
        if self.state.cap and self.state.cap.isOpened():
            self.state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.device_resolution[0])
            self.state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.device_resolution[1])
            self.state.cap.set(cv2.CAP_PROP_FPS, self.config.device_resolution[2])
            logger.info(f" device {self.config.device_id} opened and configured")
        else:
            logger.warning(" device id {} does not exist".format(self.config.device_id))

        self.state.device_resolution = np.asarray(self.config.device_resolution)

        self.state.metadata = StreamMetaData(
            device_id = self.config.device_id,
            stream_id = self.config.stream_id,
            actual_framerate = 0)
        
        self.state.frame_processor = FrameProcessor()
        self.state.frame_processor.extensions = self.config.extensions
        self.state.frame_processor.stream_id = self.config.stream_id
        self.state.frame_processor.setup()

    def cleanup(self) -> None:
        self.state.frame_processor.cleanup()
        if self.state.cap and self.state.cap.isOpened():
            logger.info(f" closing device id: {self.config.device_id}")
            self.state.cap.release()