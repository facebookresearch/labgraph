#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import os
import time
from multiprocessing import Process
from typing import List, Sequence

import pytest
import zmq

from ...graphs import (
    AsyncPublisher,
    Config,
    Connections,
    Graph,
    Module,
    Node,
    Topic,
    publisher,
    subscriber,
)
from ...runners import LocalRunner, NormalTermination, ParallelRunner
from ...util.testing import get_free_port, get_test_filename, local_test
from ..zmq_message import ZMQMessage
from ..zmq_poller_node import ZMQPollerConfig, ZMQPollerNode
from ..zmq_sender_node import ZMQSenderConfig, ZMQSenderNode


NUM_MESSAGES = 5
SAMPLE_RATE = 10
STARTUP_TIME = 1

ZMQ_ADDR = "tcp://127.0.0.1"
ZMQ_TOPIC = "zmq_topic"

DATA_DELIMITER = b"\0"


class MySinkConfig(Config):
    output_filename: str


class MySink(Node):
    """
    Convenience node for receiving messages from a `ZMQPollerNode`.
    """

    TOPIC = Topic(ZMQMessage)
    config: MySinkConfig

    def setup(self) -> None:
        self.output_file = open(self.config.output_filename, "wb")
        self.num_received = 0

    @subscriber(TOPIC)
    async def sink(self, message: ZMQMessage) -> None:
        self.output_file.write(message.data)
        self.output_file.write(DATA_DELIMITER)

        self.num_received += 1
        if self.num_received == NUM_MESSAGES:
            raise NormalTermination()

    def cleanup(self) -> None:
        self.output_file.close()


class MySourceConfig(Config):
    should_terminate: bool = True


class MySource(Node):
    """
    Convenience node for sending messages to a `ZMQSenderNode`.
    """

    TOPIC = Topic(ZMQMessage)
    config: MySourceConfig
    samples = [bytes([i]) for i in range(1, NUM_MESSAGES + 1)]

    @publisher(TOPIC)
    async def source(self) -> AsyncPublisher:
        for sample_bytes in self.samples:
            yield self.TOPIC, ZMQMessage(sample_bytes)
            await asyncio.sleep(1 / SAMPLE_RATE)

        if self.config.should_terminate:
            raise NormalTermination()


def write_samples_to_zmq(address: str, samples: Sequence[bytes], topic: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(address)

    # NOTE: In place of waiting on a monitor socket, we wait for a startup time
    # here. Otherwise we would need to listen on an extra socket in this function,
    # increasing the complexity of this test. If this startup wait becomes flaky, we may
    # want to consider adding the monitor socket here.
    time.sleep(STARTUP_TIME)
    for sample_bytes in samples:
        socket.send_multipart((bytes(topic, "UTF-8"), sample_bytes))
        time.sleep(1 / SAMPLE_RATE)
    socket.close()


def recv_samples_from_zmq(address: str, topic: str, output_fname: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, bytes(topic, "UTF-8"))
    socket.connect(address)

    with open(output_fname, "bw") as output_file:
        for _ in range(NUM_MESSAGES):
            received = socket.recv_multipart()
            topic, data = received
            output_file.write(data)
            output_file.write(DATA_DELIMITER)
    socket.close()


@local_test
def test_zmq_poller_node() -> None:
    """
    Tests that a `ZMQPollerNode` is able to read samples from a ZMQ socket and echo
    the samples back out of the graph.
    """

    class MyZMQPollerGraphConfig(Config):
        read_addr: str
        zmq_topic: str
        output_filename: str

    class MyZMQPollerGraph(Graph):
        MY_SOURCE: ZMQPollerNode
        MY_SINK: MySink
        config: MyZMQPollerGraphConfig

        def setup(self) -> None:
            self.MY_SOURCE.configure(
                ZMQPollerConfig(
                    read_addr=self.config.read_addr, zmq_topic=self.config.zmq_topic
                )
            )
            self.MY_SINK.configure(
                MySinkConfig(output_filename=self.config.output_filename)
            )

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.topic, self.MY_SINK.TOPIC),)

    graph = MyZMQPollerGraph()
    output_filename = get_test_filename()
    address = f"{ZMQ_ADDR}:{get_free_port()}"
    graph.configure(
        MyZMQPollerGraphConfig(
            read_addr=address, zmq_topic=ZMQ_TOPIC, output_filename=output_filename
        )
    )
    runner = LocalRunner(module=graph)

    samples = [bytes([i]) for i in range(1, NUM_MESSAGES + 1)]
    p = Process(target=write_samples_to_zmq, args=(address, samples, ZMQ_TOPIC))
    p.start()
    runner.run()
    p.join()

    with open(output_filename, "br") as f:
        data = f.read()
    assert set(samples) == set(data.strip(DATA_DELIMITER).split(DATA_DELIMITER))


