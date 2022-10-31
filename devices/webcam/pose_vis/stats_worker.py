#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import multiprocessing
import logging
import collections
import statistics

from typing import List
from pose_vis.utils import relative_latency

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