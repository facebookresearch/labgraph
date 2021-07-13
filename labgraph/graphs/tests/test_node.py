#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Dict, Type

import pytest

from ...messages.message import Message
from ...util.error import LabGraphError
from ..method import (
    AsyncPublisher,
    NodeMethod,
    Publisher,
    Subscriber,
    Transformer,
    publisher,
    subscriber,
)
from ..node import Node
from ..topic import Topic


class MyMessage(Message):
    int_field: int


class MyNode(Node):
    A = Topic(MyMessage)
    B = Topic(MyMessage)

    @subscriber(A)
    def my_subscriber(self, message: MyMessage) -> None:
        pass

    @publisher(A)
    def my_publisher(self, message: MyMessage) -> AsyncPublisher:
        pass

    @subscriber(A)
    @publisher(B)
    def my_transformer(self, message: MyMessage) -> AsyncPublisher:
        pass


node = MyNode()

expected_node_methods = (
    (
        MyNode,
        {
            "my_publisher": Publisher(
                name="my_publisher", published_topic_paths=("A",)
            ),
            "my_subscriber": Subscriber(
                name="my_subscriber", subscribed_topic_path="A"
            ),
            "my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("B",),
                subscribed_topic_path="A",
            ),
        },
    ),
)


@pytest.mark.parametrize("node_type,methods", expected_node_methods)  # type: ignore
def test_node_methods(node_type: Type[Node], methods: Dict[str, NodeMethod]) -> None:
    """
    Tests that MyNode has the expected NodeMethod objects.
    """
    node = node_type()
    for method_name, method in methods.items():
        assert isinstance(node.__methods__[method_name], type(method))
        assert vars(node.__methods__[method_name]) == vars(method)


def test_node_invalid_published_topic() -> None:
    bad_topic = Topic(MyMessage)
    with pytest.raises(LabGraphError) as err:

        class BadTopicNode(Node):
            @publisher(bad_topic)
            def my_publisher(self) -> AsyncPublisher:
                pass

    assert (
        "Invalid topic published by BadTopicNode.my_publisher - set the topic as a "
        "class variable in BadTopicNode" in str(err.value)
    )


def test_node_invalid_subscribed_topic() -> None:
    bad_topic = Topic(MyMessage)
    with pytest.raises(LabGraphError) as err:

        class BadTopicNode(Node):
            @subscriber(bad_topic)
            def my_subscriber(self, message: MyMessage) -> None:
                pass

    assert (
        "Invalid topic subscribed to by BadTopicNode.my_subscriber - set the topic as "
        "a class variable in BadTopicNode" in str(err.value)
    )


class BadPublishersNode(Node):
    OUTPUT = Topic(MyMessage)

    @publisher(OUTPUT)
    async def bad_publisher1(self) -> AsyncPublisher:
        yield self.OUTPUT, MyMessage(int_field=1)

    @publisher(OUTPUT)
    async def bad_publisher2(self) -> AsyncPublisher:
        yield self.OUTPUT, MyMessage(int_field=1)


def test_bad_publishers_node() -> None:
    with pytest.raises(LabGraphError) as err:
        _ = BadPublishersNode()

    assert (
        "The stream for topics (OUTPUT) has multiple publishers, but only one "
        "publisher is allowed. The following publishers were found:\n"
        "- bad_publisher1\n"
        "- bad_publisher2" in str(err.value)
    )
