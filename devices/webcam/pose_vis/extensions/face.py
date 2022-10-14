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
from pose_vis.extension import PoseVisExtension, PoseVisConfiguration, ExtensionResult, ResultData
from pose_vis.stream_combiner import CombinedVideoStream
from pose_vis.performance_tracking import PerfUtility
from argparse import ArgumentParser, Namespace

from typing import NamedTuple, Optional, Tuple
