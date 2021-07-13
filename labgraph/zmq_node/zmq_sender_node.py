#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio

import zmq
import zmq.asyncio
from zmq.utils.monitor import parse_monitor_message

from ..graphs import Config, Node, Topic, background, subscriber
from ..util.logger import get_logger
from ..zmq_node import ZMQMessage
from .constants import ZMQEvent


STARTUP_WAIT_TIME = 0.1

logger = get_logger(__name__)


class ZMQSenderConfig(Config):
    write_addr: str
    zmq_topic: str


class ZMQSenderNode(Node):
    """
    Represents a node in a LabGraph graph that subscribes to messages in a
    LabGraph topic and forwards them by writing to a ZMQ socket.

    Args:
        write_addr: The address to which ZMQ data should be written.
        zmq_topic: The ZMQ topic being sent.
    """

    topic = Topic(ZMQMessage)
    config: ZMQSenderConfig

    def setup(self) -> None:
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.monitor = self.socket.get_monitor_socket()
        logger.debug(f"{self}:binding to {self.config.write_addr}")
        self.socket.bind(self.config.write_addr)
        self.has_subscribers = False

    def cleanup(self) -> None:
        self.socket.close()

    @background
    async def _socket_monitor(self) -> None:
        while True:
            monitor_result = await self.monitor.poll(100, zmq.POLLIN)
            if monitor_result:
                data = await self.monitor.recv_multipart()
                evt = parse_monitor_message(data)

                event = ZMQEvent(evt["event"])
                logger.debug(f"{self}:{event.name}")

                if event == ZMQEvent.EVENT_ACCEPTED:
                    logger.debug(f"{self}:subscriber joined")
                    self.has_subscribers = True
                elif event in (
                    ZMQEvent.EVENT_DISCONNECTED,
                    ZMQEvent.EVENT_MONITOR_STOPPED,
                    ZMQEvent.EVENT_CLOSED,
                ):
                    break

    @subscriber(topic)
    async def zmq_subscriber(self, message: ZMQMessage) -> None:
        while not self.has_subscribers:
            await asyncio.sleep(STARTUP_WAIT_TIME)
        await self.socket.send_multipart(
            (bytes(self.config.zmq_topic, "UTF-8"), message.data), flags=zmq.NOBLOCK
        )
