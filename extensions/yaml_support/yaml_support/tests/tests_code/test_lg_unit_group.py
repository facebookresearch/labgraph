import labgraph as lg
from .test_lg_unit_message import MyMessage
from .test_lg_unit_config import MyConfig
from .test_lg_unit_node import MyNode


class MyGroup(lg.Group):

    OUTPUT = lg.Topic(MyMessage)
    config: MyConfig
    NODE_1: MyNode
    NODE_2: MyNode

    def connections(self) -> lg.Connections:
        pass

    def setup(self) -> None:
        pass
