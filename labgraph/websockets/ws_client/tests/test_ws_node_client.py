#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ....graphs import (
    Config,
    Connections,
    Graph,
    Node,
    Topic,
    subscriber,
)
from ....runners import LocalRunner, NormalTermination
from ....util.testing import local_test
from ....websockets.ws_client.ws_client_message import WSMessage
from ..ws_poller_stream_node import STREAMWSPollerNode, STREAMWSPollerConfig


NUM_MESSAGES = 5

DATA_DELIMITER = b"\0"


class MySinkConfig(Config):
    output_filename: str


class MySink(Node):
    """
    Convenience node for receiving messages from a `WSPollerNode`.
    """

    TOPIC = Topic(WSMessage)
    config: MySinkConfig

    def setup(self) -> None:
        self.output_file = open(self.config.output_filename, "wb")
        self.num_received = 0

    @subscriber(TOPIC)
    async def sink(self, message: WSMessage) -> None:
        self.output_file.write(str.encode(message.data))
        self.output_file.write(DATA_DELIMITER)

        self.num_received += 1
        if self.num_received == NUM_MESSAGES:
            raise NormalTermination()

    def cleanup(self) -> None:
        self.output_file.close()


@local_test
def test_ws_poller_node() -> None:
    """
    Tests that a `WSPollerNode` is able to read samples from a WebSocket socket and echo
    the samples back out of the graph.
    """

    class MyWSPollerGraphConfig(Config):
        output_filename: str

    class MyWSPollerGraph(Graph):
        MY_SOURCE: STREAMWSPollerNode
        MY_SINK: MySink
        config: MyWSPollerGraphConfig

        streams = ["device.stream1"]

        def setup(self) -> None:
            self.MY_SOURCE.configure(
                STREAMWSPollerConfig(
                    app_id="test_ws_poller_node",
                    streams=self.streams,
                )
            )
            self.MY_SINK.configure(
                MySinkConfig(output_filename=self.config.output_filename)
            )

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.topic, self.MY_SINK.TOPIC),)

    graph = MyWSPollerGraph()
    output_filename = "output_test_ws_node_client.txt"
    graph.configure(MyWSPollerGraphConfig(output_filename=output_filename))
    runner = LocalRunner(module=graph)

    runner.run()


if __name__ == "__main__":
    test_ws_poller_node()
