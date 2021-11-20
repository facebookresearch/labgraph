#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import time
from typing import List

import websockets

from ...graphs import Config, Topic, subscriber
from ...graphs.method import main, background
from ...runners import NormalTermination
from ...util.logger import get_logger
from .api.api_stream_descendant import ApiStreamDesc
from .api.ws_api_message_constructor import (
    get_sample_data,
)
from .ws_node_server import WSServerNode
from .ws_server_stream_message import WSStreamMessage


logger = get_logger(__name__)


class WSAPIServerConfig(Config):
    app_id: str
    ip: str
    port: int
    api_version: str
    enums: object
    # When num_messages > 0, Server will be terminated after receiving
    # num_messages number of messages.
    num_messages: int = -1
    batch_size: int = 1
    sample_rate: int = 100
    ws_server_wait_time: float = 0.01


class WSAPIServerNode(WSServerNode):
    """
    Represents a node in the graph which serves as a WebSocket API server.

    Args:
        client: The websocket client which handles websocket request.
    """

    topic = Topic(WSStreamMessage)
    output = Topic(WSStreamMessage)
    wsServer = None
    session = None
    config: WSAPIServerConfig

    @main
    def main_loop(self) -> None:
        super().main_loop()

    def setup(self):
        super().setup()
        self.num_messages = self.config.num_messages
        self.num_received = 0
        if self.num_messages > 0:
            self.should_terminate = True
        else:
            self.should_terminate = False
        self.batch_size = self.config.batch_size

        # List of streams which have established websocket connections.
        self.first_ws_activated = []
        # List of streams which have received at least one message from upstream node.
        self.first_received_streams = []
        self.terminated = False

    def create_batch_samples(self, sample_data, batch_size: int = 1) -> List:
        samples = []
        for _ in range(batch_size):
            samples.append(
                get_sample_data(
                    data=sample_data,
                    produced_timestamp_s=time.time(),
                )
            )
        return samples

    @background
    async def termination_background(self) -> None:
        while self.num_messages == -1 or self.num_received < self.num_messages:
            await asyncio.sleep(1 / self.config.sample_rate)
        self.terminated = True
        logger.info("NormalTermination is being raised")
        raise NormalTermination()

    @subscriber(topic)
    async def ws_server_publisher(self, message: WSStreamMessage) -> None:
        stream_name = message.stream_name

        if stream_name not in self.first_received_streams:
            logger.info(f"Received first message from stream_name: {stream_name}")
            self.first_received_streams.append(stream_name)
        if self.should_terminate:
            self.num_received += 1
            return

        stream_name = message.stream_name
        stream_id = message.stream_id

        while self.wsServer is None or not self.wsServer.isactive(stream_name):
            await asyncio.sleep(self.config.ws_server_wait_time)
        if stream_name not in self.first_received_streams:
            logger.info(f"Stream {stream_name} has been activated.")
            self.first_received_streams.append(stream_name)

        stream_desc = ApiStreamDesc(
            stream_name=stream_name,
            stream_id=stream_id,
        )
        self.session.add_stream(stream_desc=stream_desc)

        if self.wsServer.isactive(stream_name):
            samples = self.create_batch_samples(
                sample_data=message.samples,
                batch_size=self.batch_size,
            )

            try:
                send_samples_success = await self.session.send_samples(
                    samples=samples,
                    stream_name=stream_name,
                )
            except websockets.exceptions.ConnectionClosedError:
                send_samples_success = False

            if not send_samples_success:
                logger.info("Removing Session Stream...")
                self.session.remove_stream(stream_desc)
                logger.info("Removing Stream from WS Server...")
                self.wsServer.remove_stream(stream_name)

        await asyncio.sleep(1 / self.config.sample_rate)
