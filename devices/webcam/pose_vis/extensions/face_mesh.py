#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.face_mesh as FaceType
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
mp_face_mesh: FaceType = mp.solutions.face_mesh 

class FaceMeshExtension(PoseVisExtension):
    face_mesh: Optional[FaceType.FaceMesh] 
    
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument("--face_mesh", help="enable face mesh extension", action="store_true", required=False)

    def check_enabled(self, args: Namespace) -> bool:
        return args.face_mesh

    def setup(self) -> None:
        self.face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, ExtensionResult]:
        
        mp_results = self.face_mesh.process(frame).multi_face_landmarks

        if mp_results is None:
            mp_results = []

        return ExtensionResult(data=mp_results)

    @classmethod
    def draw_overlay(cls, frame: np.ndarray, result: ExtensionResult):

        for landmark_list in result.data:
            mp_drawing.draw_landmarks(
                frame, 
                landmark_list,
                mp_face_mesh.FACEMESH_TESSELATION,
                None,
                mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            mp_drawing.draw_landmarks(
                frame, 
                landmark_list,
                mp_face_mesh.FACEMESH_IRISES,
                None,
                mp_drawing_styles.get_default_face_mesh_contours_style()
            )
            mp_drawing.draw_landmarks(
                frame, 
                landmark_list,
                None,
                mp_face_mesh.FACEMESH_CONTOURS,
                mp_drawing_styles.get_default_face_mesh_iris_connections_style()
            )


    @classmethod
    def check_output(cls, result:ExtensionResult) -> bool:
        # check the result of 'face_mesh.process' 
        if len(result.data) > 0:
            for i in range(result.data):
                if len(result.data[i]) != 468:  
                    logger.warning(f"index {i} in result.data is not proper length")
                    return False
            return True
        else:
            logger.warning("result is empty")
        return False


    def cleanup(self) -> None:
        pass