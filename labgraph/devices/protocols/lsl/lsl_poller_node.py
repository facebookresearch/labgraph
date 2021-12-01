from pylsl import StreamInlet, resolve_stream
from labgraph.graphs import AsyncPublisher, Config, Node, Topic, publisher
from labgraph.util.logger import get_logger
from labgraph.devices.protocols.lsl import LSLMessage

import asyncio


logger = get_logger(__name__)


class LSLPollerConfig(Config):
    type: str = 'labgraph'


class LSLPollerNode(Node):
    """
    represents a node in the graph which recieves data from an LSL
    stream, data received is subsequently pushed to rest of the graph
    as as LSLMessage
    Args:
        type: The name the type assigned to incoming stream
        (default 'labgraph')
    """
    topic = Topic(LSLMessage)
    config: LSLPollerConfig

    def setup(self) -> None:
        logger.log(1, f"looking for an {self.config.type} Stream")
        self.streams = resolve_stream('type', self.config.type)
        self.inlet = StreamInlet(self.streams[0])

    @publisher(topic)
    async def lsl_subscriber(self) -> AsyncPublisher:
        while True:
            sample, timestamp = self.inlet.pull_sample()
            yield self.topic, LSLMessage(sample)
            await asyncio.sleep(0.1)
