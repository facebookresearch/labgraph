from distutils import extension
from unittest import result
import cv2
import time
import labgraph as lg
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.face_detection as FaceType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType
from labgraph.graphs.method import AsyncPublisher, publisher
from labgraph.messages import message

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, PoseVisConfiguration, ExtensionResult, ResultData
from pose_vis.stream_combiner import CombinedVideoStream
from pose_vis.performance_tracking import PerfUtility
from argparse import ArgumentParser, Namespace

from typing import NamedTuple, Optional, Tuple


mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
# mp_hands: HandsType = mp.solutions.hands
mp_face: FaceType = mp.solutions.face  

class FaceExtension(PoseVisExtension):
    face : Optional[FaceType.FaceDetection]

    # argument to enable or disable the face detection extention
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument("--face", help="enable the face detection extention", action="store_true", required=False)

    #? ake sure this is correct
    def check_enabled(self, args: Namespace) -> bool:
        return args.face 

    def setup(self) -> None:
        self.face = mp_face.FaceDetection()

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        # convert from BGR to RGB
        results: NamedTuple = self.face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        landmarks = results.multi_face_landmarks #? not sure if this is correct

        if landmarks is None:
            landmarks = []

        
