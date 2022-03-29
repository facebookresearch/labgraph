#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from typing import Tuple
from labgraph.websockets.ws_server.ws_api_node_server import (
    WSAPIServerConfig,
    WSAPIServerNode
)
from .serializer_node import SerializerConfig, Serializer
from ..aliases.aliases import SerializedGraph
from .enums.enums import ENUMS

APP_ID = 'LABGRAPH_MONITOR'
WS_SERVER = ENUMS.WS_SERVER
STREAM = ENUMS.STREAM
DEFAULT_IP = WS_SERVER.DEFAULT_IP
DEFAULT_PORT = WS_SERVER.DEFAULT_PORT
DEFAULT_API_VERSION = WS_SERVER.DEFAULT_API_VERSION
SAMPLE_RATE = 5


def run_topology(data: SerializedGraph) -> None:
    """
    A function that creates a Websocket server graph.
    The server graph streams the lagraph topology to the clients
    """
    class WSSenderNode(lg.Graph):
        SERIALIZER: Serializer
        WS_SERVER_NODE: WSAPIServerNode

        def setup(self) -> None:
            wsapi_server_config = WSAPIServerConfig(
                app_id=APP_ID,
                ip=WS_SERVER.DEFAULT_IP,
                port=ENUMS.WS_SERVER.DEFAULT_PORT,
                api_version=ENUMS.WS_SERVER.DEFAULT_API_VERSION,
                num_messages=-1,
                enums=ENUMS(),
                sample_rate=SAMPLE_RATE,
            )
            self.SERIALIZER.configure(
                SerializerConfig(
                    data=data,
                    sample_rate=SAMPLE_RATE,
                    stream_name=STREAM.LABGRAPH_MONITOR,
                    stream_id=STREAM.LABGRAPH_MONITOR_ID
                )
            )
            self.WS_SERVER_NODE.configure(wsapi_server_config)

        def connections(self) -> lg.Connections:
            return ((self.SERIALIZER.TOPIC, self.WS_SERVER_NODE.topic),)

        def process_modules(self) -> Tuple[lg.Module, ...]:
            return (self.SERIALIZER, self.WS_SERVER_NODE, )

    lg.run(WSSenderNode)
