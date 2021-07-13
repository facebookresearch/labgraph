#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from typing import Any

import pytest

from ...graphs import AsyncPublisher, Topic
from ...graphs.method import get_method_metadata
from ...messages import Message
from .. import BaseEventGenerator, BaseEventGeneratorNode, EventPublishingHeap


pytest_plugins = ["pytest_mock"]


class MyMessage(Message):
    my_field: str


class MyBaseEventGenerator(BaseEventGenerator):
    def __init__(self) -> None:
        self.heap = EventPublishingHeap()

    def generate_events(self) -> EventPublishingHeap:
        return self.heap

    def set_topics(self) -> None:
        pass


class MyBaseEventGeneratorNode(BaseEventGeneratorNode):

    MY_TOPIC = Topic(MyMessage)

    async def publish_events(self) -> AsyncPublisher:
        return await super().publish_events()


@pytest.fixture
def event_loop():  # type: ignore
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def test_base_event_generator_node_meta(mocker: Any) -> None:
    node = MyBaseEventGeneratorNode()
    publisher_metadata = get_method_metadata(node.publish_events)
    topic = publisher_metadata.published_topics[0]
    assert topic.name == node.MY_TOPIC.name
    assert topic.message_type == node.MY_TOPIC.message_type


def test_base_event_generator_node_init(mocker: Any) -> None:
    mock_time = mocker.patch(
        "labgraph.events.event_generator_node.time"
    )
    mock_time.return_value = 0.0
    node = MyBaseEventGeneratorNode()
    assert node._start_time == 0.0


def test_base_event_generator_node_elapsed(mocker: Any) -> None:
    mock_time = mocker.patch(
        "labgraph.events.event_generator_node.time"
    )
    mock_time.side_effect = [0.0, 1.0]
    node = MyBaseEventGeneratorNode()
    assert node._time_elapsed_since_start() == 1.0


def test_base_event_generator_node_generator(mocker: Any) -> None:
    generator = MyBaseEventGenerator()
    node = MyBaseEventGeneratorNode()
    node.setup_generator(generator)
    assert node._generator == generator
    assert node.generate_events() == generator.heap


def test_base_event_generator_node_publish(event_loop: Any, mocker: Any) -> None:
    node = MyBaseEventGeneratorNode()
    with pytest.raises(NotImplementedError):
        _ = event_loop.run_until_complete(node.publish_events())
