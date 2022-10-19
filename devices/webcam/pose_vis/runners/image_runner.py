#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from pose_vis.utils import absolute_path
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.streams.image_stream import ImageStream, ImageStreamConfig
from pose_vis.streams.termination_handler import TerminationHandler, TerminationHandlerConfig
from pose_vis.pose_vis_graph import PoseVis
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class ImageStreamRunnerConfig():
    """
    Config for ImageStreamRunner

    Atttributes:
        `directories`: `List[str]`
        `framerate`: `int`
    """
    directories: List[str]
    framerate: int

class ImageStreamRunner(PoseVisRunner):
    runner_config: ImageStreamRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: ImageStreamRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> None:
        num_streams = len(self.runner_config.directories)
        for i in range(num_streams):
            self.runner_config.directories[i] = absolute_path(self.runner_config.directories[i])

        logger.info(f" creating {num_streams} ImageStream(s)")

        for i in range(num_streams):
            stream_name = f"STREAM{i}"
            input_name = f"INPUT{i}"

            PoseVis.add_node(stream_name, ImageStream, [stream_name, "OUTPUT_FINISHED", "TERM_HANDLER", input_name],
                ImageStreamConfig(stream_id = i,
                directory = self.runner_config.directories[i],
                target_framerate = self.runner_config.framerate,
                extensions = self.config.extensions))
            self.set_logger_connections(i)

            logger.info(f" created ImageStream {i} with directory: {self.runner_config.directories[i]}")
        
        self.add_graph_metadata(num_streams)

        PoseVis.add_node("TERM_HANDLER", TerminationHandler, config = TerminationHandlerConfig(num_streams = num_streams))