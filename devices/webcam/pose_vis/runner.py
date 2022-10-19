#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import labgraph as lg

from pose_vis.utils import absolute_path
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.extension import PoseVisExtension
from pose_vis.streams.graph_metadata import GraphMetaDataProvider, GraphMetaDataProviderConfig
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class PoseVisConfig():
    extensions: List[PoseVisExtension]
    log_directory: str
    log_name: Optional[str]
    log_images: bool
    log_poses: bool

class PoseVisRunner(ABC):

    config: PoseVisConfig

    def __init__(self, config: PoseVisConfig) -> None:
        self.config = config

    def add_graph_metadata(self, num_streams: int) -> None:
        PoseVis.add_node("METADATA", GraphMetaDataProvider, config = GraphMetaDataProviderConfig(num_streams = num_streams))
        if self.config.log_images or self.config.log_poses:
            PoseVis.add_logger_connection(("metadata", "METADATA", "OUTPUT"))

    def set_logger_connections(self, stream_index: int) -> None:
        image_log_name = f"image_stream_{stream_index}"
        extension_log_name = f"extension_stream_{stream_index}"
        stream_name = f"STREAM{stream_index}"
        if self.config.log_images:
            PoseVis.add_logger_connection((image_log_name, stream_name, "OUTPUT_FRAMES"))
            logger.info(f" enabled image logging for stream {stream_index} with the following path: {image_log_name}")
        if self.config.log_poses:
            PoseVis.add_logger_connection((extension_log_name, stream_name, "OUTPUT_EXTENSIONS"))
            logger.info(f" enabled pose data logging for stream {stream_index} with the following path: {extension_log_name}")

    def build(self) -> None:
        logger.info(" building graph")

        # Enable extensions
        for i in range(len(self.config.extensions)):
            ext: PoseVisExtension = self.config.extensions[i]
            logger.info(f" enabling extension: {ext.__class__.__name__}")
            ext.set_enabled(i)
        
        # Check if provided log path is a full directory or relative
        self.config.log_directory = absolute_path(self.config.log_directory)
        logger.info(f" logging directory is {self.config.log_directory}")

        self.register_nodes()

    def run(self) -> None:
        logger_config: lg.LoggerConfig
        if self.config.log_name:
            logger_config = lg.LoggerConfig(output_directory = self.config.log_directory, recording_name = self.config.log_name)
        else:
            logger_config = lg.LoggerConfig(output_directory = self.config.log_directory)

        logger.info(" running graph")
        graph = PoseVis()
        runner_options = lg.RunnerOptions(logger_config = logger_config)
        runner = lg.ParallelRunner(graph = graph, options = runner_options)
        runner.run()

    @abstractmethod
    def register_nodes(self) -> None:
        raise NotImplementedError
