#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import labgraph as lg
from typing import List, Tuple, Dict

class DynamicGraph(lg.Graph):

    """
    DynamicGraph, allows you to construct a Graph object based on run-time parameters.
    `class ExampleGraph(DynamicGraph):`

    Use ExampleGraph.add_node() to register nodes.
    The `connections` parameter is expected to be a list with 4 strings:
    `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`

    Example:
        `ExampleGraph.add_node("TestNode2", TestNode2, ["TestNode2", "INPUT", "TestNode1", "OUTPUT", TestNode2Config(...)])`
    """

    _connections: List[List[str]] = []
    _logger_connections: List[Tuple[str, str, str]] = []
    _configs: dict = {}
    _cls: type = None

    @classmethod
    def add_node(cls, name: str, _type: type, connection: List[str] = None, config: lg.Config = None) -> None:
        """
        Add a node to the graph

        `name`: `str` the node's desired variable name
        `_type`: `type` the node's type
        `connection`: `List[str]` optional, expected to have a length of 4

        Example:
            `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`
        
        `config`: `lg.Config` optional, config object to be given to this node during setup
        """
        setattr(cls, name, None)
        cls.__annotations__[name] = _type
        cls.__children_types__[name] = _type

        if connection:
            cls._connections.append(connection)
        
        if config:
            cls._configs[name] = config

    @classmethod
    def add_connection(cls, connection: List[str]) -> None:
        """
        Add a connection between two nodes

        `connection`: `List[str]` expected to have a length of 4

        Example:
            `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`
        """
        cls._connections.append(connection)
    
    @classmethod
    def add_logger_connection(cls, connection: Tuple[str, str, str]) -> None:
        """
        Add a connection to the logger

        `connection`: `Tuple[str, str, str]`

        Example:
            `(logged stream path, node variable name, node output variable name)`
        """
        cls._logger_connections.append(connection)

    def setup(self) -> None:
        for key in type(self)._configs:
            self.__getattribute__(key).configure(type(self)._configs[key])

    def connections(self) -> lg.Connections:
        cons = []
        for con_list in type(self)._connections:
            node1: lg.Node = self.__getattribute__(con_list[0])
            node2: lg.Node = self.__getattribute__(con_list[2])
            cons.append((node1.__getattribute__(con_list[1]), node2.__getattribute__(con_list[3])))
        return tuple(cons)
    
    def logging(self) -> Dict[str, lg.Topic]:
        _dict = {}
        for con in type(self)._logger_connections:
            _dict[con[0]] = self.__getattribute__(con[1]).__getattribute__(con[2])
        return _dict

    def process_modules(self) -> Tuple[lg.Module, ...]:
        mods = ()
        for key in type(self).__children_types__:
            mods += (self.__getattribute__(key),)
        return mods

class DynamicGroup(lg.Group):

    """
    DynamicGroup, allows you to construct a Group object based on run-time parameters.
    `class ExampleGroup(DynamicGroup):`
    
    Use ExampleGroup.add_node() to register nodes.
    The `connections` parameter is expected to be a list with 4 strings:
    `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`

    Example:
        `DynamicGroup.add_node("TestNode2", TestNode2, ["TestNode2", "INPUT", "TestNode1", "OUTPUT", TestNode2Config(...)])`
    """

    _connections: List[List[str]] = []
    _configs: dict = {}

    @classmethod
    def add_node(cls, name: str, _type: type, connection: List[str] = None, config: lg.Config = None) -> None:
        """
        Add a node to the group

        `name`: `str` the node's desired variable name
        `_type`: `type` the node's type
        `connection`: `List[str]` optional, expected to have a length of 4

        Example:
            `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`
        
        `config`: `lg.Config` optional, config object to be given to this node during setup
        """
        setattr(cls, name, None)
        cls.__annotations__[name] = _type
        cls.__children_types__[name] = _type

        if connection:
            cls._connections.append(connection)
        
        if config:
            cls._configs[name] = config

    @classmethod
    def add_connection(cls, connection: List[str]) -> None:
        """
        Add a connection between two nodes

        `connection`: `List[str]` expected to have a length of 4

        Example:
            `[Node1Name, Node1TopicName, Node2Name, Node2TopicName]`
        """
        cls._connections.append(connection)

    @classmethod
    def add_topic(cls, name: str, topic: lg.Topic) -> None:
        """
        Add a topic object

        `name`: `str` the variable's name
        `topic`: `lg.Topic` the topic object to add
        """
        setattr(cls, name, topic)

    def setup(self) -> None:
        for key in type(self)._configs:
            self.__getattribute__(key).configure(type(self)._configs[key])

    def connections(self) -> lg.Connections:
        cons = []
        for con_list in type(self)._connections:
            node1: lg.Node = self.__getattribute__(con_list[0])
            node2: lg.Node = self.__getattribute__(con_list[2])
            cons.append((node1.__getattribute__(con_list[1]), node2.__getattribute__(con_list[3])))
        return tuple(cons)