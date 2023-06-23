#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import logging
import multiprocessing

from typing import List
from typing import Dict, List, Tuple, Union

from pose_vis.streams.messages import Capture

logger = logging.getLogger(__name__)

class BenchmarkWorker(multiprocessing.Process):
    """
    Handles capturing performance metrics without skewing results
    """

    tasks: multiprocessing.JoinableQueue
    worker_number: int
    output_path: str
    output_name: str
    start_time = 0.0
    output: Dict[str, Union[float, int, List[Tuple[float, float]], List[List[float]]]] = {"runtime": 0.0, "target_fps": 0, "frame_index": 0, "times": [], "sync": []}

    def __init__(self, tasks: multiprocessing.JoinableQueue, worker_number: int, output_path: str, output_name: str):
        self.tasks = tasks
        self.worker_number = worker_number
        self.output_path = output_path
        self.output_name = output_name
        super().__init__()
    
    def run(self):
        logger.info(f" worker {self.worker_number}: started")
        while True:
            val: Tuple[float, Tuple[int, float, int, float], List[float]] = self.tasks.get()
            if val is not None:
                self.output["runtime"] = val[1][1]
                self.output["target_fps"] = val[1][2]
                self.output["frame_index"] = val[1][0]
                self.output["times"].append((val[1][3], val[0]))
                if len(val[2]) > 0:
                    self.output["sync"].append(val[2])
                self.tasks.task_done()
            else:
                self.tasks.task_done()
                logger.info(f" saving timings to {self.output_path}")
                with open(os.path.join(self.output_path, f"{self.output_name}.json"), "w") as output:
                    output.write(json.dumps(self.output))
                logger.info(f" worker {self.worker_number}: shutting down")
                break