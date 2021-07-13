#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import time
from typing import List

import pytest

from ...graphs.graph import Graph
from ...graphs.group import Connections
from ...graphs.method import AsyncPublisher, publisher, subscriber
from ...graphs.node import Node
from ...graphs.topic import Topic
from ...messages.message import TimestampedMessage
from ...util.testing import local_test
from ..aligner import TimestampAligner
from ..exceptions import NormalTermination
from ..parallel_runner import ParallelRunner
from ..runner import RunnerOptions


NUM_MESSAGES = 5
FAST_PUBLISH_RATE = 10
SLOW_PUBLISH_RATE = 1

SMALL_ALIGN_LAG = 0.01
LARGE_ALIGN_LAG = 5


class MyMessage1(TimestampedMessage):
    int_field: int


class MyMessage2(TimestampedMessage):
    int_field: int


class MySource1(Node):
    A = Topic(MyMessage1)

    @publisher(A)
    async def source(self) -> AsyncPublisher:
        latest = time.time()
        for i in reversed(range(NUM_MESSAGES)):
            yield self.A, MyMessage1(timestamp=latest - i, int_field=i)
            await asyncio.sleep(1 / SLOW_PUBLISH_RATE)


class MySource2(Node):
    A = Topic(MyMessage2)

    @publisher(A)
    async def source(self) -> AsyncPublisher:
        latest = time.time()
        for i in reversed(range(NUM_MESSAGES)):
            yield self.A, MyMessage2(timestamp=latest - i, int_field=i)
            await asyncio.sleep(1 / FAST_PUBLISH_RATE)


class MySink(Node):
    D = Topic(MyMessage1)
    E = Topic(MyMessage2)

    def setup(self) -> None:
        self.results: List[float] = []

    @subscriber(D)
    def sink1(self, message: MyMessage1) -> None:
        self.results.append(message.timestamp)
        if len(self.results) == 2 * NUM_MESSAGES:
            raise NormalTermination()

    @subscriber(E)
    def sink2(self, message: MyMessage2) -> None:
        self.results.append(message.timestamp)
        if len(self.results) == 2 * NUM_MESSAGES:
            raise NormalTermination()


class MyGraph(Graph):
    SOURCE1: MySource1
    SOURCE2: MySource2
    SINK: MySink

    def connections(self) -> Connections:
        return ((self.SOURCE1.A, self.SINK.D), (self.SOURCE2.A, self.SINK.E))


@local_test
@pytest.mark.skip("T70572430: Fix aligner tests")
def test_slow_align_interval() -> None:
    """
    Tests that when the default timestamp aligner is specified for a runner
    with insufficient time lag, the results from its streams should arrive in
    expected (not chronological) order.
    """

    graph = MyGraph()
    aligner = TimestampAligner(SMALL_ALIGN_LAG)
    runner = ParallelRunner(graph=graph, options=RunnerOptions(aligner=aligner))
    runner.run()

    assert len(graph.SINK.results) == NUM_MESSAGES * 2
    assert graph.SINK.results != sorted(graph.SINK.results)


@local_test
@pytest.mark.skip("T70572430: Fix aligner tests")
def test_align_two_streams() -> None:
    """
    Tests that when the default timestamp aligner is specified for a runner
    with sufficient time lag, the results from all its streams should arrive
    in chronological order.
    """

    graph = MyGraph()
    aligner = TimestampAligner(LARGE_ALIGN_LAG)
    runner = ParallelRunner(graph=graph, options=RunnerOptions(aligner=aligner))
    runner.run()

    assert len(graph.SINK.results) == NUM_MESSAGES * 2
    assert graph.SINK.results == sorted(graph.SINK.results)
