#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cv2
import h5py
import os
import re
import time
import asyncio
import labgraph as lg
import numpy as np
import mediapipe as mp
import argparse as ap

import mediapipe.python.solutions.hands as HandsType
import mediapipe.python.solutions.drawing_utils as DrawingUtilsType
import mediapipe.python.solutions.drawing_styles as DrawingStylesType

from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList
from typing import NamedTuple, Optional, Tuple, List
from pathlib import Path

from webcam import VideoFrame, WebcamStreamConfig, WebcamStream

mp_drawing: DrawingUtilsType = mp.solutions.drawing_utils
mp_drawing_styles: DrawingStylesType = mp.solutions.drawing_styles
mp_hands: HandsType = mp.solutions.hands

parser = ap.ArgumentParser()
parser.add_argument("-te", "--test", help = "enable test mode", action = "store_true", required = False)
parser.add_argument("-li", "--log-images", help = "add image data to logs", action = "store_true", required = False)
parser.add_argument("-lp", "--log-poses", help = "add pose estimation data to logs", action = "store_true", required = False)
parser.add_argument("-lf", "--log-format", type = str, nargs = 1, choices = ["hdf5"], help = "sepcify logging format. Supports hdf5, default is hdf5", action = "store", required = False)
parser.add_argument("-ld", "--log-dir", type = str, nargs = 1, help = "sepcify log directory (must be full path), default is ./logs", action = "store", required = False)
parser.add_argument("-ln", "--log-name", type = str, nargs = 1, help = "sepcify log filename, default is hand_tracking_utility", action = "store", required = False)
parser.add_argument("-rp", "--replay", help = "replay a log file", action = "store_true", required = False)
parser.add_argument("-dn", "--device-number", type = int, nargs = 1, help = "specify device number to capture from, default is 0", action = "store", required = False)
parser.add_argument("-sr", "--sample-rate", type = int, nargs = 1, help = "specify sample rate from device in Hz, default is 30", action = "store", required = False)
parser.add_argument("-dr", "--device-resolution", type = int, nargs = 2, help = "specify resolution for capture device, default is 854x480", action = "store", required = False)
parser.add_argument("-ri", "--rescale-image", help = "enable rescaling display window from input size", action = "store_true", required = False)
parser.add_argument("-rr", "--rescale_resolution", type = int, nargs = 2, help = "specify resolution to rescale display stream to, default is 1280x720", action = "store", required = False)

class PoseFrame(lg.Message):
    """
    Represents a single frame of a webcam's stream along with its hand tracking estimations

    @attributes:
        frame: a (W, H, 3) shape array of the webcam's stream at its default resolution, in the blue/green/red color space
        landmarks: List[NormalizedLandmarkList], one NormalizedLandmarkList object for each detected hand
    
    NormalizedLandmarkList:
        @attributes:
            landmark: RepeatedCompositeContainer, list-like container with up to 21 hand pose landmarks with their normalized (X, Y, Z) coordinates as attributes
    """

    frame: np.ndarray
    landmarks: List[NormalizedLandmarkList]

class PoseEstimationConfig(lg.Config):
    """
    Configuration for MediaPipe's hand pose esitmation graph
    See https://google.github.io/mediapipe/solutions/hands.html

    @attributes:
        model_complexity: int
        min_detection_confidence: float
        min_tracking_confidence: float
    """

    model_complexity: int
    min_detection_confidence: float
    min_tracking_confidence: float

class PoseEstimationState(lg.State):
    """
    State object for hand pose estimation node
    See https://google.github.io/mediapipe/solutions/hands.html

    @attributes:
        hands: mediapipe.python.solutions.hands.Hands
    """

    hands: Optional[HandsType.Hands] = None

