#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import uuid
from typing import List, Optional, Mapping, Union

from ...util.logger import get_logger
from .api_message_constructor import (
    get_start_stream_request,
    get_end_stream_request,
)
from .ws_poller_node import (
    WSPollerNode,
    WSPollerConfig,
    WSConnectionType,
)


logger = get_logger(__name__)

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 9000
MOST_RECENT_API_VERSION = "0.1"


class STREAMWSPollerConfig(WSPollerConfig):
    streams: List[str]
    stream_ids: Optional[Union[List[str]]] = None
    ip: str = DEFAULT_IP
    port: int = DEFAULT_PORT
    api_version: str = MOST_RECENT_API_VERSION


class STREAMWSPollerNode(WSPollerNode):
    """
    Represents a node in the graph which polls data from WebSocket.
    Data polled from WebSocket are subsequently pushed to the rest of the
    graph as a WSMessage.

    Args:
        streams: The list of websocket streams to interface with.
        stream_ids:
            The list of stream_ids to assign each stream. If not provided,
            streams are assigned an auto-generated id: '<stream name>-<uuid>'.
    """

    config: STREAMWSPollerConfig

    def setup(self) -> None:
        super().setup()

        streams = self.streams = self.config.streams
        stream_ids = self.stream_ids = self.config.stream_ids

        if stream_ids is None:
            stream_ids = [f"{s}-{uuid.uuid1()}" for s in streams]

        if len(streams) != len(stream_ids):
            raise ValueError(
                "Number of streams and stream_ids must match: '%s' vs '%s'",
                len(streams),
                len(stream_ids),
            )

        if len(streams) == 0:
            raise ValueError("Empty list of streams requested for '%s'.", self.app_id)

        self.streams: Mapping[str, str] = {
            stream: stream_id for stream, stream_id in zip(streams, stream_ids)
        }

    async def start_streams(self, ws: WSConnectionType):
        for request_id, (stream_name, stream_id) in enumerate(self.streams.items()):
            msg = get_start_stream_request(
                target=stream_name,
                stream_id=stream_id,
                request_id=request_id,
                api_version=self.api_version,
                app_id=self.app_id,
            )

            await super().start_streams(ws, msg)

    async def end_streams(self, ws: WSConnectionType):
        logger.info("Streams are going to be ended.")
        # Handle cleanly stopping each stream upon stream app close.
        for request_id, (_, stream_id) in enumerate(self.streams.items()):
            msg = get_end_stream_request(
                stream_id=stream_id, request_id=request_id, api_version=self.api_version
            )
            # Send StopStream request for target_name stream.
            await super().end_streams(ws, msg)

    def __str__(self):
        if isinstance(self.config.streams, dict):
            streams = f"{self.config.streams.keys()}"
        else:
            streams = f"{self.config.streams}"
        return f"{self.config.app_id} ({streams})"

    def get_stream_id(self, stream_name) -> str:
        if stream_name not in self.streams:
            raise ValueError("Requested stream name not found: '%s'", stream_name)
        return self.streams[stream_name]
