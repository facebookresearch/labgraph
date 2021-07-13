#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Optional, Tuple, Type

from ..messages.message import Message
from ..util.random import random_string


STREAM_ID_LENGTH = 16


class Stream:
    """
    Represents a stream, which is a sequence of messages that is accessible in
    real-time. A stream may be accessed via one or more topics.
    """

    id: str
    topic_paths: Tuple[str, ...]
    message_type: Optional[Type[Message]]

    def __init__(
        self,
        topic_paths: Tuple[str, ...],
        message_type: Optional[Type[Message]] = None,
        id: Optional[str] = None,
    ) -> None:
        self.topic_paths = topic_paths
        self.message_type = message_type
        self.id = id or random_string(STREAM_ID_LENGTH)