class PoseEstimation(lg.Node):
    """
    PoseEstimation node, runs VideoFrame streams through MediaPipe's Hands graph to generate pose data

    @topics:
        INPUT: VideoFrame
        OUTPUT: PoseFrame
    
    @attributes:
        config: PoseEstimationConfig
        state: PoseEstimationState
    """

    INPUT = lg.Topic(VideoFrame)
    OUTPUT = lg.Topic(PoseFrame)
    config: PoseEstimationConfig
    state: PoseEstimationState

    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def processFrame(self, message: VideoFrame) -> lg.AsyncPublisher:
        results: NamedTuple = self.state.hands.process(cv2.cvtColor(message.frame, cv2.COLOR_BGR2RGB))
        landmarks = results.multi_hand_landmarks
        if landmarks is None:
            landmarks = []
        yield self.OUTPUT, PoseFrame(landmarks = landmarks, frame = message.frame)

    def setup(self):
        self.state.hands = mp_hands.Hands(
            model_complexity = self.config.model_complexity,
            min_detection_confidence = self.config.min_detection_confidence,
            min_tracking_confidence = self.config.min_tracking_confidence)

class LoggingConfig(lg.Config):
    """
    Configuration for the data logging node

    @attributes:
        log_images: bool, whether or not to log images to file
        log_poses: bool, whether or not to log pose data to file
        file_path: str, the path of the log file
    """

    log_images: bool
    log_poses: bool
    file_path: str

class LoggingState(lg.State):
    """
    State object for data logging

    @attributes:
        file: h5py.File
        closed: bool, true if the file is closed
        frame_index: the current index of the frame received from the VideoFrame topic
    """

    file: Optional[h5py.File] = None
    closed: bool = True
    frame_index: int = 0

class Logging(lg.Node):
    """
    Data logging node

    @topics:
        INPUT: PoseFrame
    
    @attributes:
        state: LoggingState
        config: LoggingConfig
    """

    INPUT = lg.Topic(PoseFrame)
    state: LoggingState
    config: LoggingConfig

    @lg.subscriber(INPUT)
    def process(self, message: PoseFrame) -> None:
        if not self.state.closed and (self.config.log_images or self.config.log_poses):
            if self.config.log_images:
                self.state.file.create_dataset("images/{}/image".format(self.state.frame_index), data = message.frame)

            if self.config.log_poses:
                hand_index = 0
                for landmark_list in message.landmarks:
                    arr = np.zeros(shape = (len(landmark_list.landmark), 3), dtype = np.float32)
                    for id, landmark in enumerate(landmark_list.landmark):
                        arr[id] = [landmark.x, landmark.y, landmark.z]
                    self.state.file.create_dataset("images/{0}/hand_landmarks/{1}".format(self.state.frame_index, hand_index), data = arr)
                    hand_index += 1

            self.state.frame_index += 1

    def setup(self) -> None:
        if (self.config.log_images or self.config.log_poses):
            self.state.file = h5py.File(self.config.file_path, "a")
            self.state.closed = False
    
    def cleanup(self) -> None:
        if (self.config.log_images or self.config.log_poses):
            self.state.closed = True
            self.state.file.close()

class LogStreamConfig(lg.Config):
    """
    Config object for streaming logged images

    @attributes:
        sample_rate: int, how many times per second to dispatch an image
        file_path: str, path to the log file
    """

    sample_rate: int
    file_path: str

class LogStream(lg.Node):
    """
    Streams the VideoFrame topic from a log file

    @topics:
        OUTPUT: VideoFrame
    
    @attributes:
        config: LogStreamConfig
        state: LoggingState
    """

    OUTPUT = lg.Topic(VideoFrame)
    config: LogStreamConfig
    state: LoggingState

    @lg.publisher(OUTPUT)
    async def read_file(self) -> lg.AsyncPublisher:
        while not self.state.closed:
            start_time_ns = time.time_ns()

            img_name = "images/{}/image".format(self.state.frame_index)
            if img_name in self.state.file:
                yield self.OUTPUT, VideoFrame(timestamp = time.time(), frame = self.state.file[img_name][:])
                self.state.frame_index += 1
            
            target_delta_time_ns = int(1000000000 / self.config.sample_rate)
            actual_delta_time_ns = time.time_ns() - start_time_ns
            sleepTime = float((target_delta_time_ns - actual_delta_time_ns) / 1000000000)
            await asyncio.sleep(0 if sleepTime < 0 else sleepTime)

    def setup(self) -> None:
        self.state.file = h5py.File(self.config.file_path, "a")
        self.state.closed = False
    
    def cleanup(self) -> None:
        self.state.closed = True
        self.state.file.close()

