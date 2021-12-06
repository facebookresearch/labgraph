from labgraph.messages import Message


class LSLMessage(Message):
    """
    A message representing data was/will be commuinicated to LSL
    """
    data: list
