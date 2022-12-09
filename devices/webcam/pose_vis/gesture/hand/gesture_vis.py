#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

# Windows-specific performance tuning
import os
if os.name == "nt":
    # Improve sleep timer resolution for this process on Windows
    # https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod
    import ctypes
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)

    # Improve device capture startup time on Windows
    # https://github.com/opencv/opencv/issues/17687
    os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import time
import logging
import cv2
import collections
import numpy as np
import argparse as ap

from enum import Enum
from typing import List, Tuple, Any
from google.protobuf.json_format import MessageToDict
from pose_vis.utils import parse_sources, parse_resolutions
from pose_vis.utils import absolute_path
from pose_vis.streams.utils.capture_handler import CaptureHandler, AllCapturesFinished
from pose_vis.display import DisplayHandler
from pose_vis.extensions.hands import HandsExtension, HandsConfig
from pose_vis.performance_utility import PerfUtility
from pose_vis.gesture.hand.annotation import Annotation, Vector

logger = logging.getLogger(__name__)

# The maximum difference value to check for when looking for a known pose
MAX_DIFFERENCE_VALUE = 450

class GV_MODE(Enum):
    VISUALIZATION = 0,
    LABEL_INPUT = 1,
    COLLECTION = 2

class GestureVis():
    """
    Runs hand tracking and gesture recognition for provided sources
    """
    sources: List[str | int]
    resolutions: List[Tuple[int, int, int]]
    cap_handler: CaptureHandler
    dis_handler: DisplayHandler
    perf: PerfUtility
    annotation: Annotation
    data_dir: str
    export_files: List[str]
    export_format: str
    running: bool = True
    mode: GV_MODE = GV_MODE.VISUALIZATION
    hand_labels: List[str]
    hand_bounds: List[List[int]]
    label_name: str = ""
    label_names: List[str] = []
    video_writers: List[cv2.VideoWriter]

    def __init__(self, sources: List[str | int], resolutions: List[Tuple[int, int, int]], data_dir: str, export_files: List[str], export_format: str) -> None:
        self.sources = sources
        self.resolutions = resolutions
        self.data_dir = data_dir
        self.annotation = Annotation()
        self.export_files = export_files
        self.export_format = export_format
        self.video_writers = []
        for i in range(len(export_files)):
            self.video_writers.append(cv2.VideoWriter(self.export_files[i], cv2.VideoWriter_fourcc(*self.export_format), self.resolutions[i][2], (self.resolutions[i][0], self.resolutions[i][1])))
        self.annotation.load_gestures(os.path.join(self.data_dir, "gestures.json"))
    
    def on_key(self, key: int) -> None:
        """
        Input handling, connected to `DisplayHandler->register_key_callback`

        Switches states based on `GV_MODE`
        """
        if self.mode == GV_MODE.VISUALIZATION and key == 13:
            self.mode = GV_MODE.LABEL_INPUT
        elif self.mode == GV_MODE.LABEL_INPUT:
            if key == 27:
                self.mode = GV_MODE.VISUALIZATION
                self.label_name = ""
            elif key == 8:
                self.label_name = self.label_name[:-1]
            elif key == 13:
                if len(self.label_name) == 0:
                    logger.warning(" label is empty")
                else:
                    if self.label_name not in self.label_names:
                        self.label_names.append(self.label_name)
                    self.mode = GV_MODE.COLLECTION
            else:
                character = chr(key)
                self.label_name += character
        elif self.mode == GV_MODE.COLLECTION:
            if key == 27:
                self.mode = GV_MODE.VISUALIZATION
                self.label_name = ""
            elif key == 32:
                for hdx in range(len(self.annotation.hands)):
                    self.annotation.add_gesture_data(self.annotation.hands[hdx], self.label_name)
                self.annotation.save_gestures(os.path.join(self.data_dir, "gestures.json"))
        elif key == 27:
            self.running = False

    def get_handedness_labels(self, mp_handedness: Any) -> List[str]:
        """
        Puts MediaPipe "handedness" labels into a simple list
        https://google.github.io/mediapipe/solutions/hands.html#multi_handedness
        """
        hand_labels: List[str] = [None] * len(mp_handedness)
        for label_index, classification in enumerate(mp_handedness):
            _dict = MessageToDict(classification)["classification"][0]
            hand_labels[label_index] = _dict["label"]
        return hand_labels

    def get_bounds_data(self, mp_screen_keypoints: Any, mp_world_keypoints: Any, frame: np.ndarray) -> Tuple[List[List[int]], List[np.ndarray]]:
        """
        Gets the screen bounds and vertices for each hand
        """
        im_width, im_height = frame.shape[1], frame.shape[0]
        num_hands = len(mp_screen_keypoints)
        hand_bounds: List[List[int]] = [None] * num_hands
        hand_vectors: List[np.ndarray] = []
        for hand_index, landmark_list_screen in enumerate(mp_screen_keypoints):
            landmark_list_screen = landmark_list_screen.landmark
            landmark_list_world = mp_world_keypoints[hand_index].landmark

            bounds_array = np.empty((0, 2), int)
            for landmark in landmark_list_screen:
                lx = landmark.x
                ly = landmark.y
                
                bx = min(int(lx * im_width), im_width - 1)
                by = min(int(ly * im_height), im_height - 1)
                point = [np.array((bx, by))]
                bounds_array = np.append(bounds_array, point, axis = 0)
            
            hand_vector = np.empty(Vector.shape)
            for landmark in landmark_list_world:
                # We're multiplying by 1000 here to convert meters into milimeters
                hand_vector = np.append(hand_vector, [[round(landmark.x * 1000.0, 2), round(landmark.y * 1000.0, 2), round(landmark.z * 1000.0, 2)]], axis=0)
            hand_vectors.append(hand_vector)

            x, y, w, h = cv2.boundingRect(bounds_array)
            hand_bounds[hand_index] = [x, y, x + w, y + h]
        return (hand_bounds, hand_vectors)

    def draw_hand_annotations(self, source_index: int, frame: np.ndarray) -> None:
        """
        Draws the pose annotation label with the lowest `difference` value
        """
        if self.mode != GV_MODE.VISUALIZATION:
            return
        
        annotations = self.annotation.guess_annotations(MAX_DIFFERENCE_VALUE)
        for hdx, ann in enumerate(annotations):
            label = "?" if len(ann[0]) == 0 else ann[0]
            bounds = self.hand_bounds[hdx]
            annotation_str = f"{self.hand_labels[hdx]}: {label} ({ann[1]:.2f})"
            text_size = cv2.getTextSize(annotation_str, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (bounds[0], bounds[1]), (bounds[0] + text_size[0][0] + 2, bounds[1] - text_size[0][1] - 2), (0, 0, 0), -1)
            cv2.putText(frame, annotation_str, (bounds[0] + 1, bounds[1] - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        if len(self.video_writers) > 0:
            self.video_writers[source_index].write(frame)

    def run(self) -> None:
        """
        Run GestureVis
        """
        # MediaPipe Hands parameters can be found here
        # https://google.github.io/mediapipe/solutions/hands.html#static_image_mode
        hands_config = HandsConfig(model_complexity = 1)

        self.cap_handler = CaptureHandler(self.sources, self.resolutions, [HandsExtension(hands_config)])
        self.dis_handler = DisplayHandler(50, {"HandsExtension": HandsExtension})
        self.perf = PerfUtility()

        self.dis_handler.register_key_callback(self.on_key)
        self.dis_handler.register_post_render_callback(self.draw_hand_annotations)
        self.cap_handler.start_workers()
        num_sources = len(self.sources)
        self.annotation_infos = collections.deque(maxlen = num_sources)

        while self.running:
            self.perf.update_start()

            results = None
            try:
                results = self.cap_handler.get_captures()
            except AllCapturesFinished:
                self.running = False
                logger.info(" capture sources have finished playing, exiting")
                continue
            captures = [results[i][0] for i in range(num_sources)]
            extensions = [results[i][1] for i in range(num_sources)]

            for i in range(num_sources):
                mp_screen_keypoints = extensions[i]["HandsExtension"]["multi_hand_landmarks"]
                mp_world_keypoints = extensions[i]["HandsExtension"]["multi_hand_world_landmarks"]
                mp_handedness = extensions[i]["HandsExtension"]["multi_handedness"]
                
                self.hand_labels = self.get_handedness_labels(mp_handedness)
                capture = captures[i]
                hand_bounds, hand_vectors = self.get_bounds_data(mp_screen_keypoints, mp_world_keypoints, capture.frame)
                self.hand_bounds = hand_bounds
                self.annotation.clear_hand_vertices()
                for vdx, vec in enumerate(hand_vectors):
                    self.annotation.set_hand_vertices(vdx, vec)

                if self.mode == GV_MODE.LABEL_INPUT:
                    cv2.putText(capture.frame, "Define or select label: press <esc> to exit", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(capture.frame, f"Specify label name: {self.label_name}_", (10, 24 + (18 * 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(capture.frame, f"Defined labels: {self.label_names}", (10, 24 + (18 * 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(capture.frame, "Press <Enter> to confirm", (10, 24 + (18 * 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                elif self.mode == GV_MODE.COLLECTION:
                    cv2.putText(capture.frame, "Collect data points: press <esc> to exit", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    label_index = self.label_names.index(self.label_name)
                    cv2.putText(capture.frame, f"Label: {self.label_name}, index: {label_index}", (10, 24 + (18 * 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    num_points = len(self.annotation.gestures[self.label_name]) if self.label_name in self.annotation.gestures else 0
                    cv2.putText(capture.frame, f"Data points: {num_points}", (10, 24 + (18 * 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(capture.frame, "Press <space> to collect data point", (10, 24 + (18 * 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1, cv2.LINE_AA)
     
            self.dis_handler.update_frames(captures, extensions)
            self.dis_handler.update_windows(0)

            time.sleep(self.perf.get_remaining_sleep_time(self.resolutions[0][2]))
            self.perf.update_end()
        self.cleanup()

    def cleanup(self) -> None:
        self.cap_handler.cleanup()
        self.dis_handler.cleanup()
        for writer in self.video_writers:
            writer.release()

parser = ap.ArgumentParser()
parser.add_argument("--sources", type = str, nargs = "*", help = "which sources to stream (url, device id, video, or image directory)", action = "store", required = False)
parser.add_argument("--resolutions", type = str, nargs = "*", help = "specify resolution/framerate per stream; format is <stream index or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)", action = "store", required = False)
default_dir = f"webcam{os.sep}pose_vis{os.sep}gesture{os.sep}hand{os.sep}data"
parser.add_argument("--data-dir", type = str, nargs = "?", const = default_dir, default = default_dir, help = f"set data directory (default: {default_dir})", action = "store", required = False)
parser.add_argument("--export", type = str, nargs = "*", help = "export annotated stream as video file", action = "store", required = False)
parser.add_argument("--export-format", type = str, nargs = "?", const = "MP4V", default = "MP4V", help = "format to write exported video in (default: H264)", action = "store", required = False)

if __name__ == "__main__":
    args = parser.parse_args()

    sources = parse_sources(args.sources)
    resolutions = parse_resolutions(len(sources), args.resolutions if args.resolutions is not None else [])
    export_files = []
    if args.export is not None:
        for _file in args.export:
            export_files.append(absolute_path(_file))
    GestureVis(sources, resolutions, absolute_path(args.data_dir), export_files, args.export_format).run()