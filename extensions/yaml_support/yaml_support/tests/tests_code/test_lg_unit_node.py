import labgraph as lg
from .test_lg_unit_message import MyMessage
from .test_lg_unit_config import MyConfig
import numpy as np
import asyncio


class MyNode(lg.Node):

    OUTPUT = lg.Topic(MyMessage)
    config: MyConfig

    @lg.publisher(OUTPUT)
    async def generate(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT, MyMessage(
                    field_1=np.random(),
                    field_2=np.random(),
                )
            await asyncio.sleep(0.001)
