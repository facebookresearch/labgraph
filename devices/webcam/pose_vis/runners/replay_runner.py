#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from pose_vis.utils import absolute_path
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.streams.replay_stream import ReplayStream, ReplayStreamConfig
from pose_vis.pose_vis_graph import PoseVis
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ReplayStreamRunnerConfig():
    """
    Config for ReplayStreamRunner

    Attributes:
        `path`: `str`
    """
    path: str

class ReplayStreamRunner(PoseVisRunner):
    """
    Runs the `ReplayStream` node to replay log files
    """
    runner_config: ReplayStreamRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: ReplayStreamRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> None:
        self.runner_config.path = absolute_path(self.runner_config.path)

        PoseVis.add_node("STREAM", ReplayStream, config = ReplayStreamConfig(
            self.config.extensions,
            self.runner_config.path))