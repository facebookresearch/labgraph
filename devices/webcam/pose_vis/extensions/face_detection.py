import logging
import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.face_detection as FaceType
import mediapipe.python.solutions.objectron as ObjectType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList #? <--

from pose_vis.extension import PoseVisExtension, ExtensionResult
from argparse import ArgumentParser, Namespace

from typing import Optional, Tuple

logger = logging.getLogger(__name__)

mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_face: FaceType = mp.solutions.face_detection
mp_object: ObjectType = mp.solutions.objectron #! <--- for object tracking - testing

class FaceDetectionExtension(PoseVisExtension):
    face : Optional[FaceType.FaceDetection]
    object_tracking : Optional[ObjectType.Objectron] #! <---- object tracking - testing

    # argument to enable or disable the face detection extension
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument("--face_detection", help="enable the face detection extension", action="store_true", required=False)

    def check_enabled(self, args: Namespace) -> bool:
        return args.face_detection

    def setup(self) -> None:
        self.face = mp_face.FaceDetection()
        self.object_tracking = mp_object.Objectron()

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, ExtensionResult]:
        # convert from BGR to RGB
        #? NormalizedDetectionList
        mp_results = self.face.process(frame).detections 

        # check if a face detection list is null
        if mp_results is None:
            mp_results = []

        return ExtensionResult(data=mp_results)

    @classmethod
    def draw_overlay(cls, frame: np.ndarray, result: ExtensionResult):

        for detection in result.data:
            mp_drawing.draw_detection(
                frame,
                detection
            )

    @classmethod
    def check_output(cls, result: ExtensionResult)-> bool:
        if len(result.data) > 0:
            for i in range(result.data):
                if len(result.data[i]) != 6: 
                    logger.warning(f'index {i} in result.data is not proper length')
                    return False
            return True
        else:
            logger.warning(" result is empty")
        return False

    # clean up called when the graph is shutdown
    def cleanup(self) -> None:
        pass
