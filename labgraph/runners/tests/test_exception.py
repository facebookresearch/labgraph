#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Awaitable, Dict, Mapping, Sequence, Type

import pytest

from ...graphs.graph import Graph
from ...graphs.group import Connections
from ...graphs.method import AsyncPublisher, background, main, publisher, subscriber
from ...graphs.module import Module
from ...graphs.node import Node
from ...graphs.topic import Topic
from ...loggers.logger import Logger
from ...messages.message import Message
from ...runners.local_runner import LocalRunner
from ...runners.parallel_runner import LOGGER_KEY, ParallelRunner
from ...runners.runner import RunnerOptions
from ...util.testing import local_test
from ..process_manager import ProcessFailureType, ProcessManagerException


class MyTestException(Exception):
    pass


class MyTestMessage(Message):
    int_field: int


class MainThrowerNode(Node):
    @main
    def entry(self) -> None:
        raise MyTestException()


class BackgroundThrowerNode(Node):
    @background
    async def background(self) -> None:
        raise MyTestException()


class PublisherThrowerNode(Node):
    TOPIC = Topic(MyTestMessage)

    @publisher(TOPIC)
    async def publisher(self) -> AsyncPublisher:
        raise MyTestException()
        yield self.TOPIC, MyTestMessage(1)


class PublisherSubscriberThrowerNode(Node):
    TOPIC = Topic(MyTestMessage)

    @subscriber(TOPIC)
    async def subscriber(self, message: MyTestMessage) -> None:
        raise MyTestException()

    @publisher(TOPIC)
    async def publisher(self) -> AsyncPublisher:
        yield self.TOPIC, MyTestMessage(1)


MODULE_TYPES = (
    MainThrowerNode,
    BackgroundThrowerNode,
    PublisherThrowerNode,
    PublisherSubscriberThrowerNode,
)


@local_test
@pytest.mark.parametrize("module_type", MODULE_TYPES)  # type: ignore
def test_local_throw(module_type: Type[Node]) -> None:
    node = module_type()
    runner = LocalRunner(module=node)
    with pytest.raises(MyTestException):
        runner.run()


class SubscriberNode(Node):
    TOPIC = Topic(MyTestMessage)

    @subscriber(TOPIC)
    async def subscriber(self, message: MyTestMessage) -> None:
        pass


class PublisherThrowerGraph(Graph):
    PUBLISHER: PublisherThrowerNode
    SUBSCRIBER: SubscriberNode

    def connections(self) -> Connections:
        return ((self.PUBLISHER.TOPIC, self.SUBSCRIBER.TOPIC),)

    def process_modules(self) -> Sequence[Module]:
        return (self.PUBLISHER, self.SUBSCRIBER)


class SubscriberThrowerNode(Node):
    TOPIC = Topic(MyTestMessage)

    @subscriber(TOPIC)
    async def subscriber(self, message: MyTestMessage) -> None:
        raise MyTestException()


class PublisherNode(Node):
    TOPIC = Topic(MyTestMessage)

    @publisher(TOPIC)
    async def publisher(self) -> AsyncPublisher:
        yield self.TOPIC, MyTestMessage(1)


class SubscriberThrowerGraph(Graph):
    PUBLISHER: PublisherNode
    SUBSCRIBER: SubscriberThrowerNode

    def connections(self) -> Connections:
        return ((self.PUBLISHER.TOPIC, self.SUBSCRIBER.TOPIC),)

    def process_modules(self) -> Sequence[Module]:
        return (self.PUBLISHER, self.SUBSCRIBER)


class MainThrowerGraph(Graph):
    PUBLISHER: PublisherNode
    SUBSCRIBER: SubscriberNode
    MAIN: MainThrowerNode

    def connections(self) -> Connections:
        return ((self.PUBLISHER.TOPIC, self.SUBSCRIBER.TOPIC),)

    def process_modules(self) -> Sequence[Module]:
        return (self.PUBLISHER, self.SUBSCRIBER, self.MAIN)


class BackgroundThrowerGraph(Graph):
    PUBLISHER: PublisherNode
    SUBSCRIBER: SubscriberNode
    BACKGROUND: BackgroundThrowerNode

    def connections(self) -> Connections:
        return ((self.PUBLISHER.TOPIC, self.SUBSCRIBER.TOPIC),)

    def process_modules(self) -> Sequence[Module]:
        return (self.PUBLISHER, self.SUBSCRIBER, self.BACKGROUND)


GRAPH_TYPES = (
    PublisherThrowerGraph,
    SubscriberThrowerGraph,
    MainThrowerGraph,
    BackgroundThrowerGraph,
)


@local_test
@pytest.mark.parametrize("graph_type", GRAPH_TYPES)  # type: ignore
def test_parallel_throw(graph_type: Type[Graph]) -> None:
    graph = graph_type()
    runner = ParallelRunner(graph=graph)
    with pytest.raises(ProcessManagerException) as ex:
        runner.run()
    assert [f for f in ex.value.failures.values() if f is not None] == [
        ProcessFailureType.EXCEPTION
    ]


class PublisherSubscriberGraph(Graph):
    PUBLISHER: PublisherNode
    SUBSCRIBER: SubscriberNode

    def connections(self) -> Connections:
        return ((self.PUBLISHER.TOPIC, self.SUBSCRIBER.TOPIC),)

    def logging(self) -> Dict[str, Topic]:
        return {"topic": self.PUBLISHER.TOPIC}

    def process_modules(self) -> Sequence[Module]:
        return (self.PUBLISHER, self.SUBSCRIBER)


class ThrowerLogger(Logger):
    def write(self, messages_by_logging_id: Mapping[str, Sequence[Message]]) -> None:
        raise MyTestException()


@local_test
def test_logger_throw() -> None:
    graph = PublisherSubscriberGraph()
    runner = ParallelRunner(
        graph=graph, options=RunnerOptions(logger_type=ThrowerLogger)
    )
    with pytest.raises(ProcessManagerException) as ex:
        runner.run()

    assert ex.value.failures == {
        LOGGER_KEY: ProcessFailureType.EXCEPTION,
        "PUBLISHER": None,
        "SUBSCRIBER": None,
    }
    assert ex.value.exceptions[LOGGER_KEY] == "MyTestException()"
