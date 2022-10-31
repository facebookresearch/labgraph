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

import multiprocessing
import logging
import cv2
import time
import collections
import statistics
import labgraph as lg

from typing import List, Optional, Dict, Deque, Any
from threading import Lock
from pose_vis.utils import relative_latency
from pose_vis.extension import PoseVisExtension, ExtensionResult
from pose_vis.performance_utility import PerfUtility
from pose_vis.streams.messages import Capture, CaptureResult, ExitSignal

logger = logging.getLogger(__name__)

class CapturePoint():
    """
    Represents a captured frame's point in time
    """
    __slots__ = "frame_index", "runtime", "target_fps", "receive_time", "device_timestamps"

    def __init__(self, frame_index: int, runtime: float, target_fps: int, receive_time: float, device_timestamps: List[float]) -> None:
        self.frame_index = frame_index
        self.runtime = runtime
        self.target_fps = target_fps
        self.receive_time = receive_time
        self.device_timestamps = device_timestamps

class CaptureStats():
    """
    Represents performance statistics
    """
    __slots__ = "framedrop", "latency", "jitter", "desync"

    def __init__(self, framedrop: float, latency: float, jitter: float, desync: List[float]):
        self.framedrop = framedrop
        self.latency = latency
        self.jitter = jitter
        self.desync = desync

class StatsWorker(multiprocessing.Process):
    """
    Processes performance stats without skewing results
    """
    tasks: multiprocessing.JoinableQueue
    results: multiprocessing.Queue
    history_size: int
    timestamps: collections.deque
    desync_vals: List[collections.deque]
    latency_vals: collections.deque

    def __init__(self, tasks: multiprocessing.JoinableQueue, results: multiprocessing.Queue, history_size: int) -> None:
        self.tasks = tasks
        self.results = results
        self.history_size = history_size
        super().__init__()
    
    def setup(self) -> None:
        self.timestamps = collections.deque(maxlen = self.history_size)
        self.latency_vals = collections.deque(maxlen = self.history_size)
        self.desync_vals = []
    
    def run(self) -> None:
        self.setup()
        while True:
            point: CapturePoint = self.tasks.get()
            if point is not None:
                extra_sources = 0

                # time created, time received
                self.timestamps.append((point.device_timestamps[0], point.receive_time))
                if len(self.timestamps) > 1:
                    extra_sources = len(point.device_timestamps) - 1
                    if extra_sources > 0:
                        if len(self.desync_vals) != extra_sources:
                            self.desync_vals = [collections.deque(maxlen = self.history_size)] * extra_sources
                        for i in range(extra_sources):
                            self.desync_vals[i].append(abs(point.device_timestamps[i + 1] - point.device_timestamps[0]))

                    # TODO: this may not be correct
                    # `rel_device` can be greater than `rel_receive`, for now we just take the absolute value
                    self.latency_vals.append(abs(relative_latency(point.device_timestamps[0], point.receive_time, self.timestamps[0][0], self.timestamps[0][1])))

                expected_frames = round(point.runtime * point.target_fps)
                framedrop = (point.frame_index / (1 if expected_frames == 0 else expected_frames)) * 100

                latency = 0.0
                jitter = 0.0
                desync = []
                if len(self.latency_vals) > 1:
                    latency = statistics.median(self.latency_vals)
                    jitter = statistics.stdev(self.latency_vals)
                    
                    if extra_sources > 0:
                        desync = [statistics.median(li) for li in self.desync_vals]

                stats = CaptureStats(
                    framedrop,
                    latency,
                    jitter,
                    desync)

                self.results.put(stats)
                self.tasks.task_done()
            else:
                self.tasks.task_done()
                break

class DisplayConfig(lg.Config):
    """
    Config for Display node

    Attributes:
        `target_framerate`: `int` target framerate for updating CV2 windows
        `stats_history_size`: `int` how many frame stats to remember
        `extension_types`: `Dict[str, type]` type lookup for enabled extensions
    """
    target_framerate: int
    stats_history_size: int
    extension_types: Dict[str, type]

