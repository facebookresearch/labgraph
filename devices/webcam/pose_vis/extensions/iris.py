#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

from optparse import Option
from unittest import result
import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.face_mesh as FaceType
import mediapipe.python.solutions.face_detection as FaceDetectType
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
# mp_iris: IrisType = mp.solutions.iris



class IrisExtension(PoseVisExtension):
    face_mesh: Optional[FaceType.FaceMesh] #? change this maybe?
    face_detect: Optional[FaceDetectType.FaceDetection] 



    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument('--iris', help='enable irises detection extension', action='store_true', required=False)


    def check_enabled(self, args: Namespace) -> bool:
        return args.iris

    def setup(self) -> None:
        # self.face_detect = mp_face
        # self.face_mesh = mp_face
        pass


    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        #TODO --- ADD CODE ---
        
        pass



    def cleanup(self) -> None:
        pass