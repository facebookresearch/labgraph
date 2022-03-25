#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from typing import Optional
import labgraph as lg
import asyncio
from labgraph.websockets.ws_server.ws_server_stream_message import (
    WSStreamMessage
)
from ..aliases.aliases import SerializedGraph

# Make it work with RandomMessage
from ....graphviz_support.graphviz_support.tests.demo_graph.random_message import RandomMessage
import numpy as np

class SerializerConfig(lg.Config):
    data: SerializedGraph
    sample_rate: int
    stream_name: str
    stream_id: str

class DataState(lg.State):
    data_1: Optional[np.ndarray] = None
    data_2: Optional[np.ndarray] = None
    data_3: Optional[np.ndarray] = None
    data_4: Optional[np.ndarray] = None

class Serializer(lg.Node):
    """
    Convenience node for sending messages to a `WSAPIServerNode`.
    """

    TOPIC = lg.Topic(WSStreamMessage)
    config: SerializerConfig
    state: DataState

    INPUT_1 = lg.Topic(RandomMessage)
    INPUT_2 = lg.Topic(RandomMessage)
    INPUT_3 = lg.Topic(RandomMessage)
    INPUT_4 = lg.Topic(RandomMessage)

    @lg.subscriber(INPUT_1)
    def add_message_1(self, message: RandomMessage) -> None:
        self.state.data_1 = message.data

    @lg.subscriber(INPUT_2)
    def add_message_2(self, message: RandomMessage) -> None:
        self.state.data_2 = message.data

    @lg.subscriber(INPUT_3)
    def add_message_3(self, message: RandomMessage) -> None:
        self.state.data_3 = message.data
        
    @lg.subscriber(INPUT_4)
    def add_message_4(self, message: RandomMessage) -> None:
        self.state.data_4 = message.data
    
    @lg.publisher(TOPIC)
    async def source(self) -> lg.AsyncPublisher:
        await asyncio.sleep(.1)
        while True:
            output_data = {
                key: value for key, value in self.config.data.items()
            }
            # Populate Serializer Node
            output_data["nodes"]["Serializer"]["upstreams"]["NoiseGenerator"][0]["fields"]["data_content"] = str(self.state.data_1[0])
            output_data["nodes"]["Serializer"]["upstreams"]["RollingAverager"][0]["fields"]["data_content"] = str(self.state.data_2[0])
            output_data["nodes"]["Serializer"]["upstreams"]["Amplifier"][0]["fields"]["data_content"] = str(self.state.data_3[0])
            output_data["nodes"]["Serializer"]["upstreams"]["Attenuator"][0]["fields"]["data_content"] = str(self.state.data_4[0])

            # Populate RollingAverage Node
            output_data["nodes"]["RollingAverager"]["upstreams"]["NoiseGenerator"][0]["fields"]["data_content"] = str(self.state.data_1[0])
            
            # Populate Amplifier Node
            output_data["nodes"]["Amplifier"]["upstreams"]["NoiseGenerator"][0]["fields"]["data_content"] = str(self.state.data_2[0])

            # Populate Attenuator Node
            output_data["nodes"]["Attenuator"]["upstreams"]["NoiseGenerator"][0]["fields"]["data_content"] = str(self.state.data_3[0])
            yield self.TOPIC, WSStreamMessage(
                samples=output_data,
                stream_name=self.config.stream_name,
                stream_id=self.config.stream_id,
            )
            await asyncio.sleep(1 / self.config.sample_rate), 