class DisplayState(lg.State):
    """
    State for Display node

    Attributes:
        `captures`: `List[Capture]` latest captures
        `extensions`: `List[Dict[str, Any]]` latest extension results
        `lock`: `Lock` used when accessing `captures` or `extensions`
        `perf`: `PerfUtility` to measure performance
        `stream_fps`: `int` FPS reported from active stream
        `stream_time`: `float` delta time reported from active stream
        `running`: `bool`
    """
    captures: Optional[Deque[Capture]] = None
    extensions: Optional[Deque[Dict[str, Any]]] = None
    stream_fps: int = 0
    stream_time: float = 0.0
    running: bool = True
    tasks: Optional[multiprocessing.JoinableQueue] = None
    results: Optional[multiprocessing.Queue] = None
    worker: Optional[StatsWorker] = None
    perf: PerfUtility = PerfUtility()

class Display(lg.Node):
    """
    Draws overlays and presents them

    Topics:
        `INPUT`: `CaptureResult`
    
    Attributes:
        `state`: `DisplayState`
        `config`: `DisplayConfig`
    """
    INPUT = lg.Topic(CaptureResult)
    INPUT_EXIT_STREAM = lg.Topic(ExitSignal)
    INPUT_EXIT_USER = lg.Topic(ExitSignal)
    state: DisplayState
    config: DisplayConfig

    @lg.subscriber(INPUT)
    async def update(self, message: CaptureResult) -> None:
        received = time.perf_counter()
        if self.state.captures is None:
            num_sources = len(message.captures)
            self.state.captures = collections.deque(maxlen = num_sources)
            self.state.extensions = collections.deque(maxlen = num_sources)

        self.state.captures.extend(message.captures[:])
        self.state.extensions.extend(message.extensions[:])

        if self.config.stats_history_size > 0:
            first_cap = self.state.captures[0]
            self.state.tasks.put(CapturePoint(
                first_cap.frame_index,
                first_cap.proc_runtime,
                first_cap.proc_target_fps,
                received,
                [cap.system_timestamp for cap in self.state.captures]))

    @lg.subscriber(INPUT_EXIT_STREAM)
    async def on_exit_stream(self, _: ExitSignal) -> None:
        self.state.running = False
    
    @lg.subscriber(INPUT_EXIT_USER)
    async def on_exit_user(self, _: ExitSignal) -> None:
        self.state.running = False

    def setup(self) -> None:
        if self.config.stats_history_size > 0:
            self.state.tasks = multiprocessing.JoinableQueue()
            self.state.results = multiprocessing.Queue()
            self.state.worker = StatsWorker(self.state.tasks, self.state.results, self.config.stats_history_size)
            self.state.worker.start()

    @lg.main
    def display(self) -> None:
        stats: CaptureStats = None
        while self.state.running:
            self.state.perf.update_start()

            if self.config.stats_history_size > 0:
                res = None
                try:
                    res = self.state.results.get_nowait()
                    stats = res
                except:
                    pass

            if self.state.captures is not None:
                for i in range(len(self.state.captures)):
                    cap: Capture = self.state.captures[i]
                    title = f"PoseVis source {cap.stream_id}"
                    frame = cap.frame.copy()
                    if len(self.state.extensions) > 0:
                        ext = self.state.extensions[i]
                        for key in ext:
                            _type: PoseVisExtension = self.config.extension_types[key]
                            _type.draw_overlay(frame, ExtensionResult(data = ext[key]))
                    cv2.imshow(title, frame)

                    if self.config.stats_history_size > 0 and stats != None:
                        desync_string = f" desync: {(stats.desync[i - 1] * 1000):05.2f}ms," if i > 0 and len(stats.desync) > 0 else ""
                        source_info = f": {cap.proc_fps}fps, latency: {(stats.latency * 1000):05.2f}ms, jitter: {(stats.jitter * 1000):05.2f}ms,{desync_string} dropped: {(100 - stats.framedrop):05.2f}%"
                        display_info = f"display: {self.state.perf.updates_per_second}fps"
                        cv2.setWindowTitle(title, f"{title} {source_info} | {display_info}")
                    else:
                        source_info = f": {cap.proc_fps}fps"
                        display_info = f"display: {self.state.perf.updates_per_second}fps"
                        cv2.setWindowTitle(title, f"{title} {source_info} | {display_info}")

            if cv2.waitKey(1) & 0xFF == 27:
                self.state.running = False

            time.sleep(self.state.perf.get_remaining_sleep_time(self.config.target_framerate))

            self.state.perf.update_end()

        raise lg.NormalTermination()
    
    def cleanup(self):
        if self.config.stats_history_size > 0:
            self.state.tasks.put(None)
            self.state.worker.join()
        cv2.destroyAllWindows()