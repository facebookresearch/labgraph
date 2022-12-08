#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import numpy as np
import mediapipe as mp

# Import MediaPipe types for intellisense
import mediapipe.python.solutions.hands as HandsType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, ExtensionResult
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_hands: HandsType = mp.solutions.hands

@dataclass
class HandsConfig():
    max_num_hands: int = 2
    model_complexity: int = 0
    min_detection_confidence: int = 0.5
    min_tracking_confidence: int = 0.5

# This class is instantiated by Pose Vis automatically
# You must import this file in extensions/__init__.py for it to be recognized
class HandsExtension(PoseVisExtension):
    # Optional here since this class will be serialized to each stream node
    # otherwise we'll get a "cannot pickle" AttributeError
    hands: Optional[HandsType.Hands]
    config: HandsConfig

    def __init__(self, config: HandsConfig = HandsConfig()) -> None:
        self.config = config
        super().__init__()

    # Register an argument that allows the user to enable this extension
    def register_args(self, parser: ArgumentParser):
        parser.add_argument("--hands", help = "enable the hand tracking extension", action = "store_true", required = False)
    
    # Tell Pose Vis if this extension is enabled or not
    def check_enabled(self, args: Namespace) -> bool:
        return args.hands
    
    # Called when the stream is initialized
    def setup(self) -> None:
        # TODO: a way to expose MediaPipe configs
        self.hands = mp_hands.Hands(
            max_num_hands = self.config.max_num_hands,
            model_complexity = self.config.model_complexity,
            min_detection_confidence = self.config.min_detection_confidence,
            min_tracking_confidence = self.config.min_tracking_confidence)

    # Called from `FrameProcessor` on each new frame from the stream
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, ExtensionResult]:
        mp_results = self.hands.process(frame)
        
        # Convert different results to a dict for easier access
        results = {"multi_hand_landmarks": [], "multi_hand_world_landmarks": [], "multi_handedness": []}
        if mp_results.multi_hand_landmarks is not None:
            results["multi_hand_landmarks"] = mp_results.multi_hand_landmarks
        if mp_results.multi_hand_world_landmarks is not None:
            results["multi_hand_world_landmarks"] = mp_results.multi_hand_world_landmarks
        if mp_results.multi_handedness is not None:
            results["multi_handedness"] = mp_results.multi_handedness
        
        return ExtensionResult(data = results)

    @classmethod
    def draw_overlay(cls, frame: np.ndarray, result: ExtensionResult) -> None:
        # Draw the detected hand landmarks onto the image
        for landmark_list in result.data["multi_hand_landmarks"]:
            mp_drawing.draw_landmarks(
                frame,
                landmark_list,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

    @classmethod
    def check_output(cls, result: ExtensionResult) -> bool:
        """
        Checks the results of `hands.process()`, assuming that at least one hand is fully visible in the frame
        """
        if "multi_hand_landmarks" in result.data:
            for i in range(len(result.data["multi_hand_landmarks"])):
                if len(result.data["multi_hand_landmarks"][i].landmark) != 21:
                    logger.warning(f" index {i} in result.data is not proper length")
                    return False
            return True
        else:
            logger.warning(" result is empty")
        return False

    # Called when the graph shuts down
    def cleanup(self) -> None:
        pass