class DisplayState(lg.State):
    """
    State object for the Display node

    @attributes:
        last_frame: np.ndarray, (W, H, 3) shaped array containing the last processed video frame from the PoseFrame topic
    """

    last_frame: Optional[np.ndarray] = None

class DisplayConfig(lg.Config):
    """
    Config object for the Display node

    @attributes:
        resize: bool, whether or not to resize the base output image after processing
        resize_dimensions: Tuple[int], (W, H) of desired resize dimensions
    """

    resize: bool
    resize_dimensions: Tuple[int]

class Display(lg.Node):
    """
    The Display node, takes PoseFrame messages and presents them to the screen using CV2

    @topics:
        INPUT: PoseFrame
    
    @attributes:
        state: DisplayState
        config: DisplayConfig
    """

    INPUT = lg.Topic(PoseFrame)
    state: DisplayState
    config: DisplayConfig

    @lg.subscriber(INPUT)
    def processFrame(self, message: PoseFrame) -> None:
        frame = message.frame
        for landmarks in message.landmarks:
            mp_drawing.draw_landmarks(
                frame,
                landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
        if self.config.resize:
            frame = cv2.resize(frame, self.config.resize_dimensions)
        self.state.last_frame = frame

    @lg.main
    def display(self):
        while self.state.last_frame is None:
            continue

        while True:
            cv2.imshow("Hand Tracking Utility", self.state.last_frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        cv2.destroyAllWindows()
        raise lg.NormalTermination()

class HandTrackingUtilityConfig(lg.Config):
    """
    Config object for HandTrackingUtilityWebcam and HandTrackingUtilityReplay graphs

    @attributes:
        log_images: bool, whether or not to log images
        log_poses: bool, whether or not to log poses
        log_name: str, the log file name
        log_dir: str, the logging directory (absolute path)
        log_format: str, which file format to use
        device_number: int, device number for WebcamStream node
        sample_rate: int, the sample rate for both WebcamStream and LogStream nodes
        device_resolution: ndarray, a (2) shaped array with the desired width and height of the device's output images
        rescale_image: bool, tells Display node to rescale output
        rescale_resolution: ndarray, a (2) shaped array with the desired width and height target for the Display node
    """

    log_images: bool
    log_poses: bool
    log_name: str
    log_dir: str
    log_format: str
    device_number: int
    sample_rate: int
    device_resolution: np.ndarray
    rescale_image: bool
    rescale_resolution: np.ndarray
    test_image_dimensions: Tuple[int]

def setup_basic(graph: lg.Graph):
    """
    Initialize shared configuration of nodes between HandTrackingUtilityWebcam, HandTrackingUtilityReplay and TestHandler graphs

    @arguments:
        graph: Graph
    """

    graph.POSE.configure(PoseEstimationConfig(model_complexity = 0, min_detection_confidence = 0.5, min_tracking_confidence = 0.5))

    count = 0
    if graph.config.log_images or graph.config.log_poses:
        count = len([entry for entry in os.listdir(graph.config.log_dir) if os.path.isfile(os.path.join(graph.config.log_dir, entry))])
    file_name = "{}_{}.{}".format(graph.config.log_name, count, graph.config.log_format)
    file_path = "{}/{}".format(graph.config.log_dir, file_name)
    graph.LOGGING.configure(LoggingConfig(log_images = graph.config.log_images, log_poses = graph.config.log_poses, file_path = file_path))

def setup_display(graph: lg.Graph):
    """
    Initialize shared configuration of nodes between HandTrackingUtilityWebcam and HandTrackingUtilityReplay graphs

    @arguments:
        graph: Graph
    """

    graph.DISPLAY.configure(DisplayConfig(resize = graph.config.rescale_image, resize_dimensions = graph.config.rescale_resolution))

class HandTrackingUtilityWebcam(lg.Graph):
    """
    Graph object for real time hand tracking using the WebcamStream node

    @attributes:
        POSE: PoseEstimation
        LOGGING: Logging
        DISPLAY: Display
        STREAM: WebcamStream
        config: HandTrackingUtilityConfig
    """

    POSE: PoseEstimation
    LOGGING: Logging
    DISPLAY: Display
    config: HandTrackingUtilityConfig

    STREAM: WebcamStream

    def connections(self) -> lg.Connections:
        return ((self.STREAM.OUTPUT, self.POSE.INPUT), (self.POSE.OUTPUT, self.DISPLAY.INPUT), (self.POSE.OUTPUT, self.LOGGING.INPUT))
    
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.STREAM, self.POSE, self.DISPLAY, self.LOGGING)
    
    def setup(self) -> None:
        setup_basic(self)
        setup_display(self)

        self.STREAM.configure(WebcamStreamConfig(sample_rate = self.config.sample_rate, device_number = self.config.device_number, device_resolution = self.config.device_resolution))

class HandTrackingUtilityReplay(lg.Graph):
    """
    Graph object for real time hand tracking using the LogStream node

    @attributes:
        POSE: PoseEstimation
        LOGGING: Logging
        DISPLAY: Display
        STREAM: LogStream
        config: HandTrackingUtilityConfig
    """

    POSE: PoseEstimation
    LOGGING: Logging
    DISPLAY: Display
    config: HandTrackingUtilityConfig

    STREAM: LogStream

    def connections(self) -> lg.Connections:
        return ((self.STREAM.OUTPUT, self.POSE.INPUT), (self.POSE.OUTPUT, self.DISPLAY.INPUT), (self.POSE.OUTPUT, self.LOGGING.INPUT))
    
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.STREAM, self.POSE, self.DISPLAY, self.LOGGING)
    
    def setup(self) -> None:
        setup_basic(self)
        setup_display(self)

        file_name = "{}.{}".format(graph.config.log_name, graph.config.log_format)
        file_path = "{}/{}".format(graph.config.log_dir, file_name)
        self.STREAM.configure(LogStreamConfig(sample_rate = self.config.sample_rate, file_path = file_path))

