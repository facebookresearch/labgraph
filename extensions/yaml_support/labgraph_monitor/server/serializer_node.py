#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
import asyncio
from labgraph.websockets.ws_server.ws_server_stream_message import (
    WSStreamMessage
)
from ..aliases.aliases import SerializedGraph


class SerializerConfig(lg.Config):
    data: SerializedGraph
    sample_rate: int
    stream_name: str
    stream_id: str


class Serializer(lg.Node):
    """
    Convenience node for sending messages to a `WSAPIServerNode`.
    """

    TOPIC = lg.Topic(WSStreamMessage)
    config: SerializerConfig

    @lg.publisher(TOPIC)
    async def source(self) -> lg.AsyncPublisher:
        await asyncio.sleep(.01)
        while True:
            msg = WSStreamMessage(
                samples=self.config.data,
                stream_name=self.config.stream_name,
                stream_id=self.config.stream_id,
            )
            yield self.TOPIC, msg
            await asyncio.sleep(1 / self.config.sample_rate)
