#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import multiprocessing
import logging
import numpy as np

from multiprocessing import shared_memory
from typing import Tuple, List, Union, Dict, Any
from pose_vis.streams.utils.capture_worker import CaptureWorker
from pose_vis.streams.messages import Capture
from pose_vis.extension import PoseVisExtension

logger = logging.getLogger(__name__)

class AllCapturesFinished(Exception):
    """
    Raised when all captures finish (e.g video files are done playing, image directories are processed)
    """
    pass

class CaptureHandler():
    """
    Handles capturing video frames via `CaptureWorker` objects
    """
    sources: List[Union[int, str]]
    resolutions: List[Tuple[int, int, int]]
    extensions: List[PoseVisExtension]
    shared_mems: List[shared_memory.SharedMemory] = []
    workers: List[CaptureWorker] = []
    # PipeConnection on Windows, different on Linux/Mac
    connections: List[Tuple[Any, Any]] = []
    finished_captures: List[int] = []
    num_sources: int = 0

    def __init__(self, sources: List[Union[int, str]], resolutions: List[Tuple[int, int, int]], extensions: List[PoseVisExtension]) -> None:
        self.sources = sources
        self.resolutions = resolutions
        self.extensions = extensions

        self.num_sources = len(self.sources)
        for i in range(self.num_sources):
            size = np.dtype(np.uint8).itemsize * np.prod((self.resolutions[i][1], self.resolutions[i][0], 3))
            try:
                self.shared_mems.append(shared_memory.SharedMemory(create = True, size = size.item(), name = f"pv_worker_{i}"))
            except FileExistsError as e:
                if os.name == "nt":
                    # This can happen if the program crashes and leaves a stray processes running
                    # Windows will automatically delete the file when it's not in use by a process
                    # https://github.com/python/cpython/issues/85059
                    logger.critical(" shared memory file already exists. Please terminate any stray Python processes and try again")
                    raise e
                else:
                    shm = shared_memory.SharedMemory(name = f"pv_worker_{i}")
                    shm.close()
                    shm.unlink()
                    # Unlink and re-create incase the array size has changed
                    self.shared_mems.append(shared_memory.SharedMemory(create = True, size = size.item(), name = f"pv_worker_{i}"))

            outbound = multiprocessing.Pipe()
            inbound = multiprocessing.Pipe()
            self.connections.append((outbound[0], inbound[0]))
            self.workers.append(CaptureWorker(
                (outbound[1], inbound[1]),
                self.extensions,
                self.sources[i],
                np.asarray(self.resolutions[i]),
                i))
        
    def start_workers(self) -> None:
        for i in range(self.num_sources):
            self.workers[i].start()

    def get_captures(self) -> List[Tuple[Capture, Dict[str, Any], bool]]:
        if len(self.finished_captures) == self.num_sources:
            raise AllCapturesFinished

        for i in range(self.num_sources):
            if i not in self.finished_captures:
                self.connections[i][0].send(True)
        
        result: List[Tuple[Capture, Dict[str, Any], bool]] = [self.connections[i][1].recv() for i in range(self.num_sources) if i not in self.finished_captures]
        for idx, res in enumerate(result):
            res[0].frame = np.ndarray(shape = (self.resolutions[i][1], self.resolutions[i][0], 3), dtype = np.uint8, buffer = self.shared_mems[idx].buf)[:]

        for res in result:
            if res[2]:
                self.finished_captures.append(res[0].stream_id)

        return result
    
    def cleanup(self) -> None:
        for con in self.connections:
            con[0].send(False)
        for worker in self.workers:
            worker.join()
        for shm in self.shared_mems:
            shm.close()
            shm.unlink()