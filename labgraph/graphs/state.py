#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from contextlib import ContextDecorator
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar


class StateMeta(type):
    def __init__(
        cls, name: str, bases: Tuple[type, ...], fields: Dict[str, Any]
    ) -> None:
        super(StateMeta, cls).__init__(name, bases, fields)

        dataclass(cls)  # type: ignore


class State(metaclass=StateMeta):
    """
    Represents the state of a LabGraph module. State objects are useful when we would
    like the module to use some memory to run its algorithm while also being able to:

    - bootstrap that module into some state in the "middle" of its algorithm
    - record all internal events of that module for the purpose of replay
    """

    pass
