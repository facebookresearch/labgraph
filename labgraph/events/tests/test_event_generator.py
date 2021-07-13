#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any

import pytest

from ...graphs import Topic
from ...messages import Message, TimestampedMessage
from ...util.error import LabGraphError
from .. import (
    BaseEventGenerator,
    DeferredMessage,
    Event,
    EventGraph,
    EventPublishingHeap,
)


pytest_plugins = ["pytest_mock"]


class MyMessage(Message):
    args_field: str
    kwargs_field: str


class MyTimestampedMessage(TimestampedMessage):
    args_field: str
    kwargs_field: str


class MyBaseEventGenerator(BaseEventGenerator):
    def generate_events(self) -> EventPublishingHeap:
        return super().generate_events()

    def set_topics(self) -> None:
        super().set_topics()


def test_deferred_message_init(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    assert message._message_type == MyMessage
    assert message._args == ("unittest_args",)
    assert message._kwargs == {"kwargs_field": "unittest_kwargs"}
    assert message._message is None


def test_deferred_message_build_regular(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    built = message.build_message()
    assert not hasattr(message, "_args")
    assert not hasattr(message, "_kwargs")
    assert isinstance(built, MyMessage)
    expected = MyMessage("unittest_args", kwargs_field="unittest_kwargs")
    assert built == expected


def test_deferred_message_build_timestamped(mocker: Any) -> None:
    mock_time = mocker.patch("labgraph.events.event_generator.time")
    mock_time.time.return_value = 0.0
    message = DeferredMessage(
        MyTimestampedMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    built = message.build_message()
    assert not hasattr(message, "_args")
    assert not hasattr(message, "_kwargs")
    assert isinstance(built, MyTimestampedMessage)
    expected = MyTimestampedMessage(
        0.0, "unittest_args", kwargs_field="unittest_kwargs"
    )
    assert built == expected


def test_event_init(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    event = Event(message, topic, 0.0)
    assert event._message == message
    assert event.topic == topic
    assert event.delay == 0.0
    assert event.duration == 0.0


def test_event_init_negative_duration(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    with pytest.raises(LabGraphError):
        _ = Event(message, topic, 0.0, -1.0)


def test_event_build_message(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    event = Event(message, topic, 0.0)
    expected = MyMessage("unittest_args", kwargs_field="unittest_kwargs")
    assert event.message == expected


def test_event_graph_init(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    event = Event(message, topic, 0.0)
    graph = EventGraph(event)
    assert len(graph.heap) == 1
    assert graph.last_event_added == event


def test_event_graph_init_bad_start_event(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    event = Event(message, topic, -1.0)
    with pytest.raises(LabGraphError):
        _ = EventGraph(event)


def test_event_graph_accumulated_time(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    start = Event(message, topic, 0.0, 1.0)
    graph = EventGraph(start)
    parent = Event(message, topic, 0.0, 1.0)
    child_1 = Event(message, topic, -0.5, 1.0)
    child_2 = Event(message, topic, -0.5, 1.0)
    graph.add_event_at_end(parent, start)
    graph.add_event_at_start(child_1, parent)
    graph.add_event_at_start(child_2, parent)
    entries = []
    while graph.heap:
        entries.append(graph.heap.pop())
    expected = [(0.0, 0, start), (0.5, 2, child_1), (0.5, 3, child_2), (1.0, 1, parent)]
    assert entries == expected


def test_event_graph_accumulated_time_no_previous(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    start = Event(message, topic, 0.0, 1.0)
    graph = EventGraph(start)
    parent = Event(message, topic, 0.0, 1.0)
    child = Event(message, topic, 0.0, 1.0)
    with pytest.raises(LabGraphError):
        graph.add_event_at_end(child, parent)


def test_event_graph_accumulated_time_before_start(mocker: Any) -> None:
    message = DeferredMessage(
        MyMessage, "unittest_args", kwargs_field="unittest_kwargs"
    )
    topic = Topic(MyMessage)
    start = Event(message, topic, 0.0, 1.0)
    graph = EventGraph(start)
    parent = Event(message, topic, 0.0, 1.0)
    child = Event(message, topic, -3.0, 1.0)
    graph.add_event_at_end(parent, start)
    with pytest.raises(LabGraphError):
        graph.add_event_at_end(child, parent)


def test_base_event_generator_abc(mocker: Any) -> None:
    generator = MyBaseEventGenerator()
    with pytest.raises(NotImplementedError):
        _ = generator.generate_events()
    with pytest.raises(NotImplementedError):
        generator.set_topics()
