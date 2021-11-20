#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio

from ....graphs import (
    AsyncPublisher,
    Config,
    Connections,
    Graph,
    Node,
    Topic,
    publisher,
)
from ....runners import LocalRunner, NormalTermination
from ....util.logger import get_logger
from ....util.testing import local_test
from ..ws_api_node_server import (
    WSAPIServerConfig,
    WSAPIServerNode,
)
from ..ws_server_stream_message import WSStreamMessage
from .enums_test_server import ENUMS
from .test_data import sample_stream_mock_data


NUM_MESSAGES = 5
SAMPLE_RATE = 1000
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

logger = get_logger(__name__)


class MySourceConfig(Config):
    should_terminate: bool = False


class MySource(Node):
    """
    Convenience node for sending messages to a `WSAPIServerNode`.
    """

    TOPIC = Topic(WSStreamMessage)
    config: WSAPIServerConfig

    @publisher(TOPIC)
    async def source(self) -> AsyncPublisher:
        logger.info("Start of MySource source...")
        while True:
            sample = sample_stream_mock_data
            msg = WSStreamMessage(
                samples=sample,
                stream_name="device.stream1",
                stream_id="DEVICE.STREAM1",
            )
            yield self.TOPIC, msg
            await asyncio.sleep(1 / SAMPLE_RATE)

        if self.config.should_terminate:
            # Give the graph time to propagate the messages
            await asyncio.sleep(0.1)
            raise NormalTermination()


@local_test
def test_server() -> None:
    """
    Local tests for LabGraph.
    """

    class MyWSSenderGraph(Graph):
        MY_SOURCE: MySource
        MY_WSServerNode: WSAPIServerNode

        config: WSAPIServerConfig

        def setup(self) -> None:
            wsapi_server_config = WSAPIServerConfig(
                app_id="test_server",
                ip=DEFAULT_IP,
                port=DEFAULT_PORT,
                api_version=DEFAULT_API_VERSION,
                num_messages=-1,
                enums=ENUMS(),
                sample_rate=SAMPLE_RATE,
            )
            self.MY_SOURCE.configure(MySourceConfig())
            self.MY_WSServerNode.configure(wsapi_server_config)

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.TOPIC, self.MY_WSServerNode.topic),)

    graph = MyWSSenderGraph()
    runner = LocalRunner(module=graph)

    runner.run()


if __name__ == "__main__":
    test_server()
