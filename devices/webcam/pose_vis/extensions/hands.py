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
from pose_vis.video_stream import StreamMetaData
from argparse import ArgumentParser, Namespace

from typing import Optional, Tuple

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_hands: HandsType = mp.solutions.hands

# This class is instantiated by Pose Vis automatically
# You must import this file in extensions/__init__.py for it to be recognized
class HandsExtension(PoseVisExtension):
    # Optional here since this class will be serialized to each stream node
    # otherwise we'll get a "cannot pickle" AttributeError
    hands: Optional[HandsType.Hands]

    # Register an argument that allows the user to enable this extension
    def register_args(self, parser: ArgumentParser):
        parser.add_argument("--hands", help = "enable the hand tracking extension", action = "store_true", required = False)
    
    # Tell Pose Vis if this extension is enabled or not
    def check_enabled(self, args: Namespace) -> bool:
        return args.hands
    
    # Called when the stream is initialized
    def setup(self) -> None:
        self.hands = mp_hands.Hands()

    # Called from `FrameProcessor` on each new frame from the stream
    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        # MediaPipe likes RGB images, not BGR
        # Convert and grab the results we're looking for
        mp_results: NormalizedLandmarkList = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).multi_hand_landmarks
        # `multi_hand_landmarks` can be null, so if it is make sure we're working on an empty list
        if mp_results is None:
            mp_results = []
        
        # I can't find documentation on NormalizedLandmarkList
        # We convert this to a normal Python list below

        # Create a blank image for drawing as it'll be overlayed onto the video stream
        overlay = np.zeros(shape = frame.shape, dtype = np.uint8)

        # Draw the detected hand landmarks onto the overlay image
        for landmark_list in mp_results:
            mp_drawing.draw_landmarks(
                overlay,
                landmark_list,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
        
        # Convert MediaPipe's results into a list so it's easier to work with down the line
        result_length = len(mp_results)
        results = [None] * result_length
        for i in range(result_length):
            landmark_list = mp_results[i].landmark
            landmarks = [None] * len(landmark_list)
            for id, landmark in enumerate(landmark_list):
                landmarks[id] = [landmark.x, landmark.y, landmark.z]
            results[i] = landmarks

        # Return the overlay for presentation, along with any data to be picked up by the logger
        return (overlay, ExtensionResult(data = results))

    # Called when the graph shuts down
    def cleanup(self) -> None:
        pass