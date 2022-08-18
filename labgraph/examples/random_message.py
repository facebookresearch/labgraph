#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np


class RandomMessage(lg.Message):
    timestamp: any
    data: np.ndarray

    latency: any = 1.0
    throughput: any = 2.0
    datarate: any  = 3.0