@local_test
def test_zmq_sender_node() -> None:
    """
    Tests that a `ZMQSenderNode` is able to read samples from the graph and write the
    samples back out to a ZMQ socket.
    """

    class MyZMQSenderGraph(Graph):
        MY_SOURCE: MySource
        MY_SINK: ZMQSenderNode

        config: ZMQSenderConfig

        def setup(self) -> None:
            self.MY_SOURCE.configure(MySourceConfig())
            self.MY_SINK.configure(self.config)

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.TOPIC, self.MY_SINK.topic),)

    output_filename = get_test_filename()
    graph = MyZMQSenderGraph()
    address = f"{ZMQ_ADDR}:{get_free_port()}"
    graph.configure(ZMQSenderConfig(write_addr=address, zmq_topic=ZMQ_TOPIC))
    runner = LocalRunner(module=graph)

    p = Process(
        target=recv_samples_from_zmq, args=(address, ZMQ_TOPIC, output_filename)
    )
    p.start()
    runner.run()
    p.join()

    with open(output_filename, "br") as f:
        data = f.read()
    assert set(graph.MY_SOURCE.samples) == set(
        data.strip(DATA_DELIMITER).split(DATA_DELIMITER)
    )


@local_test
def test_zmq_send_and_poll() -> None:
    """
    Tests that a `ZMQSenderNode` and a `ZMQPollerNode` can work together.
    """

    class MyZMQGraphConfig(Config):
        addr: str
        zmq_topic: str
        output_filename: str

    class MyZMQGraph(Graph):
        DF_SOURCE: MySource
        ZMQ_SENDER: ZMQSenderNode
        ZMQ_POLLER: ZMQPollerNode
        DF_SINK: MySink

        def setup(self) -> None:
            self.DF_SOURCE.configure(MySourceConfig(should_terminate=False))
            self.ZMQ_SENDER.configure(
                ZMQSenderConfig(
                    write_addr=self.config.addr, zmq_topic=self.config.zmq_topic
                )
            )
            self.ZMQ_POLLER.configure(
                ZMQPollerConfig(
                    read_addr=self.config.addr, zmq_topic=self.config.zmq_topic
                )
            )
            self.DF_SINK.configure(
                MySinkConfig(output_filename=self.config.output_filename)
            )

        def connections(self) -> Connections:
            return (
                (self.DF_SOURCE.TOPIC, self.ZMQ_SENDER.topic),
                (self.ZMQ_POLLER.topic, self.DF_SINK.TOPIC),
            )

        def process_modules(self) -> Sequence[Module]:
            return (self.DF_SOURCE, self.ZMQ_SENDER, self.ZMQ_POLLER, self.DF_SINK)

    output_filename = get_test_filename()
    graph = MyZMQGraph()
    address = f"{ZMQ_ADDR}:{get_free_port()}"
    graph.configure(
        MyZMQGraphConfig(
            addr=address, zmq_topic=ZMQ_TOPIC, output_filename=output_filename
        )
    )
    runner = ParallelRunner(graph=graph)
    runner.run()

    with open(output_filename, "br") as f:
        data = f.read()
    assert set(graph.DF_SOURCE.samples) == set(
        data.strip(DATA_DELIMITER).split(DATA_DELIMITER)
    )
