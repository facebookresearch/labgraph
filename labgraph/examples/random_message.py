#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.
# -*- coding: utf-8 -*-

# Built-in imports

# Import labgraph
import labgraph as lg

# Imports required for this example
import numpy as np


# A data type used in streaming, see docs: Messages
class RandomMessage(lg.Message):
    timestamp: float
    data: np.ndarray
