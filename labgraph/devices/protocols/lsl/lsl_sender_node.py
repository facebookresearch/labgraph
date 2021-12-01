import asyncio
from pylsl import StreamOutlet, StreamInfo

from labgraph.graphs import Config, Node, Topic, subscriber
from labgraph.util.logger import get_logger
from labgraph.devices.protocols.lsl import LSLMessage


logger = get_logger(__name__)


class LSLSenderConfig(Config):
    name: str
    type: str
    n_channels: int = 1
    unique_identifier: str
    srate: float = 0.0


class LSLSenderNode(Node):
    """
    Represents a node in LabGraph graph that recieves messages
    in a Labgraph topic and forwards the data via lsl stream

    Args:
        name: The name of the stream
        type: The name the type
        n_channels: Number of channels per sample. This stays constant for
                    the lifetime of the stream. (default 1)
        unique_identifier: ideally should be serial number of device
        srate:The sampling rate (in Hz) as advertised by the data source
        (default 0.0)
    """

    topic = Topic(LSLMessage)
    config: LSLSenderConfig

    def setup(self) -> None:
        self.info = StreamInfo(name=self.config.name,
                               channel_count=self.config.n_channels,
                               type=self.config.type,
                               nominal_srate=self.config.srate,
                               source_id=self.config.unique_identifier)

        self.outlet = StreamOutlet(self.info)

    @subscriber(topic)
    async def lsl_publisher(self, message: LSLMessage) -> None:
        while True:
            data = message.data
            self.outlet.push_sample(data)
            await asyncio.sleep(0.1)
