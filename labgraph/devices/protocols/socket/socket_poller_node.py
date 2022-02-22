#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import socket

from socket_message import SOCKETMessage
from labgraph.graphs import Node


class SOCKETPollerNode():
    """
    Represents a node in the graph which recieves data from SOCKET.
    Data polled from SOCKET is subsequently pushed to rest of the graph
    as as SOCKETMessage
    """

    def setup(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((socket.gethostname(), 1234))
        self.socket.listen(5)

    def cleanup(self, clientsocket) -> None:
        clientsocket.close()

    def socket_monitor(self) -> None:
        while True:
            clientsocket, address = self.socket.accept()
            print(f"Connection from {address} has been established!")
            # client socket is our local version of the client's socket,
            # so we send information to the client
            clientsocket.send(bytes("Welcome to the server!", "utf-8"))
            self.cleanup(clientsocket)
