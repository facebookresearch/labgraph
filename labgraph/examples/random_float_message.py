#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg


class RandomFloatMessage(lg.Message):
    timestamp: float
    data: float
