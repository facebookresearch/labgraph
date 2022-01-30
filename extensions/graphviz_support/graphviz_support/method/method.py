#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List


class Method:
    """
    Represents a node in the graph.
    """

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__in_edges: List[str] = []
        self.__out_edges: List[str] = []
        self.__in_adjacents: List['Method'] = []
        self.__out_adjacents: List['Method'] = []

    @property
    def name(self) -> str:
        return self.__name

    @property
    def in_edges(self) -> List[str]:
        return self.__in_edges

    @property
    def out_edges(self) -> List[str]:
        return self.__out_edges

    @property
    def in_adjacent(self) -> List['Method']:
        return self.__in_adjacents

    @property
    def out_adjacent(self) -> List['Method']:
        return self.__out_adjacents
