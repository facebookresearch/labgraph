#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import socket
from socket_message import SOCKETMessage
from labgraph.graphs import Config, Node, Topic, background
from labgraph.util.logger import get_logger


# server

# lookup what is a logger
STARTUP_WAIT_TIME = 5

logger = get_logger(__name__)


class SOCKETSenderConfig(Config):
    write_addr: str
    # The message: in our case it was (Welcome to the Server)
    socket_topic: str


class SOCKETSenderNode(Node):
    """
    Represents a node in the graph which recieves data from SOCKET.
    Data polled from SOCKET is subsequently pushed to rest of the graph
    as as SOCKETMessage

    Args: 
        read_addr: The address from which ZMQ data should be polled.
        socket_topic: The SOCKET topic being sent.
    """

    topic = Topic(SOCKETMessage)
    config: SOCKETSenderConfig

    def setup(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug(f"{self}:binding to {self.config.write_addr}")
        self.socket.bind((socket.gethostname(), self.config.write_addr))
        self.socket.listen(STARTUP_WAIT_TIME)

    def cleanup(self, clientsocket) -> None:
        clientsocket.close()

    @background
    async def socket_monitor(self) -> None:
        while True:
            clientsocket, address = self.socket.accept()
            print(f"Connection from {address} has been established!")
            # client socket is our local version of the client's socket,
            # so we send information to the client
            clientsocket.send(bytes(self.config.socket_topic, "utf-8"))
            self.cleanup(clientsocket)
