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
mp_iris: IrisType = mp.solutions.iris