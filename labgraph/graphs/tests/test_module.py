#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Type

import pytest

from ...messages.message import Message
from ..module import Module
from ..topic import PATH_DELIMITER, Topic


class MyMessageA(Message):
    """
    Simple message type for testing topics.
    """

    a: int


class MyMessageB(Message):
    """
    Simple message type for testing topics.
    """

    b: float


class MyModule(Module):
    """
    Simple child module class for testing.
    """

    A = Topic(message_type=MyMessageA)
    B = Topic(message_type=MyMessageB)

    def __init__(self) -> None:
        super(MyModule, self).__init__()


module = MyModule()

expected_topics = (("A", MyMessageA), ("B", MyMessageB))


@pytest.mark.parametrize("topic_name,message_type", expected_topics)  # type: ignore
def test_topics(topic_name: str, message_type: Type[Message]) -> None:
    """
    Tests that MyModule has the correct topics.
    """
    topic = module.__topics__[topic_name]
    assert getattr(module, topic_name) is topic
    assert isinstance(topic, Topic)
    assert topic.message_type == message_type
    assert topic.name == topic_name
