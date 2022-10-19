#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import asyncio
import labgraph as lg

from pose_vis.streams.messages import ProcessedVideoFrame, StreamMetaData, CombinedExtensionResult
from pose_vis.frame_processor import FrameProcessor
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility
from typing import Optional, List
from labgraph.loggers.hdf5.reader import HDF5Reader

logger = logging.getLogger(__name__)

class ReplayStreamConfig(lg.Config):
    """
    Config for ReplayStream

    Attributes:
        `stream_id`: `int` the id for this stream
        `extensions`: `List[PoseVisExtension]` extension objects to be executed on each frame
        `log_path`: `str` absolute path to log file
    """
    stream_id: int
    extensions: List[PoseVisExtension]
    log_path: str

class ReplayStreamState(lg.State):
    """
    State for ReplayStream

    Attributes:
        `metadata`: `StreamMetaData` utility class sent with ProcessedVideoFrame messages
        `perf`: `PerfUtility` utility to track frames per second
        `frame_index`: `int` current frame index since startup
        `frame_processor`: `FrameProcessor` handles extension execution
        `reader`: `Optional[HDF5Reader]` log file reader utility
    """
    # Using optional here as LabGraph expects state attributes to be initialized
    # We create and assign these objects during setup
    metadata: Optional[StreamMetaData] = None
    perf: PerfUtility = PerfUtility()
    frame_index: int = 0
    frame_processor: Optional[FrameProcessor] = None
    reader: Optional[HDF5Reader] = None

class ReplayStream(lg.Node):
    """
    Replays log files

    Topics:
        `OUTPUT_FRAMES`: `ProcessedVideoFrame`
        `OUTPUT_EXTENSIONS`: `CombinedExtensionResult`
    
    Attributes:
        `config`: `LogStreamConfig`
        `state`: `LogStreamState`
    """
    OUTPUT_FRAMES = lg.Topic(ProcessedVideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(CombinedExtensionResult)
    config: ReplayStreamConfig
    state: ReplayStreamState

    @lg.publisher(OUTPUT_FRAMES)
    @lg.publisher(OUTPUT_EXTENSIONS)
    async def read_camera(self) -> lg.AsyncPublisher:
        image_log_name = f"image_stream_{self.config.stream_id}"
        extension_log_name = f"extension_stream_{self.config.stream_id}"
        num_images = len(self.state.reader.logs[image_log_name])
        for i in range(num_images):
            self.state.perf.update_start()

            message: ProcessedVideoFrame = self.state.reader.logs[image_log_name][i]
            if len(self.config.extensions) > 0:
                overlayed, ext_results = self.state.frame_processor.process_frame(message.original.reshape(message.resolution[1], message.resolution[0], 3), self.state.metadata)
                yield self.OUTPUT_FRAMES, ProcessedVideoFrame(original = message.original,
                    overlayed = overlayed,
                    resolution = message.resolution,
                    frame_index = self.state.frame_index,
                    metadata = self.state.metadata)
                yield self.OUTPUT_EXTENSIONS, CombinedExtensionResult(results = ext_results)
            else:
                yield self.OUTPUT_FRAMES, message
                if extension_log_name in self.state.reader.logs:
                    yield self.OUTPUT_EXTENSIONS, self.state.reader.logs[extension_log_name][i]

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(self.state.perf.get_remaining_sleep_time(message.metadata.actual_framerate if message.metadata.actual_framerate > 0 else message.resolution[2]))
            self.state.perf.update_end()
        logger.info(" log replay finished")

    def setup(self) -> None:
        logger.info(f" stream {self.config.stream_id}: reading log")
        image_log_name = f"image_stream_{self.config.stream_id}"
        extension_log_name = f"extension_stream_{self.config.stream_id}"
        self.state.reader = HDF5Reader(self.config.log_path, {image_log_name: ProcessedVideoFrame, extension_log_name: CombinedExtensionResult})

        self.state.metadata = StreamMetaData(
            device_id = self.state.reader.logs[image_log_name][0].metadata.device_id,
            stream_id = self.config.stream_id,
            actual_framerate = 0)

        self.state.frame_processor = FrameProcessor()
        self.state.frame_processor.extensions = self.config.extensions
        self.state.frame_processor.stream_id = self.config.stream_id
        self.state.frame_processor.setup()

    def cleanup(self) -> None:
        self.state.frame_processor.cleanup()