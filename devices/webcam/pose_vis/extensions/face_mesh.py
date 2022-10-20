#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.hands as HandsType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.streams.messages import StreamMetaData
from argparse import ArgumentParser, Namespace

from typing import Optional, Tuple

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_face_mesh: Facetype = mp.solutions.face_mesh #! make sure this is right

class FaceExtension(PoseVisExtension):
    face_mesh: Optional[FaceType.Face] #! <---------
    
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument("--face_mesh", help="enable face mesh extension", action="store_true", required=False)

    def check_enabled(self, args: Namespace) -> bool:
        return args.face_mesh

    def setup(self) -> None:
        self.face_mesh = mp_face_mesh.Face_mesh()

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        
        mp_results = self.face_mesh.proccess(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        mp_results = mp_results.multi_face_landmarks

        if mp_results is None:
            mp_results = []

        overlay = np.zeros(shape=frame.shape, dtype=np.uint8)

        for landmark_list in mp_results:
            mp_drawing.draw_landmarks(
                overlay, 
                landmark_list,
                mp_face_mesh.FACEMESH_TESSELATION,
                mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            mp_drawing.draw_landmarks(
                overlay, 
                landmark_list,
                mp_face_mesh.FACEMESH_CONTOURS,
                mp_drawing_styles.get_default_face_mesh_contours_style()
            )
        
        return (overlay, ExtensionResult(data=mp_results))

    def cleanup(self) -> None:
        pass