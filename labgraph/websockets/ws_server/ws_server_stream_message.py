#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import numpy as np

from ...messages import Message


class WSStreamMessage(Message):
    """
    A message representing data that was/will be communicated
    to WebSocket.
    """

    samples: np.float64
    stream_name: str
    stream_id: str
