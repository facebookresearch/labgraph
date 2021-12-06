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