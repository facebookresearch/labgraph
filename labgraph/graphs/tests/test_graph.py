#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, Dict

from ...messages.message import Message
from ..graph import Graph
from ..group import Connections, Group
from ..method import AsyncPublisher, publisher, subscriber
from ..node import Node
from ..topic import Topic


pytest_plugins = ["pytest_mock"]


def test_incomplete_graph(mocker: Any) -> None:
    """
    Tests that an attempted graph with topics that lack publishers and/or subcribers
    logs a warning.
    """
    logger_module = __name__.rsplit(".", 2)[0] + ".graph.logger"
    mock_logger = mocker.patch(logger_module)

    class MyMessage(Message):
        int_field: int

    class MyNode(Node):
        A = Topic(MyMessage)
        B = Topic(MyMessage)

        @subscriber(A)
        @publisher(B)
        def my_transformer(self, message: MyMessage) -> AsyncPublisher:
            pass

    class MyChildGroup(Group):
        C = Topic(MyMessage)
        MY_NODE1: MyNode
        MY_NODE2: MyNode

        def connections(self) -> Connections:
            return ((self.C, self.MY_NODE1.A), (self.MY_NODE1.B, self.MY_NODE2.A))

    class MyParentGroup(Group):
        D = Topic(MyMessage)
        E = Topic(MyMessage)
        MY_CHILD1: MyChildGroup
        MY_CHILD2: MyChildGroup

        def connections(self) -> Connections:
            return ((self.D, self.MY_CHILD1.C), (self.E, self.MY_CHILD2.MY_NODE1.A))

    class MyGraph(Graph):
        MY_COMPONENT: MyParentGroup

        def logging(self) -> Dict[str, Topic]:
            return {"D": self.MY_COMPONENT.D}

    MyGraph()

    expected_message = (
        "MyGraph has unused topics:\n"
        "\t- MY_COMPONENT/D has no publishers\n"
        "\t- MY_COMPONENT/E has no publishers\n"
        "\t- MY_COMPONENT/MY_CHILD1/C has no publishers\n"
        "\t- MY_COMPONENT/MY_CHILD1/MY_NODE1/A has no publishers\n"
        "\t- MY_COMPONENT/MY_CHILD1/MY_NODE2/B has no subscribers\n"
        "\t- MY_COMPONENT/MY_CHILD2/C has no publishers\n"
        "\t- MY_COMPONENT/MY_CHILD2/MY_NODE1/A has no publishers\n"
        "\t- MY_COMPONENT/MY_CHILD2/MY_NODE2/B has no subscribers\n"
        "This could mean that there are publishers and/or subscribers of Cthulhu "
        "streams that LabGraph doesn't know about, and/or that data in some topics is "
        "being discarded."
    )

    mock_logger.warning.assert_called_with(expected_message)


def test_complete_graph() -> None:
    """
    Tests that we are able to construct a valid graph where all the topics have
    publishers and subscribers.
    """

    class MyMessage(Message):
        int_field: int
        str_field: str

    class MySource(Node):
        A = Topic(MyMessage)

        @publisher(A)
        def my_publisher(self) -> AsyncPublisher:
            pass

    class MyTransformer(Node):
        B = Topic(MyMessage)
        C = Topic(MyMessage)

        @subscriber(B)
        @publisher(C)
        def my_transformer(self, message: MyMessage) -> AsyncPublisher:
            pass

    class MySink(Node):
        D = Topic(MyMessage)

        @subscriber(D)
        def my_subscriber(self, message: MyMessage) -> None:
            pass

    class MyGraph(Graph):
        MY_SOURCE: MySource
        MY_TRANSFORMER: MyTransformer
        MY_SINK: MySink

        def connections(self) -> Connections:
            return (
                (self.MY_SOURCE.A, self.MY_TRANSFORMER.B),
                (self.MY_TRANSFORMER.C, self.MY_SINK.D),
            )

    MyGraph()
