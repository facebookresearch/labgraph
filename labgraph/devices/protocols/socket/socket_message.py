from labgraph.messages import Message


class SOCKETMessage(Message):
    """
    A message representing data that was/will be communicate to SOCKET
    """

    data: bytes
