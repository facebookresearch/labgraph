#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from asyncio import get_event_loop
from typing import Any

import websockets

from ...graphs import AsyncPublisher, Config, Node, Topic, publisher
from ...util.logger import get_logger
from .ws_client_message import WSMessage


logger = get_logger(__name__)
WSConnectionType = Any
WSConnectType = Any


class WSPollerConfig(Config):
    app_id: str
    ip: str
    port: int
    api_version: str


class WSPollerNode(Node):
    """
    Represents a node in the graph which polls data from WebSocket.
    Data polled from WebSocket are subsequently pushed to the rest of the
    graph as a WSMessage.

    Args:
        app_id: Websocket Name.
        ip: IP Address of websocket subscribtion.
        port: Port Address of websocket subscribtion.
        api_version: WebSocket API Version.
    """

    topic = Topic(WSMessage)
    config: WSPollerConfig

    async def start_streams(self, ws: WSConnectionType, msg: str):
        await ws.send(msg)
        try:
            # Receive API Event in response.
            await ws.recv()
        except websockets.ConnectionClosed:
            print("Websocket Connection Terminated")
            return

    async def end_streams(self, ws: WSConnectionType, msg: str):
        # Send StopStream request.
        await ws.send(msg)

    def __enter__(self):
        return get_event_loop().run_until_complete(self.__aenter__())

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return get_event_loop().run_until_complete(
            self.__aexit__(exc_type, exc_val, exc_tb)
        )

    async def connect(self) -> None:
        self._ctx = websockets.connect(self.url)
        self.ws = await self._ctx.__aenter__()

    async def start_streaming(self) -> None:
        await self.start_streams(self.ws)

    async def end_streaming(self, exc_type, exc_val, exc_tb) -> None:
        await self.end_streams(self.ws)
        if self._ctx is not None:
            await self._ctx.__aexit__(exc_type, exc_val, exc_tb)

    def get_next(self):
        """Return the next message synchronously."""
        return get_event_loop().run_until_complete(self.aget_next())

    async def aget_next(self, ws: WSConnectionType):
        """Coroutine for receiving and parsing incoming stream messages."""
        return await ws.recv()

    def recv(self) -> Any:
        return get_event_loop().run_until_complete(self.arecv())

    async def arecv(self) -> Any:
        res = await self.ws.recv()
        self.num_processed_messages += 1
        return res

    def setup(self) -> None:
        self._ip = self.config.ip
        self._port = self.config.port
        self.app_id = self.config.app_id
        self.api_version = self.config.api_version

        self.ws: Any = None
        self._ctx: Any = None
        self.url = f"ws://{self._ip}:{self._port}"

        self.shutdown = False

    def cleanup(self) -> None:
        self.shutdown = True

    @publisher(topic)
    async def ws_publisher(self) -> AsyncPublisher:
        await self.connect()
        await self.start_streaming()

        while not self.shutdown:
            message = await self.aget_next(self.ws)
            yield self.topic, WSMessage(message)

        get_event_loop().run_until_complete(self.end_streaming())
