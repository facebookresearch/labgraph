from distutils import extension
from locale import normalize
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

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.video_stream import StreamMetaData
from argparse import ArgumentParser, Namespace

from typing import NamedTuple, Optional, Tuple


mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
# mp_hands: HandsType = mp.solutions.hands
mp_face: FaceType = mp.solutions.face_detection

class FaceExtension(PoseVisExtension):
    face : Optional[FaceType.FaceDetection]

    # argument to enable or disable the face detection extention
    def register_args(self, parser: ArgumentParser) -> None:
        parser.add_argument("--face", help="enable the face detection extention", action="store_true", required=False)

    #? make sure this is correct
    def check_enabled(self, args: Namespace) -> bool:
        return args.face 

    def setup(self) -> None:
        self.face = mp_face.FaceDetection()

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        # convert from BGR to RGB
        mp_results: NormalizedDetectionList = self.face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).detections # make sure this is right

        # detections = mp_results.detections # a list of the detected face location data

        # check if a face is null
        if mp_results is None:
            mp_results = []

        # blank image
        overlay = np.zeros(shape=frame.shape, dtype=np.uint8)

        for detection in mp_results:
            mp_drawing.draw_detection(
                overlay,
                detection,  
                #! these two below might not be the correct styles 
                #? switch order maybe?
                mp_drawing_styles.get_default_face_mesh_contours_style(), 
                mp_drawing_styles.get_default_face_mesh_tesselation_style(),
            )
        
        results = mp_results

        # result_len = len(mp_results)
        # results = [None] * result_len

        # for i in range(result_len):
        #     detection_list = mp_results[i].detection #! maybe wrong
        #     detections = [None]*len(detection_list)

        #     for id in enumerate(detection_list):
        #         detections[id] = [detection.x, detection.y, detection.z]
        #     result[i] = detections


        return (overlay, ExtensionResult(data=results)) 


    # clean up
    def cleanup(self) -> None:
        #? maybe add something
        pass
