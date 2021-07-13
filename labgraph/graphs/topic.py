#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple
from copy import deepcopy
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type, Union, cast

from ..messages.message import Message
from ..util.error import LabGraphError


PATH_DELIMITER = "/"


class Topic:
    """
    Represents a topic in a graph. A user can instantiate this in a `Module` in
    order to add the topic to their graph. The name of the topic is inferred
    from the class variable to which it is assigned - it remains `None` until
    then. It is referred to via its class variable, which has the added benefit
    of being possible to check for correctness statically. Note that topics are
    basically references to streams, and multiple topics can reference the same
    stream by connecting them via `Group.connections`.

    Args:
        message_type: The message type for messages that are in this topic.
    """

    message_type: Type[Message]

    def __init__(self, message_type: Type[Message]) -> None:
        self.message_type = message_type
        self._name: Optional[str] = None

    def _assign_name(self, name: str) -> None:
        assert self._name is None
        self._name = name

    @property
    def name(self) -> str:
        assert self._name is not None
        return self._name
