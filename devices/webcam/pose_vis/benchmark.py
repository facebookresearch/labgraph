#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import asyncio
import logging
import time
import multiprocessing
import labgraph as lg

from queue import Queue
from pose_vis.streams.messages import Capture, CaptureResult, ExitSignal
from pose_vis.benchmark_worker import BenchmarkWorker
from typing import Optional, List

logger = logging.getLogger(__name__)

class CapturePoint():
    __slots__ = "rec_time", "captures"

    def __init__(self, rec_time: float, captures: List[Capture]) -> None:
        self.rec_time = rec_time
        self.captures = captures

class BenchmarkConfig(lg.Config):
    """
    Config for `Benchmark`

    Attributes:
        `output_path`: `str` path to output results
        `output_name`: `str` output filename (no extension)
        `run_time`: `int` how long to benchmark for
    """
    output_path: str
    output_name: str
    run_time: int

class BenchmarkState(lg.State):
    """
    State for `Benchmark`

    Attributes:
        `start_time`: `float`
        `done`: `bool`
        `tasks`: `Optional[multiprocessing.JoinableQueue]`
        `worker`: `Optional[BenchmarkWorker]`
    """
    start_time: float = 0.0
    done: bool = False
    points: Optional[Queue] = None
    tasks: Optional[multiprocessing.JoinableQueue] = None
    worker: Optional[BenchmarkWorker] = None

class Benchmark(lg.Node):
    """
    Records timestamps from `CaptureResult`

    Topics:
        `INPUT`: `CaptureResult`
        `OUTPUT_EXIT`: `ExitSignal`
    """
    INPUT = lg.Topic(CaptureResult)
    OUTPUT_EXIT = lg.Topic(ExitSignal)
    state: BenchmarkState
    config: BenchmarkConfig

    def setup(self) -> None:
        logger.info(f" benchmarking for {self.config.run_time} seconds")
        self.state.points = Queue()
        self.state.tasks = multiprocessing.JoinableQueue()
        self.state.worker = BenchmarkWorker(self.state.tasks, 0, self.config.output_path, self.config.output_name)
        self.state.worker.start()

    @lg.publisher(OUTPUT_EXIT)
    async def on_done(self) -> lg.AsyncPublisher:
        while True:
            point: CapturePoint = None
            try:
                point = self.state.points.get_nowait()
            except:
                pass
            if point is not None:
                cap0 = point.captures[0]
                self.state.tasks.put((
                    point.rec_time,
                    (cap0.frame_index, cap0.proc_runtime, cap0.proc_target_fps, cap0.system_timestamp),
                    [point.captures[i].system_timestamp for i in range(1, len(point.captures))]))
            elif self.state.done:
                break
            await asyncio.sleep(0.005)
        yield self.OUTPUT_EXIT, ExitSignal()

    @lg.subscriber(INPUT)
    async def on_msg(self, message: CaptureResult) -> None:
        rec_time = time.perf_counter()
        if self.state.start_time == 0:
            self.state.start_time = rec_time

        if not self.state.done and rec_time - self.state.start_time >= self.config.run_time:
            self.state.done = True
        elif rec_time - self.state.start_time > 5:
            captures = message.captures[:]
            # We're ignoring the first 5 seconds to give the graph time to stabilize and get a more accurate result
            self.state.points.put(CapturePoint(rec_time, captures))
                
    def cleanup(self) -> None:
        logger.info(" closing worker...")
        self.state.tasks.put(None)
        self.state.tasks.join()