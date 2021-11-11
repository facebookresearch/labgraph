#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# Built-in imports

# Import labgraph
import labgraph as lg

# Imports required for this example
import numpy as np

# A data type used in streaming, see docs: Messages
class RandomMessage(lg.Message):
    timestamp: float
    data: np.ndarray


