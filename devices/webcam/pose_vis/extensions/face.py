from distutils import extension
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

# config class for the face detection node
class FaceDetectionConfig(lg.Config):
    extension_id: int
    #? maybe not needed
    model_complexity: int
    min_detection_confidence: float
    min_tracking_confidence: float

# state class for the face detection node
class FaceDetectionState(lg.State):
    face: Optional[FaceType.FaceDetection] = None

# face detection node
class FaceDetection(lg.Node):
    INPUT = lg.Topic(CombinedVideoStream)
    OUTPUT = lg.Topic(ExtensionResult)
    config : FaceDetectionConfig
    state : FaceDetectionState


    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT
    async def process_frames(self, message:CombinedVideoStream) -> lg.AsyncPublisher:
        pass