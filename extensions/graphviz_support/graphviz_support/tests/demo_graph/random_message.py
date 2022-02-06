#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import numpy as np


class RandomMessage(lg.Message):
    timestamp: float
    data: np.ndarray
