#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List


class GraphVizNode:
    """
    Represents a node in the graph.

    @attributes:
        name: A string that represents the name of the node.

        in_edge: A string that represents
                 a path to the topic to which the node is subscribed

        out_edges: A list of strings.
                   It represents the paths of the different topics
                   on which the node publishes data

        downstream_nodes: A list of GraphVizNode.
                          It represents the adjacent node to which
                          the node is streaming data
    """
    def __init__(self, name: str) -> None:
        self.__name = name
        self.__in_edge: str = ''
        self.__out_edges: List[str] = []
        self.__downstream_nodes: List['GraphVizNode '] = []

    @property
    def name(self) -> str:
        return self.__name

    @property
    def in_edge(self) -> str:
        return self.__in_edge

    @in_edge.setter
    def in_edge(self, value) -> None:
        self.__in_edge = value

    @property
    def out_edges(self) -> List[str]:
        return self.__out_edges

    @property
    def downstream_nodes(self) -> List['GraphVizNode ']:
        return self.__downstream_nodes
