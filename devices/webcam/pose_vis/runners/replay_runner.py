#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from pose_vis.utils import absolute_path
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.streams.replay_stream import ReplayStream, ReplayStreamConfig
from pose_vis.display import Display, DisplayConfig
from pose_vis.streams.messages import GraphMetaData
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.extension import PoseVisExtension
from dataclasses import dataclass
from labgraph.loggers.hdf5.reader import HDF5Reader

logger = logging.getLogger(__name__)

@dataclass
class ReplayStreamRunnerConfig():
    """
    Config for ReplayStreamRunner

    Attributes:
        `path`: `str`
        `display_framerate`: `int`
    """
    path: str
    display_framerate: int

class ReplayStreamRunner(PoseVisRunner):
    runner_config: ReplayStreamRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: ReplayStreamRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> None:
        self.runner_config.path = absolute_path(self.runner_config.path)

        log_types = {"metadata": GraphMetaData}
        reader = HDF5Reader(self.runner_config.path, log_types)
        logger.info(f" reading log metadata: {self.runner_config.path}")
        num_streams = reader.logs["metadata"][0].num_streams

        logger.info(f" creating {num_streams} ReplayStream(s)")

        for i in range(num_streams):
            stream_name = f"STREAM{i}"
            input_frames_name = f"INPUT_FRAMES{i}"
            input_exts_name = f"INPUT_EXTS{i}"

            PoseVis.add_node(stream_name, ReplayStream, [stream_name, "OUTPUT_FRAMES", "DISPLAY", input_frames_name],
                ReplayStreamConfig(stream_id = i,
                log_path = self.runner_config.path,
                extensions = self.config.extensions))
            self.set_logger_connections(i)

            PoseVis.add_connection([stream_name, "OUTPUT_EXTENSIONS", "DISPLAY", input_exts_name])

            logger.info(f" created ReplayStream {i} with directory: {self.runner_config.path}")
        
        self.add_graph_metadata(num_streams)

        ext_types = {}
        for cls in PoseVisExtension.__subclasses__():
            ext_types[cls.__name__] = cls
        PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(target_framerate = self.runner_config.display_framerate, num_streams = num_streams, extension_types = ext_types))