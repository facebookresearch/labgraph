#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import asyncio
import cv2
import labgraph as lg
import numpy as np

from pose_vis.streams.messages import ProcessedVideoFrame, StreamMetaData, CombinedExtensionResult
from pose_vis.frame_processor import FrameProcessor
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from typing import Optional, Tuple, List

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
        `perf`: `PerfUtility` utility to track frames per second
        `frame_index`: `int` current frame index since startup
        `frame_processor`: `FrameProcessor` handles extension execution
    """
    # Using optional here as LabGraph expects state attributes to be initialized
    # We create and assign these objects during setup
    cap: Optional[cv2.VideoCapture] = None
    metadata: Optional[StreamMetaData] = None
    perf: PerfUtility = PerfUtility()
    frame_index: int = 0
    frame_processor: Optional[FrameProcessor] = None

class CameraStream(lg.Node):
    """
    CameraStream node, captures an image from configured device on a loop, runs the image through each configured extension, and outputs the results

    Topics:
        `OUTPUT_FRAMES`: `ProcessedVideoFrame`
        `OUTPUT_EXTENSIONS`: `CombinedExtensionResult`
    
    Attributes:
        `config`: `CameraStreamConfig`
        `state`: `CameraStreamState`
    """
    OUTPUT_FRAMES = lg.Topic(ProcessedVideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(CombinedExtensionResult)
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
            if cap_state:
                try:
                    success, frame = self.state.cap.read()
                    if not success:
                        error = True
                except cv2.error:
                    error = True

                if error:
                    self.state.cap.release()
                    print("CameraStream: warning: device {} capture has encountered an error and has been closed".format(self.config.device_id))
            
            if not cap_state or error:
                # Give a blank image if there's an issue with the device, instead of crashing
                # CV2 uses H x W
                frame = np.zeros(shape = (self.config.device_resolution[1], self.config.device_resolution[0], 3), dtype = np.uint8)
            
            overlayed, ext_results = self.state.frame_processor.process_frame(frame, self.state.metadata)
            # Flatten the images since we don't know their sizes until runtime or data will be stripped when logging
            # https://github.com/facebookresearch/labgraph/issues/20
            yield self.OUTPUT_FRAMES, ProcessedVideoFrame(original = frame.reshape(-1),
                overlayed = overlayed.reshape(-1),
                resolution = np.asarray(self.config.device_resolution),
                frame_index = self.state.frame_index,
                metadata = self.state.metadata)
            yield self.OUTPUT_EXTENSIONS, CombinedExtensionResult(results = ext_results)

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(self.state.perf.get_remaining_sleep_time(self.config.device_resolution[2]))
            self.state.perf.update_end()

    def setup(self) -> None:
        print(f"CameraStream: opening device id: {self.config.device_id}")
        self.state.cap = cv2.VideoCapture(self.config.device_id)
        if self.state.cap and self.state.cap.isOpened():
            self.state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.device_resolution[0])
            self.state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.device_resolution[1])
            self.state.cap.set(cv2.CAP_PROP_FPS, self.config.device_resolution[2])
            print(f"CameraStream: device {self.config.device_id} opened and configured")
        else:
            print("CameraStream: warning: device id {} does not exist".format(self.config.device_id))
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
            print(f"CameraStream: closing device id: {self.config.device_id}")
            self.state.cap.release()