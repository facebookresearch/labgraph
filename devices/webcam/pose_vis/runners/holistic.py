#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.holistic as HolisticType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from argparse import ArgumentParser, Namespace

from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# medaiapipe setup
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_holistic: HolisticType = mp.solutions.holisitc

class HolisticExtension(PoseVisExtension):
    holistic: Optional[HolisticType.Holistic] #! <-- test this

    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument('--holistic', help='enable holistic extension', action='store_true', required=False)

    def check_enabled(self, args: Namespace) -> bool:
        return args.holistic
    
    def setup(self) -> None:
        self.holistic = mp_holistic.Holistic() #! <-- test

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, ExtensionResult]:
        
        result = self.holistic.process(frame)
        
        face_landmarks = result.face_landmarks
        pose_landmarks = result.pose_landmarks

        if face_landmarks is None:
            face_landmarks = []
        if pose_landmarks is None:
            pose_landmarks = []

        return ExtensionResult(data=result)

    @classmethod
    def draw_overlay(cls, frame:np.ndarray, result: ExtensionResult):

        # draw holistic
        #! test these two 
        mp_drawing.draw_landmarks(
            frame,
            result.face_landmarks,
            mp_holistic.FACEMESH_CONTOURS,
            None, #! <-- make sure this is correct 
            mp_drawing_styles.get_default_face_mesh_contours_style()
        )

        mp_drawing.draw_landmarks(
            frame, 
            result.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            mp_drawing_styles.get_default_pose_landmarks_style()
        )


    @classmethod
    def check_output(cls, result:ExtensionResult) -> bool:
        # recheck this function
        if len(result.data)>0:
            for i in range(result.data):
                if len(result.data[i] != 510): #! <-- this number might not be correct
                    logger.warning(f'index {i} in result.data is not proper length')
                    return False
            return True
        else:
            logger.warning('result is empty')
        return False

    def cleanup(self) -> None:
        pass