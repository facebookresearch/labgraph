#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio

import zmq
import zmq.asyncio
from zmq.utils.monitor import parse_monitor_message

from ..graphs import AsyncPublisher, Config, Node, Topic, background, publisher
from ..util.logger import get_logger
from ..zmq_node import ZMQMessage
from .constants import ZMQEvent


POLL_TIME = 0.1

logger = get_logger(__name__)


class ZMQPollerConfig(Config):
    read_addr: str
    zmq_topic: str
    poll_time: float = POLL_TIME


class ZMQPollerNode(Node):
    """
    Represents a node in the graph which polls data from ZMQ.
    Data polled from ZMQ are subsequently pushed to the rest of the
    graph as a ZMQMessage.

    Args:
        read_addr: The address from which ZMQ data should be polled.
        zmq_topic: The ZMQ topic being polled.
        timeout:
            The maximum amount of time (in seconds) that should be
            spent polling a ZMQ socket each time.  Defaults to
            FOREVER_POLL_TIME if not specified.
        exit_condition:
            An optional ZMQ event code specifying the event which,
            if encountered by the monitor, should signal the termination
            of this particular node's activity.
    """

    topic = Topic(ZMQMessage)
    config: ZMQPollerConfig

    def setup(self) -> None:
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.monitor = self.socket.get_monitor_socket()
        self.socket.connect(self.config.read_addr)
        self.socket.subscribe(self.config.zmq_topic)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.socket_open = False

    def cleanup(self) -> None:
        self.socket.close()

    @background
    async def socket_monitor(self) -> None:
        while True:
            monitor_result = await self.monitor.poll(100, zmq.POLLIN)
            if monitor_result:
                data = await self.monitor.recv_multipart()
                evt = parse_monitor_message(data)

                event = ZMQEvent(evt["event"])
                logger.debug(f"{self}:{event.name}")

                if event == ZMQEvent.EVENT_CONNECTED:
                    self.socket_open = True
                elif event == ZMQEvent.EVENT_CLOSED:
                    was_open = self.socket_open
                    self.socket_open = False
                    # ZMQ seems to be sending spurious CLOSED event when we
                    # try to connect before the source is running. Only give up
                    # if we were previously connected. If we give up now, we
                    # will never unblock zmq_publisher.
                    if was_open:
                        break
                elif event in (
                    ZMQEvent.EVENT_DISCONNECTED,
                    ZMQEvent.EVENT_MONITOR_STOPPED,
                ):
                    self.socket_open = False
                    break

    @publisher(topic)
    async def zmq_publisher(self) -> AsyncPublisher:
        # Wait for socket connection
        while not self.socket_open:
            await asyncio.sleep(POLL_TIME)

        while self.socket_open:
            poll_result = await self.socket.poll(
                self.config.poll_time * 1000, zmq.POLLIN
            )
            if poll_result:
                _, data = await self.socket.recv_multipart()
                yield self.topic, ZMQMessage(data)
