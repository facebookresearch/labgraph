#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List


class GraphVizNode:
    """
    Represents a node in the graph.
    """

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__in_edge: str = ''
        self.__out_edges: List[str] = []
        self.__in_adjacents: List['GraphVizNode '] = []
        self.__out_adjacents: List['GraphVizNode '] = []

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
    def in_adjacents(self) -> List['GraphVizNode ']:
        return self.__in_adjacents

    @property
    def out_adjacents(self) -> List['GraphVizNode ']:
        return self.__out_adjacents
