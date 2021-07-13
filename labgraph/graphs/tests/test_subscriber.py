#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import pytest

from ...messages.message import Message
from ...util.error import LabGraphError
from ..method import subscriber
from ..node import Node
from ..topic import Topic


class MyMessage(Message):
    int_field: int


def test_duplicate_subscriber() -> None:
    """
    Tests that an error is thrown when multiple subscriber decorators are applied to a
    method.
    """
    with pytest.raises(LabGraphError) as err:

        class MyNode(Node):
            A = Topic(MyMessage)

            @subscriber(A)
            @subscriber(A)
            def my_subscriber(self, message: MyMessage) -> None:
                pass

    assert "Method 'my_subscriber' already has a @subscriber decorator" in str(
        err.value
    )


def test_subscriber_signature() -> None:
    """
    Tests that an error is thrown when a subscriber has an invalid signature for message
    callbacks.
    """
    with pytest.raises(LabGraphError) as err:

        class MyNode(Node):
            A = Topic(MyMessage)

            @subscriber(A)
            def my_subscriber(self) -> None:
                pass

    assert (
        "Expected subscriber 'my_subscriber' to have signature def my_subscriber(self, "
        "message: MyMessage) -> None"
    ) in str(err.value)
