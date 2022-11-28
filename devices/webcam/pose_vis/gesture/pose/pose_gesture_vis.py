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
import json
import logging
import cv2
import collections
import numpy as np
import argparse as ap
import math

from pathlib import Path
from enum import Enum
from typing import List, Tuple, Any, Deque
from dataclasses import dataclass
from google.protobuf.json_format import MessageToDict
from pose_vis.utils import parse_sources, parse_resolutions
from pose_vis.utils import absolute_path
from pose_vis.streams.utils.capture_handler import CaptureHandler, AllCapturesFinished
from pose_vis.display import DisplayHandler
# from pose_vis.extensions.hands import HandsExtension, HandsConfig, mp_hands
from pose_vis.extensions.pose import PoseExtension, PoseConfig ,mp_pose
from pose_vis.performance_utility import PerfUtility

logger = logging.getLogger(__name__)

LANDMARK_DISTANCE = [
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_WRIST ),
    # (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_ELBOW ),
    # (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP ),
    # (mp_pose.PoseLandmark.LEFT_ELBOW, mp_pose.PoseLandmark.LEFT_WRIST ),
    # ! Maybe add from wrist to thumb/index finger

    (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_WRIST),
    # (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_ELBOW),
    # (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP ),
    # (mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_WRIST ),



    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_ANKLE ),
    # (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE ),
    # (mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE ),
    # ! Maybe distance from ankle to toe

    (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_ANKLE )
    # (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE ),
    # (mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE )
]

LANDMARK_DIRECTION = [
    # todo --- ADD HERE ---
]

TORSO_DISTANCE = [
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP),
    (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
    (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP)
]

DRAW_DEBUG = False

MAX_DIFFERENCE_VALUE = 3 #! play around with this value


#! go over these
class GV_MODE(Enum):
    VISUALIZATION = 0,
    LABEL_INPUT = 1,
    COLLECTION = 2

#! revisit this class
@dataclass
class AnnotationInfo():
    pose_labels: List[str]
    pose_bounds: List[List[int]]
    gesture_data: List[np.ndarray]
    draw: bool

