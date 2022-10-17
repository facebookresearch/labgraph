#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import asyncio
import cv2
import labgraph as lg
import numpy as np

from pose_vis.video_stream import ProcessedVideoFrame, StreamMetaData
from pose_vis.frame_processor import FrameProcessor
from pose_vis.extension import PoseVisExtension, CombinedExtensionResult
from pose_vis.performance_tracking import PerfUtility
from typing import Optional, Tuple, List

class CameraStreamConfig(lg.Config):
    device_id: int
    stream_id: int
    device_resolution: Tuple[int, int, int]
    extensions: List[PoseVisExtension]

class CameraStreamState(lg.State):
    cap: Optional[cv2.VideoCapture] = None
    metadata: Optional[StreamMetaData] = None
    perf: PerfUtility = PerfUtility()
    frame_index: int = 0
    frame_processor: Optional[FrameProcessor] = None

class CameraStream(lg.Node):
    OUTPUT_FRAMES = lg.Topic(ProcessedVideoFrame)
    OUTPUT_EXTENSIONS = lg.Topic(CombinedExtensionResult)
    config: CameraStreamConfig
    state: CameraStreamState

    @lg.publisher(OUTPUT_FRAMES)
    @lg.publisher(OUTPUT_EXTENSIONS)
    async def read_camera(self) -> lg.AsyncPublisher:
        while True:
            self.state.perf.update_start()

            error = False
            cap_state = self.state.cap.isOpened() if self.state.cap else False

            frame: np.ndarray
            if cap_state:
                try:
                    success, frame = self.state.cap.read()
                    if not success:
                        error = True
                except cv2.error:
                    error = True

                if error:
                    self.state.cap.release()
                    print("CameraStream: warning: device {} capture has encountered an error and has been closed".format(self.config.device_id))
            
            if not cap_state or error:
                frame = np.zeros(shape = (self.config.device_resolution[1], self.config.device_resolution[0], 3), dtype = np.uint8)
            
            overlayed, ext_results = self.state.frame_processor.process_frame(frame.copy(), self.state.metadata)
            yield self.OUTPUT_FRAMES, ProcessedVideoFrame(original = frame, overlayed = overlayed, frame_index = self.state.frame_index, metadata = self.state.metadata)
            yield self.OUTPUT_EXTENSIONS, CombinedExtensionResult(results = ext_results)

            self.state.metadata.actual_framerate = self.state.perf.updates_per_second
            self.state.frame_index += 1
            await asyncio.sleep(PerfUtility.ns_to_s(PerfUtility.get_sleep_time_ns(self.state.perf.last_update_start_ns, self.config.device_resolution[2])))
            self.state.perf.update_end()

    def setup(self) -> None:
        print(f"CameraStream: opening device id: {self.config.device_id}")
        self.state.cap = cv2.VideoCapture(self.config.device_id)
        if self.state.cap and self.state.cap.isOpened():
            self.state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.device_resolution[0])
            self.state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.device_resolution[1])
            self.state.cap.set(cv2.CAP_PROP_FPS, self.config.device_resolution[2])
        else:
            print("CameraStream: warning: device id {} does not exist".format(self.config.device_id))
        self.state.metadata = StreamMetaData(
            target_framerate = self.config.device_resolution[2],
            device_id = self.config.device_id,
            stream_id = self.config.stream_id,
            actual_framerate = 0)
        self.state.frame_processor = FrameProcessor()
        self.state.frame_processor.extensions = self.config.extensions
        self.state.frame_processor.setup()

    def cleanup(self) -> None:
        self.state.frame_processor.cleanup()
        if self.state.cap and self.state.cap.isOpened():
            print(f"CameraStream: closing device id: {self.config.device_id}")
            self.state.cap.release()