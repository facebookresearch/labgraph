#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import cv2
import numpy as np

from typing import List, Tuple
from dataclasses import dataclass, field
from pose_vis.streams.messages import StreamMetaData
from pose_vis.extension import PoseVisExtension

logger = logging.getLogger(__name__)

@dataclass
class FrameProcessor():
    """
    Handles extension execution

    Attributes:
        `stream_id`: `int` should be set when creating this object
        `extensions`: `List[PoseVisExtension]` the list of extensions to execute
    """
    stream_id: int = -1
    extensions: List[PoseVisExtension] = field(default_factory = list)

    def setup(self) -> None:
        for ext in self.extensions:
            logger.info(f" stream {self.stream_id}: setting up extension {ext.__class__.__name__}")
            ext.setup()

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, str]:
        ext_results = {}
        overlayed = frame.copy()
        for ext in self.extensions:
            overlay, ext_result = ext.process_frame(frame, metadata)
            # TODO: addWeighted() leads to a darker image overall, I'm guessing due to lack of transparency support
            # It is, however extremely fast, faster than other methods I've experimented with
            overlayed = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0.0)
            ext_results[ext.__class__.__name__] = ext_result.data
        return (overlayed, ext_results)

    def cleanup(self) -> None:
        for ext in self.extensions:
            ext.cleanup()