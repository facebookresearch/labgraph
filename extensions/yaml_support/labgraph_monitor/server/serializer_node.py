#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from dataclasses import field
from typing import Dict, Optional
import labgraph as lg
import asyncio
from labgraph.websockets.ws_server.ws_server_stream_message import (
    WSStreamMessage
)
from ..aliases.aliases import SerializedGraph

# Make it work with RandomMessage
from ....graphviz_support.graphviz_support.tests.demo_graph.random_message import RandomMessage

class SerializerConfig(lg.Config):
    data: SerializedGraph
    sub_pub_match: Optional[Dict] = field(default_factory=dict)
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

    SERIALIZER_OUTPUT = lg.Topic(WSStreamMessage)
    config: SerializerConfig
    state: DataState

    SERIALIZER_INPUT_1 = lg.Topic(RandomMessage)
    SERIALIZER_INPUT_2 = lg.Topic(RandomMessage)
    SERIALIZER_INPUT_3 = lg.Topic(RandomMessage)
    SERIALIZER_INPUT_4 = lg.Topic(RandomMessage)

    def get_grouping(self, topic: lg.Topic) -> str:
        """
        Matches subscriber topics with grouping that produced information 
        """
        for key, value in self.config.sub_pub_match.items():
            if topic.name in value["topics"]:
                return key
        return ""

    @lg.subscriber(SERIALIZER_INPUT_1)
    def add_message_1(self, message: RandomMessage) -> None:
        grouping = self.get_grouping(self.SERIALIZER_INPUT_1)
        self.state.data_1 = {
            "grouping": grouping,
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }

    @lg.subscriber(SERIALIZER_INPUT_2)
    def add_message_2(self, message: RandomMessage) -> None:
        grouping = self.get_grouping(self.SERIALIZER_INPUT_2)
        self.state.data_2 = {
            "grouping": grouping,
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }

    @lg.subscriber(SERIALIZER_INPUT_3)
    def add_message_3(self, message: RandomMessage) -> None:
        grouping = self.get_grouping(self.SERIALIZER_INPUT_3)
        self.state.data_3 = {
            "grouping": grouping,
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }
        
    @lg.subscriber(SERIALIZER_INPUT_4)
    def add_message_4(self, message: RandomMessage) -> None:
        grouping = self.get_grouping(self.SERIALIZER_INPUT_4)
        self.state.data_4 = {
            "grouping": grouping,
            "timestamp": message.timestamp,
            "numpy": list(message.data),
        }
    
    def output(self, _in: Dict) -> Dict:
        """
        Updates serialized message with data according to grouping
        
        @params:
            value of a dictionary that represents individual nodes
        """
        for node, value in _in.items():
            for state in self.state.__dict__.values():
                if state["grouping"] in value["upstreams"].keys():
                    value["upstreams"][state["grouping"]][0]["fields"]["timestamp"]["content"] = state["timestamp"]
                    value["upstreams"][state["grouping"]][0]["fields"]["data"]["content"] = state["numpy"]

        return _in

    @lg.publisher(SERIALIZER_OUTPUT)
    async def source(self) -> lg.AsyncPublisher:
        await asyncio.sleep(.1)
        while True:
            output_data = dict()
            if hasattr(self.config, "data"):
                # Populate Serialized Graph with real-time data
                output_data = {
                    key: self.output(value) for key, value in self.config.data.items() if key == "nodes"
                }
            yield self.SERIALIZER_OUTPUT, WSStreamMessage(
                samples=output_data,
                stream_name=self.config.stream_name,
                stream_id=self.config.stream_id,
            )
            await asyncio.sleep(1 / self.config.sample_rate), 
