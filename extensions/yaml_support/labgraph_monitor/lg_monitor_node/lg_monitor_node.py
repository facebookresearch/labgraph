#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List, Set
from .lg_monitor_message import LabgraphMonitorMessage


class LabgraphMonitorNode:
    """
    Represents a node in the graph.

    @attributes:
        name: A string that represents the name of the node.

        grouping: logical grouping of methods
                  which always share the same process

        in_edges: A set of in_edge.

        in_edge: A string that represents
                 a path to the topic to which the node is subscribed

        out_edges: A list of strings.
                   It represents the paths of the different topics
                   on which the node publishes data

        upstream_node: A LabgraphMonitorNode.
                       It represents the adjacent node
                       from where the data is received

        upstream_message: Represents the Labgraph message
                          that is received from the upstream
    """

    in_edges: Set[str] = set()

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__grouping: str = ''
        self.__in_edge: str = ''
        self.__out_edges: List[str] = []
        self.__upstream_node: 'LabgraphMonitorNode ' = None
        self.__upstream_message: LabgraphMonitorNode = None

    @property
    def name(self) -> str:
        return self.__name

    @property
    def grouping(self) -> str:
        return self.__grouping

    @grouping.setter
    def grouping(self, value) -> None:
        self.__grouping = value

    @property
    def in_edge(self) -> str:
        return self.__in_edge

    @in_edge.setter
    def in_edge(self, value) -> None:
        self.__in_edge = value
        self.in_edges.add(value)

    @property
    def out_edges(self) -> List[str]:
        return self.__out_edges

    @property
    def upstream_node(self) -> 'LabgraphMonitorNode':
        return self.__upstream_node

    @upstream_node.setter
    def upstream_node(self, value) -> None:
        self.__upstream_node = value

    @property
    def upstream_message(self) -> LabgraphMonitorMessage:
        return self.__upstream_message