class TestVideoStream(lg.Node):
    """
    Outputs a single VideoFrame message for use in test cases

    @topics:
        OUTPUT: VideoFrame
    """

    OUTPUT = lg.Topic(VideoFrame)

    @lg.publisher(OUTPUT)
    async def send_frame(self) -> lg.AsyncPublisher:
        path = os.path.dirname(os.path.realpath(__file__))
        frame = cv2.imread("{}/test/thumbs_up.png".format(path), flags = cv2.IMREAD_COLOR)
        yield self.OUTPUT, VideoFrame(timestamp = time.time(), frame = frame)

class TestHandlerConfig(lg.Config):
    """
    Config object for TestHandler node

    @attributes:
        image_dimensions: Tuple[int], will be compared to PoseFrame's frame.shape attribute
    """

    image_dimensions: Tuple[int]

class TestHandlerState(lg.State):
    """
    State object for tracking whether or not TestHandler has received a PoseFrame
    """
    got_pose: bool = False

class TestHandler(lg.Node):
    """
    Node for testing functionality

    @topics:
        INPUT: PoseFrame
    
    @attributes:
        state: TestHandlerState
        config: TestHandlerConfig
    """

    INPUT = lg.Topic(PoseFrame)
    state: TestHandlerState
    config: TestHandlerConfig

    @lg.subscriber(INPUT)
    def got_message(self, message: PoseFrame) -> None:
        assert message.frame.shape == self.config.image_dimensions, "Video stream frame failed dimension check"
        assert len(message.landmarks) == 2, "Pose landmark list failed length check"
        assert len(message.landmarks[0].landmark) == 21, "Hand 1 landmark list failed length check"
        assert len(message.landmarks[1].landmark) == 21, "Hand 2 landmark list failed length check"
        self.state.got_pose = True
    
    @lg.main
    def check(self) -> None:
        start_time = time.time()
        while not self.state.got_pose:
            time.sleep(1)
            if time.time() - start_time > 30.0:
                break
        assert self.state.got_pose, "PoseFrame failed to arrive within 30 seconds"
        raise lg.NormalTermination()

