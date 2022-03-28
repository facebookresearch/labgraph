#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from typing import Dict, Optional
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
    data_1: Optional[Dict] = None
    data_2: Optional[Dict] = None
    data_3: Optional[Dict] = None
    data_4: Optional[Dict] = None

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
        self.state.data_1 = {
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }

    @lg.subscriber(INPUT_2)
    def add_message_2(self, message: RandomMessage) -> None:
        self.state.data_2 = {
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }

    @lg.subscriber(INPUT_3)
    def add_message_3(self, message: RandomMessage) -> None:
        self.state.data_3 = {
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }
        
    @lg.subscriber(INPUT_4)
    def add_message_4(self, message: RandomMessage) -> None:
        self.state.data_4 = {
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }
    
    @lg.publisher(TOPIC)
    async def source(self) -> lg.AsyncPublisher:
        await asyncio.sleep(.1)
        while True:
            output_data = dict()
            if hasattr(self.config, "data"):
                output_data = {
                    key: value for key, value in self.config.data.items()
                }
                # Populate Serializer Node
                output_data["nodes"]["Serializer"]["upstreams"]["NoiseGenerator"][0]["fields"]["timestamp"]["content"] = self.state.data_1["timestamp"]
                output_data["nodes"]["Serializer"]["upstreams"]["NoiseGenerator"][0]["fields"]["data"]["content"] = self.state.data_1["numpy"]
                output_data["nodes"]["Serializer"]["upstreams"]["RollingAverager"][0]["fields"]["timestamp"]["content"] = self.state.data_2["timestamp"]
                output_data["nodes"]["Serializer"]["upstreams"]["RollingAverager"][0]["fields"]["data"]["content"] = self.state.data_2["numpy"]
                output_data["nodes"]["Serializer"]["upstreams"]["Amplifier"][0]["fields"]["timestamp"]["content"] = self.state.data_3["timestamp"]
                output_data["nodes"]["Serializer"]["upstreams"]["Amplifier"][0]["fields"]["data"]["content"] = self.state.data_3["numpy"]
                output_data["nodes"]["Serializer"]["upstreams"]["Attenuator"][0]["fields"]["timestamp"]["content"] = self.state.data_4["timestamp"]
                output_data["nodes"]["Serializer"]["upstreams"]["Attenuator"][0]["fields"]["data"]["content"] = self.state.data_4["numpy"]

                # Populate RollingAverage Node
                output_data["nodes"]["RollingAverager"]["upstreams"]["NoiseGenerator"][0]["fields"]["timestamp"]["content"] = self.state.data_1["timestamp"]
                output_data["nodes"]["RollingAverager"]["upstreams"]["NoiseGenerator"][0]["fields"]["data"]["content"] = self.state.data_1["numpy"]
                
                # Populate Amplifier Node
                output_data["nodes"]["Amplifier"]["upstreams"]["NoiseGenerator"][0]["fields"]["timestamp"]["content"] = self.state.data_2["timestamp"]
                output_data["nodes"]["Amplifier"]["upstreams"]["NoiseGenerator"][0]["fields"]["data"]["content"] = self.state.data_2["numpy"]

                # Populate Attenuator Node
                output_data["nodes"]["Attenuator"]["upstreams"]["NoiseGenerator"][0]["fields"]["timestamp"]["content"] = self.state.data_3["timestamp"]
                output_data["nodes"]["Attenuator"]["upstreams"]["NoiseGenerator"][0]["fields"]["data"]["content"] = self.state.data_3["numpy"]
            yield self.TOPIC, WSStreamMessage(
                samples=output_data,
                stream_name=self.config.stream_name,
                stream_id=self.config.stream_id,
            )
            await asyncio.sleep(1 / self.config.sample_rate), 
