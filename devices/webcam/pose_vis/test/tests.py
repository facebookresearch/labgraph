#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import unittest
import logging
import labgraph as lg

from typing import List
from pose_vis.utils import absolute_path
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.streams.messages import CaptureResult
from pose_vis.runner import PoseVisConfig
from pose_vis.runners.source_runner import SourceStreamRunner, SourceStreamRunnerConfig
from pose_vis.extensions.hands import HandsExtension

logger = logging.getLogger(__name__)

class TestSubscriberConfig(lg.Config):
    enabled_extensions: List[PoseVisExtension]

class TestSubscriber(lg.Node):
    INPUT = lg.Topic(CaptureResult)
    config: TestSubscriberConfig

    @lg.subscriber(INPUT)
    def on_message(self, message: CaptureResult) -> None:
        for ext in self.config.enabled_extensions:
            ext_name = ext.__class__.__name__
            assert(ext.check_output(ExtensionResult(message.extensions[0][ext_name])))
            logger.info(f" {ext_name} reported data is OK")

class TestPoseVis(unittest.TestCase):
    def test_all(self):
        extensions = [HandsExtension()]

        config = PoseVisConfig(
            extensions=extensions,
            log_directory=absolute_path(f"webcam{os.sep}logs"),
            log_name=None,
            enable_logging=False,
            display_framerate=0,
            stats_history_size=0)
        
        runner_config = SourceStreamRunnerConfig(
            sources=[absolute_path(f"webcam{os.sep}images")],
            resolutions=[(3186, 5184, 30)])

        runner = SourceStreamRunner(config, runner_config)
        runner.build()

        PoseVis.add_node(name="TEST_SUBSCRIBER", _type=TestSubscriber, connection=["STREAM", "OUTPUT", "TEST_SUBSCRIBER", "INPUT"], config=TestSubscriberConfig(extensions))

        runner.run()

if __name__ == "__main__":
    unittest.main()