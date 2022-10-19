#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass
from enum import Enum
from typing import List, DefaultDict, Optional, Tuple, Any

class PoseVisMode(Enum):
    """
    Defines which mode `PoseVisRunner` starts under

    `DEVICE_STREAMING` uses the `CameraStream` node and requires `device_ids`, `device_resolutions`, and `display_framerate` to be set in `PoseVisConfiguration`

    `IMAGE_STREAMING` uses the `ImageStream` node and requires `image_streaming_directory` to be set in `PoseVisConfiguration`
    """
    DEVICE_STREAMING = 0,
    IMAGE_STREAMING = 1,
    LOG_REPLAY = 2

@dataclass
class PoseVisConfiguration():
    """
    PoseVisRunner configuration

    Attributes:
        `mode`: `PoseVisMode` required
        `enabled_extensions`: `List[Any]` expected to be a list of PoseVisExtension objects
        `device_ids`: `List[int]` required if using `PoseVisMode.DEVICE_STREAMING`
        `device_resolutions`: `DefaultDict[int, Tuple[int, int, int]]` required if using `PoseVisMode.DEVICE_STREAMING`
        `display_framerate`: `int` required if using `PoseVisMode.DEVICE_STREAMING`
        `image_streaming_directory`: `str` required if using `PoseVisMode.IMAGE_STREAMING`
        `image_streaming_framerate`: `int` required if using `PoseVisMode.IMAGE_STREAMING`
        `log_directory`: `str` required, can be relative from pose_vis directory or a full path
        `log_name`: `Optional[str]` not required
        `log_images`: `bool` required
        `log_poses`: `bool` required
    """
    mode: PoseVisMode
    enabled_extensions: List[Any]
    device_ids: List[int]
    device_resolutions: DefaultDict[int, Tuple[int, int, int]]
    display_framerate: int
    image_streaming_directory: str
    image_streaming_framerate: int
    log_directory: str
    log_name: Optional[str]
    log_images: bool
    log_poses: bool