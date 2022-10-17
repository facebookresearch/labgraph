#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import labgraph as lg
import numpy as np

from dataclasses import dataclass

@dataclass
class StreamMetaData:
    """
    Utility dataclass for information of a particular stream input

    Attributes:
        `target_framerate`: `int`, the target framerate of this source
        `actual_franerare`: `int`, the actual framerate of this source
        `device_id`: `int`, the device identifier, e.g. `/dev/video{n} on Linux`. `-1` for non-device based streams
        `stream_id`: `int`, the contiguous index of this stream
    """
    target_framerate: int
    actual_framerate: int
    device_id: int
    stream_id: int

class ProcessedVideoFrame(lg.Message):
    """
    Each `np.ndarray` instance is a (H, W, 3) shaped array containing `np.uint8` datatype that represents an image
    Image formats are in the Blue Green Red color space

    Attributes:
        `original`: `np.ndarray` the original input frame
        `overlayed`: `np.ndarray` the original frame combined with overlays produced by each extension
        `frame_index`: `int`, frame counter since startup
        `metadata`: `StreamMetaData`
    """
    original: np.ndarray
    overlayed: np.ndarray
    frame_index: int
    metadata: StreamMetaData