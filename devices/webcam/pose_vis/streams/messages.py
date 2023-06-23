#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import labgraph as lg
import numpy as np

from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class Capture():
    """
    Represents a single video frame

    Attributes:
        `frame`: `np.ndarray` video frame matrix, shape is (H, W, 3), RGB color space, short datatype
        `stream_id`: `int` source index for this capture
        `frame_index`: `int` total frames since startup
        `system_timestamp`: `float` `time.perf_counter()` value for when this frame was created
        `proc_delta_time`: `float` time in seconds this frame took to produce
        `proc_runtime`: `float` total runtime for this source
        `proc_fps`: `int` frames per second at the time this frame was produced
        `proc_target_fps`: `int` target frames per second for this source
    """
    frame: np.ndarray
    stream_id: int
    frame_index: int
    system_timestamp: float
    proc_delta_time: float
    proc_runtime: float
    proc_fps: int
    proc_target_fps: int

class CaptureResult(lg.Message):
    """
    Represents the current frame from every capture source

    Attributes:
        `captures`: `List[Capture]` `Capture`s by source index
        `extensions`: `List[Dict[str, Any]]` extension data by source index
    """
    captures: List[Capture]
    extensions: List[Dict[str, Any]]

class ExitSignal(lg.Message):
    """
    Passed to `Display` or `TerminationHandler` when a stream wants to close the graph
    """
    pass