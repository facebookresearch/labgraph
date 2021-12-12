#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Optional
import labgraph as lg
import numpy as np


class MyState(lg.State):
    field: Optional[np.ndarray] = None
