#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import time
import logging
import multiprocessing
import cv2
import numpy as np

from multiprocessing import shared_memory
from typing import List, Tuple, Union, Optional, Any
from pose_vis.streams.messages import Capture
from pose_vis.extension import PoseVisExtension
from pose_vis.performance_utility import PerfUtility

# https://docs.opencv.org/4.2.0/d4/da8/group__imgcodecs.html#ga288b8b3da0892bd651fce07b3bbd3a56
SUPPORTED_IMG_EXTENSIONS = [".bmp", ".jpeg", ".jpg", ".png", ".webp"]

logger = logging.getLogger(__name__)

class CaptureWorker(multiprocessing.Process):
    """
    Handles setup of CV2 VideoCapture, frame indexing, runtime tracking, and communication with its parent process
    """
    connections: Tuple[Any, Any]
    shared_mem: shared_memory.SharedMemory
    extensions: List[PoseVisExtension]
    worker_number: int
    cap_source: Union[int, str]
    resolution: np.ndarray
    images: List[str] = []
    capture_finished: bool = False
    frame_index: int = 0
    start_time: float = 0.0
    blank_frame: Optional[np.ndarray] = None
    capture: Optional[cv2.VideoCapture] = None
    perf: Optional[PerfUtility] = None

    def __init__(self, connections: Tuple[Any, Any], extensions: List[PoseVisExtension], cap_source: Union[int, str], resolution: np.ndarray, worker_number: int):
        self.connections = connections
        self.extensions = extensions
        self.cap_source = cap_source
        self.resolution = resolution
        self.worker_number = worker_number
        super().__init__()
    
    def setup(self) -> None:
        self.perf = PerfUtility()

        self.shared_mem = shared_memory.SharedMemory(name = f"pv_worker_{self.worker_number}")

        self.blank_frame = np.zeros(shape = (self.resolution[1], self.resolution[0], 3), dtype = np.uint8)
        
        self.open_capture()

        for ext in self.extensions:
            logger.info(f" worker {self.worker_number}: setting up extension {ext.__class__.__name__}")
            ext.setup()
        logger.info(f" worker {self.worker_number}: started")

    def open_capture(self) -> None:
        if isinstance(self.cap_source, int) or os.path.isfile(self.cap_source):
            logger.info(f" opening source {self.cap_source}")
            self.capture = cv2.VideoCapture(self.cap_source)

            if self.capture.isOpened():
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.capture.set(cv2.CAP_PROP_FPS, self.resolution[2])
                self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.capture.set(cv2.CAP_PROP_CONVERT_RGB, 1)
                logger.info(f" source {self.cap_source} opened and configured")
            else:
                logger.warning(f" source {self.cap_source} does not exist")
        
        else:
            logger.info(f" opening directory: {self.cap_source}")
            for _file in os.listdir(self.cap_source):
                ext = os.path.splitext(_file)[1]
                if ext.lower() in SUPPORTED_IMG_EXTENSIONS:
                    self.images.append(os.path.join(self.cap_source, _file))
            logger.info(f" found {len(self.images)} image(s)")

    def read_capture(self) -> Tuple[np.ndarray, float]:
        num_images = len(self.images)

        if self.capture is not None and self.capture.isOpened():
            success, frame = self.capture.read()
            timestamp = time.perf_counter()

            if success:
                if isinstance(self.cap_source, str):
                    if frame.shape != (self.resolution[1], self.resolution[0], 3):
                        frame = cv2.resize(frame, (self.resolution[0], self.resolution[1]), interpolation = cv2.INTER_NEAREST)
                else:
                    frame = cv2.flip(frame, 1)

                frame.flags.writeable = False
                self.frame_index += 1
                return (frame, timestamp)

            elif isinstance(self.cap_source, str):
                self.capture_finished = True
            else:
                logger.warning(f" source {self.cap_source} gave unsuccessful grab()")

        elif num_images > 0 and self.frame_index < num_images:
            if self.frame_index + 1 == num_images:
                self.capture_finished = True

            self.frame_index += 1
            return (cv2.imread(self.images[self.frame_index], cv2.IMREAD_COLOR), time.perf_counter())

        return (self.blank_frame.copy(), time.time())

    def cleanup(self) -> None:
        if self.capture is not None and self.capture.isOpened():
            self.capture.release()
            logger.info(f" source {self.cap_source} released")
        logger.info(f" worker {self.worker_number}: shutting down")
        for ext in self.extensions:
            ext.cleanup()
    
    def run(self) -> None:
        self.setup()

        while True:
            if self.start_time == 0:
                self.start_time = time.perf_counter()

            self.perf.update_start()
            instruction: bool = self.connections[0].recv()

            if instruction:
                frame, timestamp = self.read_capture()
                dst = np.ndarray(shape = frame.shape, dtype = frame.dtype, buffer = self.shared_mem.buf)
                dst[:] = frame[:]
                cap = Capture(
                    None,
                    self.worker_number,
                    self.frame_index,
                    timestamp,
                    self.perf.delta_time if self.perf.delta_time > 0 else 1 / self.resolution[2],
                    time.perf_counter() - self.start_time,
                    self.perf.updates_per_second,
                    self.resolution[2])

                ext_results = {}
                for ext in self.extensions:
                    ext_result = ext.process_frame(frame)
                    ext_results[ext.__class__.__name__] = ext_result.data
                
                self.connections[1].send((cap, ext_results, self.capture_finished))
            else:
                break

            self.perf.update_end()

        self.cleanup()