from email.base64mime import header_length
import socket
import pickle
from labgraph.graphs import Config, Node
from labgraph.graphs.method import background
from labgraph.util.logger import get_logger

# client

logger = get_logger(__name__)


class SOCKETPollerConfig(Config):
    read_addr: str
    socket_topic: str


class SOCKETPollerNode(Node):
    """
    Represents a node in a Labgraph graph that subscribes to messages in a
    Labgraph topic and forwards them by writing to a SOCKET object.
    """
    config: SOCKETPollerConfig

    def setup(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((socket.gethostname(), self.config.read_addr))

        self.socket_open = False

    def cleanup(self) -> None:
        self.socket.close()

    @background
    def socket_monitor(self) -> None:
        data = ''
        while True:
            # What's the size of the socket
            msg = self.socket.recv(header_length)
            if not len(msg):
                break
            data += msg
        data = pickle.loads(data)
        event = data["event"]
        logger.debug(f"{self}:{event.name}")
