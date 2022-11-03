#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
from optparse import Option
from unittest import result
import cv2
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

from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_pose: PoseType = mp.solutions.pose

class PoseExtension(PoseVisExtension):
    pose: Optional[PoseType.Pose]

    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument('--pose', help='enable pose estimation extension', action = 'store_true', required= False)

    def check_enabled(self, args: Namespace) -> bool:
        return args.pose

    def setup(self) -> None:
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def process_frame(self, frame: np.ndarray) -> ExtensionResult:
        
        result = self.pose.process(frame)

        results = {"pose_landmarks": []}

        if result.pose_landmarks is not None:
            results["pose_landmarks"] = result.pose_landmarks
        
        return ExtensionResult(data=results)


    @classmethod
    def draw_overlay(cls, frame: np.ndarray, result: ExtensionResult):

        for pose_landmark_list in result.data["pose_landmarks"]:
            mp_drawing.draw_landmarks(
                frame, 
                pose_landmark_list,
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