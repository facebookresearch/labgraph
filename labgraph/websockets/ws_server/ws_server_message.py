#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ...messages import Message


class WSServerMessage(Message):
    """
    A message representing data that was/will be communicated
    to WebSocket.
    """

    data: str
