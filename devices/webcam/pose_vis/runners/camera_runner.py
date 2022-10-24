#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging

from dataclasses import dataclass
from pose_vis.runner import PoseVisRunner, PoseVisConfig
from pose_vis.streams.camera_stream import CameraStream, CameraStreamConfig
from pose_vis.display import Display, DisplayConfig
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.extension import PoseVisExtension
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

@dataclass
class CameraStreamRunnerConfig():
    """
    Config for CameraStreamRunner

    Attributes:
        `device_ids`: `List[int]`
        `device_resolutions`: `Dict[int, Tuple[int, int, int]]`
        `display_framerate`: `int`
    """
    device_ids: List[int]
    device_resolutions: Dict[int, Tuple[int, int, int]]
    display_framerate: int

class CameraStreamRunner(PoseVisRunner):
    runner_config: CameraStreamRunnerConfig

    def __init__(self, config: PoseVisConfig, runner_config: CameraStreamRunnerConfig) -> None:
        self.runner_config = runner_config
        super().__init__(config)
    
    def register_nodes(self) -> None:
        num_devices = len(self.runner_config.device_ids)
        logger.info(f" creating {num_devices} CameraStream(s) with device ids {self.runner_config.device_ids} and resolutions {self.runner_config.device_resolutions}")

        for i in range(num_devices):
            stream_name = f"STREAM{i}"
            input_frames_name = f"INPUT_FRAMES{i}"
            input_exts_name = f"INPUT_EXTS{i}"

            device_id = self.runner_config.device_ids[i]
            device_resolution = self.runner_config.device_resolutions[device_id] if device_id in self.runner_config.device_resolutions else self.runner_config.device_resolutions[-1]
            PoseVis.add_node(stream_name, CameraStream, [stream_name, "OUTPUT_FRAMES", "DISPLAY", input_frames_name],
                CameraStreamConfig(stream_id = i,
                device_id = device_id,
                device_resolution = device_resolution,
                extensions = self.config.extensions))
            PoseVis.add_connection(["DISPLAY", input_exts_name, stream_name, "OUTPUT_EXTENSIONS"])
            self.set_logger_connections(i)

            logger.info(f" created CameraStream {i} with device id {device_id} and resolution {device_resolution}")
        
        self.add_graph_metadata(num_devices)

        ext_types = {}
        for cls in PoseVisExtension.__subclasses__():
            ext_types[cls.__name__] = cls
        PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(target_framerate = self.runner_config.display_framerate, num_streams = num_devices, extension_types = ext_types))