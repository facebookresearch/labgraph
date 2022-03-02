import socket
from labgraph.graphs import Config, Node
from labgraph.graphs.method import background

# client


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

    def cleanup(self) -> None:
        self.socket.close()

    @background
    def socket_monitor(self) -> None:
        data = ''
        while True:
            msg = self.socket.recv(8)
            if(len(msg) <= 0):
                break
            data += msg.decode("utf-8")
        print(data)
