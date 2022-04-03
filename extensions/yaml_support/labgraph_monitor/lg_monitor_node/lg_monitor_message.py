#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg
from ..aliases.aliases import SerializedMessage


class LabgraphMonitorMessage:
    """
    Represents a Labgraph message.
    A message is a collection of data that can be sent
    between nodes via topics.

    @attributes:
        message: A class that inherent from lg.Message,
              The class name represents the type of the message.
    """
    def __init__(self, value: lg.Message) -> None:
        self.___value: str = value

    def name(self) -> str:
        return self.___value.__name__

    def serialize(self) -> SerializedMessage:
        """
        A function that returns a serialized version of the labgraph message.
        """
        serialized_message: SerializedMessage = {
            "name": self.name(),
            "fields": {}
        }

        for annotation in self.___value.__annotations__.items():
            name = annotation[0]
            type = (annotation[1]).__name__

            serialized_message['fields'][name] = type

        return serialized_message
