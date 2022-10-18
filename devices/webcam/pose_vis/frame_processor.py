#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import json
import numpy as np

from typing import List, Tuple
from dataclasses import dataclass, field
from pose_vis.video_stream import StreamMetaData
from pose_vis.extension import PoseVisExtension

@dataclass
class FrameProcessor():
    stream_id: int = -1
    extensions: List[PoseVisExtension] = field(default_factory = list)

    def setup(self) -> None:
        for ext in self.extensions:
            print(f"CameraStream.FrameProcessor: stream {self.stream_id}: setting up extension {ext.__class__.__name__}")
            ext.setup()

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, str]:
        ext_results = {}
        overlayed = frame.copy()
        for ext in self.extensions:
            overlay, ext_result = ext.process_frame(frame, metadata)
            overlayed = cv2.addWeighted(overlay, 0.5, overlayed, 0.5, 0.0)
            ext_results[ext.__class__.__name__] = ext_result.data
        return (overlayed, json.dumps(ext_results))

    def cleanup(self) -> None:
        for ext in self.extensions:
            ext.cleanup()