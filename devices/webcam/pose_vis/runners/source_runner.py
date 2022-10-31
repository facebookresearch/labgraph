#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from dataclasses import dataclass
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.streams.source_stream import SourceStream, SourceStreamConfig
from pose_vis.pose_vis_graph import PoseVis
from typing import List, Tuple, Union

logger = logging.getLogger(__name__)

@dataclass
class SourceStreamRunnerConfig():
    """
    Config for SourceStreamRunner

    Attributes:
        `sources`: `List[Union[int, str]]`
        `resolutions`: `List[Tuple[int, int, int]]`
    """
    sources: List[Union[int, str]]
    resolutions: List[Tuple[int, int, int]]

class SourceStreamRunner(PoseVisRunner):
    """
    Runs the `SourceStream` node to capture video sources
    """
    runner_config: SourceStreamRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: SourceStreamRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> int:
        # Sort by framerate to select lowest value
        # The stream shouldn't run faster than the slowest source
        _sorted = sorted(self.runner_config.resolutions, key = lambda r: r[2])
        PoseVis.add_node("STREAM", SourceStream, config = SourceStreamConfig(
            self.runner_config.sources,
            self.runner_config.resolutions,
            self.config.extensions,
            _sorted[0][2]))

        