#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from dataclasses import dataclass
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.runners.source_runner import SourceStreamRunner, SourceStreamRunnerConfig
from pose_vis.benchmark import Benchmark, BenchmarkConfig
from pose_vis.utils import absolute_path
from pose_vis.pose_vis_graph import PoseVis
from typing import List, Tuple, Union

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkRunnerConfig():
    """
    Config for BenchmarkRunner

    Attributes:
        `sources`: `List[Union[int, str]]`
        `resolutions`: `List[Tuple[int, int, int]]`
        `output_path`: `str`
        `output_name`: `str`
        `run_time`: `int`
    """
    sources: List[Union[int, str]]
    resolutions: List[Tuple[int, int, int]]
    output_path: str
    output_name: str
    run_time: int

class BenchmarkRunner(PoseVisRunner):
    """
    Runs the `Benchmark` node for gathering performance details
    """
    runner_config: BenchmarkRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: BenchmarkRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> None:
        self.runner_config.output_path = absolute_path(self.runner_config.output_path)
        logger.info(f" benchmark output path is {self.runner_config.output_path}")

        srunner = SourceStreamRunner(self.config, SourceStreamRunnerConfig(self.runner_config.sources, self.runner_config.resolutions))
        srunner.register_nodes()

        PoseVis.add_node("BENCHMARK", Benchmark, ["STREAM", "OUTPUT", "BENCHMARK", "INPUT"], BenchmarkConfig(
            self.runner_config.output_path,
            self.runner_config.output_name,
            self.runner_config.run_time))
        
        if self.config.display_framerate > 0:
            PoseVis.add_connection(["BENCHMARK", "OUTPUT_EXIT", "DISPLAY", "INPUT_EXIT_USER"])
        else:
            PoseVis.add_connection(["BENCHMARK", "OUTPUT_EXIT", "TERM_HANDLER", "INPUT_EXIT_USER"])