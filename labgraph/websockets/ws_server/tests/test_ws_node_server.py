#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ....graphs.node_test_harness import NodeTestHarness, run_async
from ..ws_api_node_server import WSAPIServerConfig, WSAPIServerNode
from ..ws_server_stream_message import WSStreamMessage
from .enums import ENUMS
from .test_data import sample_stream_mock_data


NUM_MESSAGES = 5
SAMPLE_RATE = 10
STARTUP_TIME = 1

DATA_DELIMITER = b"\0"

WS_SERVER = ENUMS.WS_SERVER
MOCK = ENUMS.MOCK
STREAM = ENUMS.STREAM
DEFAULT_IP = WS_SERVER.DEFAULT_IP
DEFAULT_PORT = WS_SERVER.DEFAULT_PORT
DEFAULT_API_VERSION = WS_SERVER.DEFAULT_API_VERSION
DEFAULT_MOCK_STREAM_NAMES = MOCK.DEFAULT_MOCK_STREAM_NAMES
DEFAULT_MOCK_STREAM_IDS = MOCK.DEFAULT_MOCK_STREAM_IDS


class TestWSServerNode:
    def test_wsapi_server_node(self) -> None:
        # Setting up node
        wsapi_server_config = WSAPIServerConfig(
            app_id="test_WSAPIServerNode:",
            ip=DEFAULT_IP,
            port=DEFAULT_PORT,
            api_version=DEFAULT_API_VERSION,
            num_messages=NUM_MESSAGES,
            enums=ENUMS(),
        )
        test_harness = NodeTestHarness(WSAPIServerNode)

        stream_name: str
        stream_id: str

        with test_harness.get_node(config=wsapi_server_config) as node:
            # Create dummy WSAPIServerNode
            msg = WSStreamMessage(
                samples=sample_stream_mock_data,
                stream_name=DEFAULT_MOCK_STREAM_NAMES[0],
                stream_id=DEFAULT_MOCK_STREAM_IDS[0],
            )

            run_async(node.ws_server_publisher, args=[msg])
