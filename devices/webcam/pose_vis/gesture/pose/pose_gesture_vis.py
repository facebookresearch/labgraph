#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

# Windows-specific performance tuning
import os
if os.name == "nt":
    # Improve sleep timer resolution for this process on Windows
    # https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod
    import ctypes
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)

    # Improve device capture startup time on Windows
    # https://github.com/opencv/opencv/issues/17687
    os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import time
import json
import logging
import cv2
import collections
import numpy as np
import argparse as ap
import math

from pathlib import Path
from enum import Enum
from typing import List, Tuple, Any, Deque
from dataclasses import dataclass
from google.protobuf.json_format import MessageToDict
from pose_vis.utils import parse_sources, parse_resolutions
from pose_vis.utils import absolute_path
from pose_vis.streams.utils.capture_handler import CaptureHandler, AllCapturesFinished
from pose_vis.display import DisplayHandler
# from pose_vis.extensions.hands import HandsExtension, HandsConfig, mp_hands
from pose_vis.extensions.pose import PoseExtension, PoseConfig ,mp_pose
from pose_vis.performance_utility import PerfUtility

logger = logging.getLogger(__name__)

LANDMARK_DISTANCE = [
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_WRIST ),
    # (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_ELBOW ),
    # (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP ),
    # (mp_pose.PoseLandmark.LEFT_ELBOW, mp_pose.PoseLandmark.LEFT_WRIST ),
    # ! Maybe add from wrist to thumb/index finger

    (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_WRIST),
    # (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_ELBOW),
    # (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP ),
    # (mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_WRIST ),



    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_ANKLE ),
    # (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE ),
    # (mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE ),
    # ! Maybe distance from ankle to toe

    (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_ANKLE )
    # (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE ),
    # (mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE )
]

LANDMARK_DIRECTION = [
    # todo --- ADD HERE ---
]

TORSO_DISTANCE = [
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP),
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
    (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP)
]

DRAW_DEBUG = False

MAX_DIFFERENCE_VALUE = 3 #! play around with this value


#! go over these
class GV_MODE(Enum):
    VISUALIZATION = 0,
    LABEL_INPUT = 1,
    COLLECTION = 2

#! revisit this class
@dataclass
class AnnotationInfo():
    pose_labels: List[str]
    pose_bounds: List[List[int]]
    gesture_data: List[np.ndarray]
    draw: bool

class PoseGestureVis():
    
    sources: List[str | int]
    resolutions: List[Tuple[int, int, int]]
    cap_handler: CaptureHandler
    dis_handler: DisplayHandler
    perf: PerfUtility
    annotation_infos: Deque[AnnotationInfo]
    data_dir: str
    export_files: List[str]
    export_format: str
    running: bool = True
    mode: GV_MODE = GV_MODE.VISUALIZATION
    label_name: str = ""
    label_names: List[str] = []
    label_data: List[np.ndarray] = []
    video_writers: List[cv2.VideoWriter]

    # ! Test this
    def __init__(self, sources: List[str | int], resolutions: List[Tuple[int, int, int]], data_dir: str, export_files: List[str], export_format: str) -> None:
        self.sources = sources
        self.resolutions = resolutions
        self.data_dir = data_dir
        self.export_files = export_files
        self.export_format = export_format
        self.video_writers = []
        for i in range(len(export_files)):
            self.video_writers.append(cv2.VideoWriter(self.export_files[i], cv2.VideoWriter_fourcc(*self.export_format), self.resolutions[i][2], (self.resolutions[i][0], self.resolutions[i][1])))
        self.load_data()

    def load_data(self):
        label_names = os.path.join(self.data_dir, "labels.json")

        if os.path.exists(label_names):
            with open(label_names, 'r') as _file:
                self.label_names = json.load(_file)

            np_files = [_file for _file in os.listdir(self.data_dir) if _file.endswith('.npy')]
            self.label_data = [np.empty(shape=(0, len(LANDMARK_DISTANCE) + (len(LANDMARK_DIRECTION) * 3)), dtype=np.float32)] * len(label_names) #! Go over this

            for _file in np_files:
                index = int(path(_file).stem)
                self.label_data[index] = np.load(os.path.join(self.data_sir, _file))


    def on_key(self, key: int):
        pass