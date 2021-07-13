#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import pytest

from ...messages.message import Message
from ...util.error import LabGraphError
from ..method import AsyncPublisher, publisher
from ..topic import Topic


class MyMessage(Message):
    int_field: int


def test_duplicate_publisher() -> None:
    with pytest.raises(LabGraphError) as err:
        A = Topic(MyMessage)

        @publisher(A)
        @publisher(A)
        def my_publisher() -> AsyncPublisher:
            pass

    assert (
        "Method 'my_publisher' got two @publisher decorators for the same topic"
        in str(err.value)
    )


def test_multiple_publisher() -> None:
    A = Topic(MyMessage)
    B = Topic(MyMessage)

    @publisher(A)
    @publisher(B)
    def my_publisher() -> AsyncPublisher:
        pass
