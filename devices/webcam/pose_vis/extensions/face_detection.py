import cv2
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.face_detection as FaceType
import mediapipe.python.solutions.objectron as ObjectType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.streams.messages import StreamMetaData
from argparse import ArgumentParser, Namespace

from typing import Optional, Tuple

mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_face: FaceType = mp.solutions.face_detection
mp_object: ObjectType = mp.solutions.objectron #! <--- for object tracking - testing

class FaceExtension(PoseVisExtension):
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

    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        # convert from BGR to RGB
        #? NormalizedDetectionList
        mp_results = self.face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).detections # make sure this is right
        mp_obj_results = self.object_tracking.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).detected_objects #! <- object tracking - testing 


        # print(f'mp_object is {mp_obj_results}')

        # detections = mp_results.detections # a list of the detected face location data

        # check if a face detection list is null
        if mp_results is None:
            mp_results = []

        if mp_obj_results in None:
            mp_obj_results = []

        # blank image for creating the overlay on
        overlay = np.zeros(shape=frame.shape, dtype=np.uint8)

        for detection in mp_results:
            mp_drawing.draw_detection(
                overlay,
                detection
            )
        
        #! ERROR here - cant iterate nonetype
        # for detected_objects in mp_obj_results:
        #     mp_drawing.draw_landmarks(
        #         overlay,
        #         detected_objects.landmarks_2d,
        #         mp_object.BOX_CONNECTIONS                
        #     )

        #todo implement box tracking 
        



        return (overlay, ExtensionResult(data=mp_results)) 

    @classmethod
    def check_output(cls, result: ExtensionResult)-> bool:
        return False

    # clean up called when the graph is shutdown
    def cleanup(self) -> None:
        pass
