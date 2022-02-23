import socket


class SOCKETSenderNode():
    """
    Represents a node in a Labgraph graph that subscribes to messages in a
    Labgraph topic and forwards them by writing to a SOCKET object.
    """

    def setup(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((socket.gethostname(), 1234))

    def cleanup(self) -> None:
        self.socket.close()

    def socket_monitor(self) -> None:
        data = ''
        while True:
            msg = self.socket.recv(8)
            if(len(msg) <= 0):
                break
            data += msg.decode("utf-8")
        print(data)
