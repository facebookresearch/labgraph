#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg


class LabgraphMonitorMessage:
    """
    Represents a Labgraph message.
    A message is a collection of data that can be sent
    between nodes via topics.

    @attributes:
        name: A string that represents the name of the message.

        type: A class that inherent from lg.Message,
              The class name represents the type of the message.
    """
    def __init__(self, name: str, type: lg.Message) -> None:
        self.__name: str = name
        self.__type: lg.Message = type

    @property
    def name(self) -> str:
        return self.__name

    @property
    def type(self) -> str:
        return self.__type
