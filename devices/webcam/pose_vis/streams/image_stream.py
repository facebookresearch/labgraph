#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import asyncio
import cv2
import labgraph as lg
import numpy as np

from pose_vis.streams.messages import ProcessedVideoFrame, StreamMetaData, CombinedExtensionResult
from pose_vis.frame_processor import FrameProcessor
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from dataclasses import field
from typing import Optional, List

# https://docs.opencv.org/4.2.0/d4/da8/group__imgcodecs.html#ga288b8b3da0892bd651fce07b3bbd3a56
SUPPORTED_EXTENSIONS = [".bmp", ".jpeg", ".jpg", ".png", ".webp"]

class ImageStreamConfig(lg.Config):
    """
    Config for ImageStream

    Attributes:
        `directory`: `str` path to load images from
        `target_framerate`: `int` how many images per second to process
        `stream_id`: `int` the id for this stream
        `extensions`: `List[PoseVisExtension]` extension objects to be executed on each frame
    """
    directory: str
    target_framerate: int
    stream_id: int
    extensions: List[PoseVisExtension]

class ImageStreamState(lg.State):
    """
    State for ImageStream

    Attributes:
        `images`: `List[str]` file paths to each image in a directory
        `metadata`: `StreamMetaData` utility class sent with ProcessedVideoFrame messages
        `perf`: `PerfUtility` utility to track frames per second
        `frame_index`: `int` current frame index since startup
        `frame_processor`: `FrameProcessor` handles extension execution
    """
    # Using optional here as LabGraph expects state attributes to be initialized
    # We create and assign these objects during setup
    images: List[str] = field(default_factory = list)
    metadata: Optional[StreamMetaData] = None
    perf: PerfUtility = PerfUtility()
    frame_index: int = 0
    frame_processor: Optional[FrameProcessor] = None

class ImageStream(lg.Node):
    """
    Loads all images in a directory, runs the image through each configured extension, and outputs the results

    Topics:
        `OUTPUT_FRAMES`: `ProcessedVideoFrame`
        `OUTPUT_EXTENSIONS`: `CombinedExtensionResult`
    
    Attributes:
        `config`: `ImageStreamConfig`
        `state`: `ImageStreamState`
    """
    OUTPUT_FRAMES = lg.Topic(ProcessedVideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(CombinedExtensionResult)
    config: ImageStreamConfig
    state: ImageStreamState

    @lg.publisher(OUTPUT_FRAMES)
    @lg.publisher(OUTPUT_EXTENSIONS)
    async def read_camera(self) -> lg.AsyncPublisher:
        while self.state.frame_index < len(self.state.images):
            self.state.perf.update_start()

            frame = cv2.imread(self.state.images[self.state.frame_index], cv2.IMREAD_COLOR)
            # CV2 uses H x W
            resolution = [frame.shape[1], frame.shape[0], self.config.target_framerate]
            
            overlayed, ext_results = self.state.frame_processor.process_frame(frame.copy(), self.state.metadata)
            # Flatten the images since we don't know their sizes until runtime or data will be stripped when logging
            # https://github.com/facebookresearch/labgraph/issues/20
            yield self.OUTPUT_FRAMES, ProcessedVideoFrame(original = frame.reshape(-1),
                overlayed = overlayed.reshape(-1),
                resolution = np.asarray(resolution, dtype = np.int32),
                frame_index = self.state.frame_index,
                metadata = self.state.metadata)
            yield self.OUTPUT_EXTENSIONS, CombinedExtensionResult(results = ext_results)

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(self.state.perf.get_remaining_sleep_time(self.config.target_framerate))
            self.state.perf.update_end()
        raise lg.NormalTermination()

    def setup(self) -> None:
        print(f"ImageStream: opening directory: {self.config.directory}")
        for _file in os.listdir(self.config.directory):
            ext = os.path.splitext(_file)[1]
            if ext.lower() in SUPPORTED_EXTENSIONS:
                self.state.images.append(os.path.join(self.config.directory, _file))
        print(f"ImageStream: found {len(self.state.images)} image(s)")

        self.state.metadata = StreamMetaData(
            device_id = -1,
            stream_id = self.config.stream_id,
            actual_framerate = 0)
        
        self.state.frame_processor = FrameProcessor()
        self.state.frame_processor.extensions = self.config.extensions
        self.state.frame_processor.stream_id = self.config.stream_id
        self.state.frame_processor.setup()

    def cleanup(self) -> None:
        print("ImageStream: all images processed")
        self.state.frame_processor.cleanup()