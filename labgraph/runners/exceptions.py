#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ..messages.message import Message


class NormalTermination(Exception):
    """
    Raised to indicate normal graph termination.
    """

    pass


class ExceptionMessage(Message):
    """
    Holds the bytes for a thrown exception in a LabGraph message.
    Convenient for passing exceptions between processes.
    """

    exception: bytes
