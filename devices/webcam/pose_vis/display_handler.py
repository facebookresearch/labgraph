#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import multiprocessing
import cv2
import time
import collections
import numpy as np

from typing import Callable, List, Dict, Deque, Any
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.streams.messages import Capture
from pose_vis.stats_worker import StatsWorker, CapturePoint, CaptureStats

class DisplayHandler():
    """
    Handles image display, drawing, and CV2 key events
    """
    history_size: int
    extension_types: Dict[str, type]
    key_callbacks: List[Callable[[int], None]]
    post_render_callbacks: List[Callable[[int, np.ndarray], None]]
    tasks: multiprocessing.JoinableQueue
    results: multiprocessing.Queue
    worker: StatsWorker
    stats: CaptureStats = None
    captures: Deque[Capture] = None
    extensions: Deque[Dict[str, Any]] = None

    def __init__(self, history_size: int, extension_types: Dict[str, type]) -> None:
        self.history_size = history_size
        self.extension_types = extension_types
        self.key_callbacks = []
        self.post_render_callbacks = []
        if self.history_size > 0:
            self.tasks = multiprocessing.JoinableQueue()
            self.results = multiprocessing.Queue()
            self.worker = StatsWorker(self.tasks, self.results, self.history_size)
            self.worker.start()
    
    def register_key_callback(self, method: Callable[[int], None]) -> None:
        """
        Registers a callback to be called on successful `cv2.waitKey()`
        """
        self.key_callbacks.append(method)

    def register_post_render_callback(self, method: Callable[[int, np.ndarray], None]) -> None:
        """
        Registers a callback to be called after rendering extension data
        """
        self.post_render_callbacks.append(method)

    def update_frames(self, captures: List[Capture], extensions: List[Dict[str, Any]]) -> None:
        """
        Update list of currently presented frames and extension data
        """
        received = time.perf_counter()
        if self.captures is None:
            num_sources = len(captures)
            self.captures = collections.deque(maxlen = num_sources)
            self.extensions = collections.deque(maxlen = num_sources)

        self.captures.extend(captures)
        self.extensions.extend(extensions)

        if self.history_size > 0:
            first_cap = self.captures[0]
            self.tasks.put(CapturePoint(
                first_cap.frame_index,
                first_cap.proc_runtime,
                first_cap.proc_target_fps,
                received,
                [cap.system_timestamp for cap in self.captures]))

    def update_windows(self, framerate: int) -> None:
        """
        Update CV2 windows and process key presses

        `framerate` is for displaying the current framerate in the window title. Set to 0 to disable
        """
        if self.history_size > 0:
            res = None
            try:
                res = self.results.get_nowait()
                self.stats = res
            except:
                pass

        if self.captures is not None:
            for i in range(len(self.captures)):
                cap: Capture = self.captures[i]
                title = f"PoseVis source {cap.stream_id}"
                frame = cv2.cvtColor(cap.frame.copy(), cv2.COLOR_RGB2BGR)
                if len(self.extensions) > 0:
                    ext = self.extensions[i]
                    for key in ext:
                        _type: PoseVisExtension = self.extension_types[key]
                        _type.draw_overlay(frame, ExtensionResult(data = ext[key]))
                for callback in self.post_render_callbacks:
                    callback(i, frame)
                cv2.imshow(title, frame)

                display_info = f"| display: {framerate}fps" if framerate > 0 else ""
                if self.history_size > 0 and self.stats != None:
                    desync_string = f" desync: {(self.stats.desync[i - 1] * 1000):05.2f}ms," if i > 0 and len(self.stats.desync) > 0 else ""
                    source_info = f": {cap.proc_fps}fps, latency: {(self.stats.latency * 1000):05.2f}ms, jitter: {(self.stats.jitter * 1000):05.2f}ms,{desync_string} dropped: {(100 - self.stats.framedrop):05.2f}%"
                    cv2.setWindowTitle(title, f"{title} {source_info} {display_info}")
                else:
                    source_info = f": {cap.proc_fps}fps"
                    cv2.setWindowTitle(title, f"{title} {source_info} {display_info}")

        key = cv2.waitKey(1)
        if key != -1:
            for callback in self.key_callbacks:
                callback(key)

    def cleanup(self) -> None:
        """
        Must be called during program shutdown
        """
        if self.history_size > 0:
            self.tasks.put(None)
            self.worker.join()
        cv2.destroyAllWindows()

