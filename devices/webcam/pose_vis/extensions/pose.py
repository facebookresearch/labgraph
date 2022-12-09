#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import numpy as np
import mediapipe as mp

# Import MediaPipe types for intellisense
import mediapipe.python.solutions.pose as PoseType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_pose: PoseType = mp.solutions.pose

@dataclass
class PoseConfig():
    model_complexity: int = 1
    smooth_landmarks: bool = True
    enable_segmentation: bool = False
    smooth_segmentation: bool = True
    min_detection_confidence = 0.5
    min_tracking_confidence = 0.5

class PoseExtension(PoseVisExtension):
    pose: Optional[PoseType.Pose]
    config: PoseConfig

    def __init__(self, config: PoseConfig = PoseConfig()) -> None:
        self.config = config
        super().__init__()

    # register argument allowing user to run this extension
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument('--pose', help='enable pose estimation extension', action = 'store_true', required= False)

    # check to see if extension is enabled or not
    def check_enabled(self, args: Namespace) -> bool:
        return args.pose

    def setup(self) -> None:
        self.pose = mp_pose.Pose(
            model_complexity = self.config.model_complexity,
            smooth_landmarks = self.config.smooth_landmarks,
            enable_segmentation = self.config.enable_segmentation,
            smooth_segmentation = self.config.smooth_segmentation,
            min_detection_confidence = self.config.min_detection_confidence, 
            min_tracking_confidence = self.config.min_tracking_confidence
        )

    def process_frame(self, frame: np.ndarray) -> ExtensionResult:
        
        mp_result = self.pose.process(frame)

        results = {"pose_landmarks":[], "pose_world_landmarks":[]}

        if (mp_result.pose_landmarks is not None):
            results["pose_landmarks"] = mp_result.pose_landmarks
        elif(mp_result.pose_world_landmarks is not None):
            results["pose_world_landmarks"] = mp_result.pose_world_landmarks
        
        return ExtensionResult(data=results)


    @classmethod
    def draw_overlay(cls, frame: np.ndarray, result: ExtensionResult):

        # for pose_landmark_list in result.data["pose_landmarks"]:
        mp_drawing.draw_landmarks(
            frame, 
            result.data["pose_landmarks"],
            mp_pose.POSE_CONNECTIONS,
            mp_drawing_styles.get_default_pose_landmarks_style()
        )

    @classmethod
    def check_output(cls, result: ExtensionResult):
        if len(result.data) > 0:
            for i in range(result.data):
                if len(result.data[i]) != 33:
                    logger.warning(f' index {i} in result is not proper length')
                    return False
            return True
        else:
            logger.warning(' result is empty')
        return False

    def cleanup(self) -> None:
        pass