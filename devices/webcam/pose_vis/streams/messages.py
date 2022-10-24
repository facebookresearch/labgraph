#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import labgraph as lg
import numpy as np

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StreamMetaData:
    """
    Utility dataclass for information of a particular stream input

    Attributes:
        `actual_franerate`: `int`, the actual framerate of this source
        `device_id`: `int`, the device identifier, e.g. `/dev/video{n} on Linux`. `-1` for non-device based streams
        `stream_id`: `int`, the contiguous index of this stream
    """
    actual_framerate: int
    device_id: int
    stream_id: int

class VideoFrame(lg.Message):
    """
    Attributes:
        `frame`: `np.ndarray` flat (W * H * 3) shaped array containing `np.uint8` datatype that represents an image, BGR color space
        `timestamp`: `float` OS time of capture
        `resolution`: `np.ndarray` the resolution of the images (W, H, framerate)
        `frame_index`: `int`, frame counter since startup
        `metadata`: `StreamMetaData`
    """
    frame: np.ndarray
    timestamp: float
    resolution: np.ndarray
    frame_index: int
    metadata: StreamMetaData

class ExtensionResults(lg.Message):
    """
    All extension results combined into a dictionary
    
    Attributes:
    `results`: `Dict[str, Any]`
    `timestamp`: `float` OS time of completing processing
    `frame_index`: `int`, frame counter since startup
    `metadata`: `StreamMetaData`
    """
    results: Dict[str, Any]
    timestamp: float
    frame_index: int
    metadata: StreamMetaData

class GraphMetaData(lg.Message):
    """
    Utility message for log playback

    Attributes:
        `num_streams`: `int`
    """
    num_streams: int

class FinishedMessage(lg.Message):
    """
    Message for nodes to produce when they've finished processing

    Picked up by the `TerminationHandler` node for graph shutdown when not using the `Display` node
    """
    stream_id: int