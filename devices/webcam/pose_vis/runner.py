#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import labgraph as lg

from pose_vis.utils import absolute_path
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.extension import PoseVisExtension
from pose_vis.display import Display, DisplayConfig
from pose_vis.termination_handler import TerminationHandler
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class PoseVisConfig():
    """
    Config for `PoseVisRunner` parent class

    Attributes:
        `extensions`: `List[PoseVisExtension]`
        `log_directory`: `str`
        `log_name`: `Optional[str]`
        `enable_logging`: `bool`
        `display_framerate`: `int`
    """
    extensions: List[PoseVisExtension]
    log_directory: str
    log_name: Optional[str]
    enable_logging: bool
    display_framerate: int
    stats_history_size: int

class PoseVisRunner(ABC):
    """
    Parent runner class that takes care of basic graph setup
    """
    config: PoseVisConfig

    def __init__(self, config: PoseVisConfig) -> None:
        self.config = config

    def build(self) -> None:
        """
        Build the `PoseVis` graph
        """
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

        if self.config.display_framerate > 0:
            ext_types = {}
            for cls in PoseVisExtension.__subclasses__():
                ext_types[cls.__name__] = cls
            PoseVis.add_node("DISPLAY", Display, ["STREAM", "OUTPUT", "DISPLAY", "INPUT"], DisplayConfig(
                target_framerate = self.config.display_framerate,
                stats_history_size = self.config.stats_history_size,
                extension_types = ext_types))
            PoseVis.add_connection(["STREAM", "OUTPUT_EXIT", "DISPLAY", "INPUT_EXIT_STREAM"])
        else:
            PoseVis.add_node("TERM_HANDLER", TerminationHandler)
            PoseVis.add_connection(["STREAM", "OUTPUT_EXIT", "TERM_HANDLER", "INPUT_EXIT_STREAM"])
        
        if self.config.enable_logging:
            PoseVis.add_logger_connection(("captures", "STREAM", "OUTPUT"))

    def run(self) -> None:
        """
        Run the `PoseVis` graph
        """
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
        """
        Function called for derived classes to add their specific nodes
        """
        raise NotImplementedError