class PoseGestureVis():
    
    sources: List[str | int]
    resolutions: List[Tuple[int, int, int]]
    cap_handler: CaptureHandler
    dis_handler: DisplayHandler
    perf: PerfUtility
    annotation_infos: Deque[AnnotationInfo]
    data_dir: str
    export_files: List[str]
    export_format: str
    running: bool = True
    mode: GV_MODE = GV_MODE.VISUALIZATION
    label_name: str = ""
    label_names: List[str] = []
    label_data: List[np.ndarray] = []
    video_writers: List[cv2.VideoWriter]

    # ! Test this
    def __init__(self, sources: List[str | int], resolutions: List[Tuple[int, int, int]], data_dir: str, export_files: List[str], export_format: str) -> None:
        self.sources = sources
        self.resolutions = resolutions
        self.data_dir = data_dir
        self.export_files = export_files
        self.export_format = export_format
        self.video_writers = []
        for i in range(len(export_files)):
            self.video_writers.append(cv2.VideoWriter(self.export_files[i], cv2.VideoWriter_fourcc(*self.export_format), self.resolutions[i][2], (self.resolutions[i][0], self.resolutions[i][1])))
        self.load_data()

    def load_data(self):
        label_names = os.path.join(self.data_dir, "labels.json")

        if os.path.exists(label_names):
            with open(label_names, 'r') as _file:
                self.label_names = json.load(_file)

            np_files = [_file for _file in os.listdir(self.data_dir) if _file.endswith('.npy')]
            self.label_data = [np.empty(shape=(0, len(LANDMARK_DISTANCE) + (len(LANDMARK_DIRECTION) * 3)), dtype=np.float32)] * len(label_names) #! Go over this

            for _file in np_files:
                index = int(path(_file).stem)
                self.label_data[index] = np.load(os.path.join(self.data_sir, _file))


    def on_key(self, key: int):
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
                        self.label_data.append(np.ndarray(shape = (0, len(LANDMARK_DISTANCES) + (len(LANDMARK_DIRECTIONS) * 3)), dtype = np.float32))
                    self.mode = GV_MODE.COLLECTION
            else:
                character = chr(key)
                self.label_name += character
        elif self.mode == GV_MODE.COLLECTION:
            if key == 27:
                self.mode = GV_MODE.VISUALIZATION
                self.label_name = ""
            elif key == 32:
                self.save_gesture_keypoints()
        elif key == 27:
            self.running = False



    #! MAYBE A DEF HERE



    def get_bound_data(self, mp_screen_keypoints, mp_world_keypoints, frame:np.ndarray):
        im_width, im_height = frame.shape[1], frame.shape[0]
        # num_hands = len(mp_screen_keypoints)
        pose_bounds: List[List[int]] = [None] * num_hands
        gesture_data: List[np.array] = [np.empty(shape = (len(LANDMARK_DISTANCES) + (len(LANDMARK_DIRECTIONS) * 3)), dtype = np.float32)] * num_hands
        
        

        #! fix bugs here
        for pose_index, landmark_list_screen in enumerate(mp_screen_keypoints):
            landmark_list_screen = landmark_list_screen.landmark
            landmark_list_world = mp_world_keypoints[pose_index].landmark
            bounds_array = np.empty((0, 2), int)
            gesture_distances = np.empty(shape = (len(LANDMARK_DISTANCES) + (len(LANDMARK_DIRECTIONS) * 3)), dtype = np.float32)
            for landmark in landmark_list_screen:
                lx = landmark.x
                ly = landmark.y
                
                bx = min(int(lx * im_width), im_width - 1)
                by = min(int(ly * im_height), im_height - 1)
                point = [np.array((bx, by))]
                bounds_array = np.append(bounds_array, point, axis = 0)
            
            palm_size = 0.0
            for landmark_ids in PALM_DISTANCES:
                lid1 = landmark_ids[0]
                lid2 = landmark_ids[1]
                landmark1 = landmark_list_world[lid1]
                landmark2 = landmark_list_world[lid2]
                palm_size += math.dist((landmark1.x, landmark1.y, landmark1.z), (landmark2.x, landmark2.y, landmark2.z))
            palm_size = palm_size / len(PALM_DISTANCES)

            for ddx, landmark_ids in enumerate(LANDMARK_DISTANCES):
                lid1 = landmark_ids[0]
                lid2 = landmark_ids[1]
                landmark1 = landmark_list_world[lid1]
                landmark2 = landmark_list_world[lid2]

                dist = math.dist((landmark1.x, landmark1.y, landmark1.z), (landmark2.x, landmark2.y, landmark2.z)) / palm_size
                gesture_distances[ddx] = dist

            dir_index = 0
            for landmark_ids in LANDMARK_DIRECTIONS:
                lid1 = landmark_ids[0]
                lid2 = landmark_ids[1]
                landmark1 = landmark_list_world[lid1]
                landmark2 = landmark_list_world[lid2]
                direction = np.asarray((landmark1.x - landmark2.x, landmark1.y - landmark2.y, landmark1.z - landmark2.z))
                direction = direction / np.linalg.norm(direction)
                gesture_distances[len(LANDMARK_DISTANCES) + dir_index] = direction[0]
                gesture_distances[len(LANDMARK_DISTANCES) + dir_index + 1] = direction[1]
                gesture_distances[len(LANDMARK_DISTANCES) + dir_index + 2] = direction[2]
                dir_index += 3

            if DRAW_DEBUG:
                for ddx, landmark_ids in enumerate(LANDMARK_DISTANCES):
                    lid1 = landmark_ids[0]
                    lid2 = landmark_ids[1]
                    landmark1 = landmark_list_screen[lid1]
                    landmark2 = landmark_list_screen[lid2]

                    sx1 = min(int(landmark1.x * im_width), im_width - 1)
                    sy1 = min(int(landmark1.y * im_height), im_height - 1)
                    cv2.putText(frame, f"({lid1})", (sx1, sy1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
                    sx2 = min(int(landmark2.x * im_width), im_width - 1)
                    sy2 = min(int(landmark2.y * im_height), im_height - 1)
                    cv2.putText(frame, f"({lid2})", (sx2, sy2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)

                    cv2.putText(frame, f"({gesture_distances[ddx]:.4f})", ((sx1 + sx2) // 2, (sy1 + sy2) // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
                    cv2.line(frame, (sx1, sy1), (sx2, sy2), (192, 192, 192), 1)

            gesture_data[pose_index] = gesture_distances

            x, y, w, h = cv2.boundingRect(bounds_array)
            pose_bounds[pose_index] = [x, y, x + w, y + h]
        return (hand_bounds, gesture_data)













        return (pose_bounds, gesture_data)
    
    
    def guess_pose(self, source_index, pose_index):
        differences = []

        for label_id, pose in enumerate(self.label_data):
            for i in range(np.ma.size(pose, axis=0)):
                difference = 0.0
                for j in range(len(pose[i])):
                    difference += abs(self.annotation_infos[source_index].gesture_data[pose_index][j] - pose[i][j])
                differences.append((label_id, difference))
        differences.sort(key = lambda x: x[1])
        
        return differences
    
    def draw_annotations(self, source_index: int, frame: np.ndarray):
        ann_info = self.annotation_infos[source_index]
        if not ann_info.draw:
            return
        
        for pose_index, bounds in enumerate(ann_info.pose_bounds):
            label = "?" if len(ann_info.pose_labels) <= pose_index else ann_info.pose_labels[pose_index]
            classification = "?"

            differences = self.guess_pose(source_index, pose_index)
            num_guesses = len(differences)

            if num_guesses > 0 and differences[0][1] <= MAX_DIFFERENCE_VALUE:
                classification = self.label_names[differences[0][0]]
    
            diff_str = f" {differences[0][1]:.2f}" if num_guesses > 0 else ""
            annotation = f"{label}: {classification}{diff_str}"
            text_size = cv2.getTextSize(annotation, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (bounds[0], bounds[1]), (bounds[0] + text_size[0][0] + 2, bounds[1] - text_size[0][1] - 2), (0, 0, 0), -1)
            cv2.putText(frame, annotation, (bounds[0] + 1, bounds[1] - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
    
        if len(self.video_writers) > 0:
            self.video_writers[source_index].write(frame)

    #! TEST THIS 
    def save_pose_keypoints(self) -> None:
        label_index = self.label_names.index(self.label_name)
        for ann_info in self.annotation_infos:
            for pose_keypoints in ann_info.gesture_data:
                self.label_data[label_index] =np.append(self.label_data[label_index], [pose_keypoints], axis = 0)
        
        with open(os.path.join(self.data_dir, "label.json"), "w") as output:
            output.write(json.dumps(self.label_names))
        np.save(os.path.join(self.data_dir, f'{label_index}'), self.label_data[label_index])

    



    def run(self) -> None:
        pass










    
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



if __name__ == '__main__':
    args = parser.parse_args()

    sources = parse_sources(args.sources)
    resolutions = parse_resolutions(len(sources), args.resolutions if args.resolutions is not None else [])
    export_files = []
    if args.export is not None:
        for _file in args.export:
            export_files.append(absolute_path(_file))
    print(export_files)
    PoseGestureVis(sources, resolutions, absolute_path(args.data_dir), export_files, args.export_format).run()