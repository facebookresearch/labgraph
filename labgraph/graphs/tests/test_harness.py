#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import dataclasses

import pytest

from ...messages.message import Message
from ..config import Config
from ..method import AsyncPublisher, publisher, subscriber
from ..node import Node
from ..node_test_harness import NodeTestHarness, run_async, run_with_harness
from ..state import State
from ..topic import Topic


NUM_MESSAGES = 10


class MyMessage(Message):
    my_field: int


class MyConfig(Config):
    my_field: int


class MyState(State):
    counter: int


class MyNode(Node):
    config: MyConfig
    state: MyState

    A = Topic(MyMessage)
    B = Topic(MyMessage)

    def setup(self) -> None:
        # Some simple state we can set to check that setup() executed
        self.other_state: int = 5

    # A simple publisher
    @publisher(A)
    async def my_publisher(self) -> AsyncPublisher:
        for i in range(NUM_MESSAGES):
            yield self.A, MyMessage(my_field=i)

    # A simple subscriber that updates state (used by the test to check it ran)
    @subscriber(B)
    async def my_subscriber(self, message: MyMessage) -> None:
        self.state.counter = message.my_field

    def cleanup(self) -> None:
        # Update the state so we can check cleanup() ran
        self.other_state = 6


def test_get_node() -> None:
    """
    Test NodeTestHarness.get_node()
    """
    harness = NodeTestHarness(MyNode)
    with harness.get_node(
        config=MyConfig(1), state=MyState(counter=-1)  # type: ignore
    ) as node:  # type: ignore
        # Ensure node is of correct type
        assert isinstance(node, MyNode)
        # Check the node has its config set
        assert node.config.asdict() == {"my_field": 1}
        # Check the node has its state set
        assert dataclasses.asdict(node.state) == {"counter": -1}
        # Check the node ran setup()
        assert node.other_state == 5

    # Check the node ran cleanup() after leaving the with block
    assert node.other_state == 6


def test_run_async() -> None:
    """
    Test run_async()
    """
    harness = NodeTestHarness(MyNode)
    with harness.get_node(
        config=MyConfig(1), state=MyState(counter=-1)  # type: ignore
    ) as node:  # type: ignore
        # Run the async publisher function and assert its yielded messages
        publish_result = run_async(node.my_publisher)
        assert len(publish_result) == NUM_MESSAGES
        assert [message.asdict() for _, message in publish_result] == [
            {"my_field": i} for i in range(NUM_MESSAGES)
        ]

        # Run the async subscriber function
        run_async(node.my_subscriber, args=[MyMessage(my_field=20)])  # type: ignore
        # Assert that the subscriber function ran
        assert node.state.counter == 20


def test_run_with_harness() -> None:
    """
    Test run_with_harness()
    """
    publish_result = run_with_harness(
        MyNode,
        MyNode.my_publisher,
        config=MyConfig(1),
        state=MyState(counter=1),  # type: ignore
    )
    assert len(publish_result) == NUM_MESSAGES
    assert [message.asdict() for _, message in publish_result] == [
        {"my_field": i} for i in range(NUM_MESSAGES)
    ]


def test_run_with_harness_max_num_results() -> None:
    """
    Test passing max_num_results to run_with_harness
    """
    publish_result = run_with_harness(
        MyNode,
        MyNode.my_publisher,
        config=MyConfig(1),
        state=MyState(counter=1),  # type: ignore
        max_num_results=1,
    )
    assert len(publish_result) == 1

    # Check that using max_num_results with a non-generator raises
    with pytest.raises(TypeError):
        run_with_harness(MyNode, _not_a_generator, max_num_results=1)  # type: ignore


def test_run_async_max_num_results() -> None:
    """
    Test passing max_num_results to run_async
    """
    harness = NodeTestHarness(MyNode)
    with harness.get_node(
        config=MyConfig(1), state=MyState(counter=-1)  # type: ignore
    ) as node:  # type: ignore
        publish_result = run_async(node.my_publisher, max_num_results=1)
        assert len(publish_result) == 1

    # Check that using max_num_results with a non-generator raises
    with pytest.raises(TypeError):
        run_async(_not_a_generator, max_num_results=1)  # type: ignore


async def _not_a_generator() -> None:
    pass