class TestGraph(lg.Graph):
    """
    Graph for testing functionality

    @attributes:
        POSE: PoseEstimation
        LOGGING: Logging
        HANDLER: Handler
        STREAM: LogStream
        config: HandTrackingUtilityConfig
    """

    STREAM: TestVideoStream
    POSE: PoseEstimation
    LOGGING: Logging
    HANDLER: TestHandler
    config: HandTrackingUtilityConfig

    def connections(self) -> lg.Connections:
        return ((self.STREAM.OUTPUT, self.POSE.INPUT), (self.POSE.OUTPUT, self.HANDLER.INPUT), (self.POSE.OUTPUT, self.LOGGING.INPUT))
    
    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.STREAM, self.POSE, self.LOGGING, self.HANDLER)

    def setup(self):
        setup_basic(self)
        self.HANDLER.configure(TestHandlerConfig(image_dimensions = self.config.test_image_dimensions))

def run_tests(config: HandTrackingUtilityConfig):
    """
    Begins a series of tests:
        Checks that the test image ./test/thumbs_up.png exists

        Ensures PoseFrame comes back with correctly sized data

        Ensures logs are created

        Deletes test log data when finished
    
    @arguments:
        config: HandTrackingUtilityConfig
    """

    path = os.path.dirname(os.path.realpath(__file__))
    test_img_path = "{}/test/thumbs_up.png".format(path)
    assert os.path.isfile(test_img_path), "{} failed isfile()".format(test_img_path)

    graph = TestGraph()
    graph.configure(config)
    runner = lg.ParallelRunner(graph = graph)
    runner.run()

    assert os.path.isfile(graph.LOGGING.config.file_path), "{} failed isfile()".format(graph.LOGGING.config.file_path)
    os.remove(graph.LOGGING.config.file_path)
    os.rmdir("{}/test_log".format(path))

    print("All test cases passed")

if __name__ == "__main__":
    args = parser.parse_args()

    if args.test:
        args.log_images = True
        args.log_poses = True
        args.log_dir = ["./test_log"]
        args.log_name = ["test_log"]

    path = ""
    if args.log_dir:
        # Check if directory is a full path or relative
        if args.log_dir[0].startswith("/") or re.match(r'[a-zA-Z]:', args.log_dir[0]):
            path = args.log_dir[0]
        else:
            dir = args.log_dir[0].removeprefix(".").removeprefix("/").removeprefix("\\")
            path = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), dir)
        path = path.removesuffix("/").removesuffix("\\")
    else:
        path = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), "logs")
    log_name = args.log_name[0] if args.log_name else "hand_tracking_utility"
    log_format = args.log_format[0] if args.log_format else "hdf5"
    if args.log_images or args.log_poses:
        Path(path).mkdir(parents = True, exist_ok = True)
        print("Saving log file (images: {}, poses: {}) {}.{} in {}".format(args.log_images, args.log_poses, log_name, log_format, path))

    config = HandTrackingUtilityConfig(
        log_images = args.log_images,
        log_poses = args.log_poses,
        log_name = log_name,
        log_dir = path,
        log_format = log_format,
        device_number = args.device_number if args.device_number else 0,
        sample_rate = args.sample_rate[0] if args.sample_rate else 30,
        device_resolution = np.array([args.device_resolution[0], args.device_resolution[1]] if args.device_resolution else np.array([854, 480])),
        rescale_image = args.rescale_image,
        rescale_resolution = np.array([args.rescale_resolution[0], args.rescale_resolution[1]] if args.rescale_resolution else np.array([1280, 720])),
        test_image_dimensions = (778, 860, 3)
    )
    graph = None
    if args.test:
        run_tests(config)
    else:
        if args.replay:
            graph = HandTrackingUtilityReplay()
            graph.configure(config)
        else:
            graph = HandTrackingUtilityWebcam()
            graph.configure(config)
        runner = lg.ParallelRunner(graph = graph)
        runner.run()