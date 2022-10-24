#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import time
import asyncio
import labgraph as lg

from pose_vis.streams.messages import VideoFrame, StreamMetaData, ExtensionResults
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
        `OUTPUT_FRAMES`: `VideoFrame`
        `OUTPUT_EXTENSIONS`: `ExtensionResults`
    
    Attributes:
        `config`: `LogStreamConfig`
        `state`: `LogStreamState`
    """
    OUTPUT_FRAMES = lg.Topic(VideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(ExtensionResults)
    config: ReplayStreamConfig
    state: ReplayStreamState

    @lg.publisher(OUTPUT_FRAMES)
    @lg.publisher(OUTPUT_EXTENSIONS)
    async def read_log(self) -> lg.AsyncPublisher:
        image_log_name = f"image_stream_{self.config.stream_id}"
        extension_log_name = f"extension_stream_{self.config.stream_id}"
        num_images = len(self.state.reader.logs[image_log_name])
        for i in range(num_images):
            self.state.perf.update_start()

            frame_message: VideoFrame = self.state.reader.logs[image_log_name][i]
            yield self.OUTPUT_FRAMES, frame_message
            
            ext_message: ExtensionResults
            # Due to extension results being yielded seperately, it may be possible the last message gets dropped,
            # depending on how the graph was terminated
            if extension_log_name in self.state.reader.logs and len(self.state.reader.logs[extension_log_name]) > i:
                ext_message = self.state.reader.logs[extension_log_name][i]
            
            if len(self.config.extensions) > 0:                
                ext_results = {} if ext_message is None else ext_message.results
                ext_results.update(self.state.frame_processor.process_frame(frame_message.frame.reshape(frame_message.resolution[1], frame_message.resolution[0], 3), self.state.metadata))
                yield self.OUTPUT_EXTENSIONS, ExtensionResults(results = ext_results,
                    timestamp = time.time(),
                    frame_index = self.state.frame_index,
                    metadata = self.state.metadata)
            else:
                yield self.OUTPUT_EXTENSIONS, ext_message
                

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(self.state.perf.get_remaining_sleep_time(frame_message.metadata.actual_framerate if frame_message.metadata.actual_framerate > 0 else frame_message.resolution[2]))
            self.state.perf.update_end()
        logger.info(" log replay finished")

    def setup(self) -> None:
        logger.info(f" stream {self.config.stream_id}: reading log")
        image_log_name = f"image_stream_{self.config.stream_id}"
        extension_log_name = f"extension_stream_{self.config.stream_id}"
        self.state.reader = HDF5Reader(self.config.log_path, {image_log_name: VideoFrame, extension_log_name: ExtensionResults})

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