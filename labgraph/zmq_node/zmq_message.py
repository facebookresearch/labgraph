#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ..messages import Message
from ..messages.types import BytesType


class ZMQMessage(Message):
    """
    A message representing data that was/will be communicated
    to ZMQ.
    """

    data: bytes
