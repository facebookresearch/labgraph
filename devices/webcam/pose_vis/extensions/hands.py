import cv2
import time
import labgraph as lg
import numpy as np
import mediapipe as mp
# Import MediaPipe types for intellisense
import mediapipe.python.solutions.hands as HandsType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType

# Every extension will probably need these imports
from pose_vis.extension import PoseVisExtension, PoseVisConfiguration, ExtensionResult, ResultData
from pose_vis.stream_combiner import CombinedVideoStream
from pose_vis.performance_tracking import PerfUtility
from argparse import ArgumentParser, Namespace

from typing import NamedTuple, Optional, Tuple

# MediaPipe setup: https://google.github.io/mediapipe/solutions/hands.html
mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_hands: HandsType = mp.solutions.hands

# Config for HandsVisualization node, can contain anything really but you will need an `extension_id` variable
# this is obtained from the PoseVisExtension setup class
class HandsVisualizationConfig(lg.Config):
    extension_id: int
    model_complexity: int
    min_detection_confidence: float
    min_tracking_confidence: float

# State for HandsVisualization node
class HandsVisualizationState(lg.State):
    hands: Optional[HandsType.Hands] = None

# The HandsVisualization node, runs the received frame through MediaPipe and outputs MediaPipe's data as well as the resulting
# image from MediaPipe's drawing utility
class HandsVisualization(lg.Node):
    # CombinedVideoStream has a `frames` list, where each index is a stream id, 0 - max number of stream sources
    INPUT = lg.Topic(CombinedVideoStream)
    # The node's output, all extensions should have this output message. See extension.py
    OUTPUT = lg.Topic(ExtensionResult)
    config: HandsVisualizationConfig
    state: HandsVisualizationState

    # Subscribe and publish in the same method, so it's 1 CombinedVideoStream in, 1 ExtensionResult out
    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def process_frames(self, message: CombinedVideoStream) -> lg.AsyncPublisher:
        # This is for profiling how long this method's execution takes
        start_time_ns = time.time_ns()

        # Find out how many stream sources we're working it
        num_frames = len(message.frames)
        # Create the output arrays based on num_frames
        result_frames = [None] * num_frames
        result_data = [None] * num_frames

        # Iterate each frame from CombinedVideoStream
        for i in range(num_frames):
            # Generate hand tracking data
            results: NamedTuple = self.state.hands.process(cv2.cvtColor(message.frames[i], cv2.COLOR_BGR2RGB))
            # NamedTuple will not serialize, so we put its data into a list
            landmarks = results.multi_hand_landmarks
            # Create a blank frame to draw on so we can overlay it when displaying
            result_frame = np.zeros(shape = message.frames[i].shape, dtype = np.uint8)
            # Ensure the message isn't empty if no hands are recognized
            if landmarks is None:
                landmarks = []
            else:
                # Draw the hand tracking data onto the blank image
                for landmark_list in landmarks:
                    mp_drawing.draw_landmarks(
                        result_frame,
                        landmark_list,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())
            # Add the results to the output arrays
            result_frames[i] = result_frame
            result_data[i] = ResultData(frame_index = message.metadatas[i].frame_index, data = landmarks)

        # Build an ExtensionResult and send the message
        yield self.OUTPUT, ExtensionResult(extension_id = self.config.extension_id,
            # This can be set to 0 but having timings is useful for performance tracking
            update_time_ms = PerfUtility.ns_to_ms(time.time_ns() - start_time_ns),
            result_frames = result_frames,
            result_data = result_data)

    def setup(self) -> None:
        # Setup for MediaPipe's Hands module: https://google.github.io/mediapipe/solutions/hands.html
        self.state.hands = mp_hands.Hands(
            model_complexity = self.config.model_complexity,
            min_detection_confidence = self.config.min_detection_confidence,
            min_tracking_confidence = self.config.min_tracking_confidence)

# This class is instantiated by Pose Vis automatically
# You must import this file in extensions/__init__.py for it to be recognized
class HandsExtension(PoseVisExtension):

    # Register an argument that allows the user to enable this extension
    def register_args(self, parser: ArgumentParser):
        parser.add_argument("--hands", help = "enable the hand tracking extension", action = "store_true", required = False)
    
    # Tell Pose Vis if this extension is enabled or not
    def check_enabled(self, args: Namespace) -> bool:
        return args.hands
    
    # Pose Vis will ask for some information and then handle the rest
    # The output is as follows Tuple[<node class object>, <node config object>, <node input topic>, <node output topic>]
    def configure_node(self, extension_id: int, config: PoseVisConfiguration) -> Tuple[type, lg.Config, lg.Topic, lg.Topic]:
        return (HandsVisualization,
            HandsVisualizationConfig(extension_id = extension_id, model_complexity = 0, min_detection_confidence = 0.5, min_tracking_confidence = 0.5),
            HandsVisualization.INPUT,
            HandsVisualization.OUTPUT)