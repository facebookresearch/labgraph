#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg
from labgraph.graphs.stream import Stream
from typing import List, Dict, Tuple
from ..lg_monitor_node.lg_monitor_node import LabgraphMonitorNode
from ..lg_monitor_node.lg_monitor_message import LabgraphMonitorMessage
from ..aliases.aliases import SerializedGraph

def identify_upstream_message(
    in_edge: str,
    topics: Dict[str, lg.Topic]
) -> LabgraphMonitorMessage:
    """
    A function that identifies upstream message
    based on the subscribed topic path (in edge)

    @params:
        in_edge: A string that represents
                 a path to the topic to which the node is subscribed

        topics:  References to streams
    """
    return LabgraphMonitorMessage(
        topics[in_edge].message_type
    )


def identify_graph_nodes(graph: lg.Graph) -> List[LabgraphMonitorNode]:
    """
    A function that identifies the graph methods
    and return them as individual nodes

    @params:
        graph: Instance of the running computational graph

    @return: List of nodes
    """
    nodes: List[LabgraphMonitorNode] = []

    for key, method in graph.__methods__.items():
        node: LabgraphMonitorNode = LabgraphMonitorNode(method.name)

        # Find grouping name
        group_path = '/'.join(key.split('/')[:-1])
        node.grouping = type(graph.__descendants__[group_path]).__name__

        if hasattr(method, 'subscribed_topic_path'):
            node.in_edge = method.subscribed_topic_path

        if hasattr(method, 'published_topic_paths'):
            for published_topic_path in method.published_topic_paths:
                node.out_edges.append(published_topic_path)

        if node.in_edge:
            node.upstream_message = identify_upstream_message(
                node.in_edge,
                graph.__topics__
            )
            nodes.append(node)

        elif node.out_edges:
            nodes.append(node)

    return nodes


def out_edge_node_mapper(
    nodes: List[LabgraphMonitorNode]
) -> Dict[str, List[LabgraphMonitorNode]]:
    """
    A function that maps a published topic to the publisher node

    @params:
        nodes: The list of nodes of the graph

    @return: A dictionary where the key is the published topic path
             and the value is the publisher node
    """
    out_edge_node_map: Dict[str, List[LabgraphMonitorNode]] = {}

    for node in nodes:
        for out_edge in node.out_edges:
            out_edge_node_map[out_edge] = node

    return out_edge_node_map


def in_out_edge_mapper(streams: Stream) -> Dict[str, str]:
    """
    A function that maps the in_edge of a downstream node
             with the out_edge of the appropriate upstream node

    @params:
        streams: sequence of messages that are accessible in real-time

    @return: A dictionary where the key is the subscribed topic path
             and the value is the published topic path
    """
    in_out_edge_map: Dict[str, str] = {}

    for stream in streams:
        difference = set(stream.topic_paths).difference(
            LabgraphMonitorNode.in_edges
        )

        if difference:
            upstream_edge = max(difference, key=len)
            for edge in stream.topic_paths:
                if edge != upstream_edge:
                    in_out_edge_map[edge] = upstream_edge

    return in_out_edge_map


def connect_to_upstream(
    nodes: List[LabgraphMonitorNode],
    streams: Stream
) -> List[LabgraphMonitorNode]:
    """
    A function that connect a node to its upstream node

    @params:
        nodes: The list of nodes of the graph
        streams: sequence of messages that are accessible in real-time

    @return: The new list of nodes after update
    """
    out_edge_node_map = out_edge_node_mapper(nodes)
    in_out_edge_map = in_out_edge_mapper(streams)

    for node in nodes:
        if node.in_edge:
            node.upstream_node = out_edge_node_map[
                in_out_edge_map[node.in_edge]
            ]

    return nodes


def serialize_graph(graph: lg.Graph) -> SerializedGraph:
    """
    A function that returns a serialized version of the graph topology.

    @params:
        name: The name of the graph
        nodes: The list of nodes of the graph

    @return: A serialized version of the graph topology
    """
    # List of graph nodes
    nodes: List[LabgraphMonitorNode] = []

    # Identify graph nodes
    nodes = identify_graph_nodes(graph)

    # Connect graph edges
    nodes = connect_to_upstream(nodes, graph.__streams__.values())

    serialized_graph: SerializedGraph = {
        "name": type(graph).__name__,
        "nodes": {}
    }

    for node in nodes:
        if node.grouping not in serialized_graph["nodes"]:
            serialized_graph["nodes"][node.grouping] = {
                "upstreams": {}
            }

        if node.upstream_node:

            if node.upstream_node.grouping not in \
             serialized_graph["nodes"][node.grouping]["upstreams"]:
                (serialized_graph["nodes"]
                    [node.grouping]
                    ["upstreams"]
                    [node.upstream_node.grouping]) = [
                        node.upstream_message.serialize()
                    ]
            else:
                (serialized_graph["nodes"]
                    [node.grouping]
                    ["upstreams"]
                    [node.upstream_node.grouping]).append(
                        node.upstream_message.serialize()
                    )

    return serialized_graph

def sub_pub_grouping_map(graph: lg.Graph) -> Dict[str, str]:
    """
    A function that matches subscribers with their publishers
    to automate assigning real-time messages to serialized graph

    @params:
        graph: An instance of the computational graph

    @return: A dictionary where the key is a publisher grouping
            and the value is a dictionary of sets of topic paths subscribed and their groupings
    """
    sub_pub_grouping_map: Dict[str, str] = {}
    for stream in graph.__streams__.values():
        difference = set(stream.topic_paths).difference(LabgraphMonitorNode.in_edges)
        if difference:
            upstream_edge = max(difference, key=len)
            for edge in stream.topic_paths:
                if edge != upstream_edge:
                    # convert SERIALIZER/SERIALIZER_INPUT_1 to its grouping Serializer
                    edge_path = "/".join(edge.split("/")[:-1])
                    edge_grouping = type(graph.__descendants__[edge_path]).__name__
                    
                    # convert SERIALIZER/SERIALIZER_INPUT_1 to its topic SERIALIZER_INPUT_1
                    topic_path = edge.split("/")[-1]

                    # convert NOISE_GENERATOR/NOISE_GENERATOR_OUTPUT to its grouping NoiseGenerator
                    group_path = "/".join(upstream_edge.split("/")[:-1])
                    grouping = type(graph.__descendants__[group_path]).__name__

                    if grouping in sub_pub_grouping_map:
                        sub_pub_grouping_map[grouping]["topics"].add(topic_path)
                        sub_pub_grouping_map[grouping]["subscribers"].add(edge_grouping)
                    else:
                        sub_pub_grouping_map[grouping] = {
                            "topics": {topic_path},
                            "subscribers": {edge_grouping},
                        }
                    
    return sub_pub_grouping_map

def generate_graph_topology(graph: lg.Graph) -> SerializedGraph:
    """
    A function that serializes the graph topology
    and sends it to LabGraph Monitor Front-End
    using WebSockets API

    @params:
        graph: An instance of the computational graph
    
    @return: Serialized topology of the graph
    """
    serialized_graph = serialize_graph(graph)

    return serialized_graph

def set_graph_topology(graph: lg.Graph) -> None:
    """
    A function that serializes the graph topology
    and applies the information to serve as graph 
    attribute for LabGraph Monitor Front-End 
    real-time messaging using WebSockets API
    
    @params:
        graph: An instance of the computational graph
    """
    # Serialize the graph topology
    serialized_graph = serialize_graph(graph)

    # Match subscribers with their publishers
    sub_pub_map = sub_pub_grouping_map(graph)

    # Set graph's topology and real-time messages matching
    if hasattr(graph, "set_topology"):
        graph.set_topology(serialized_graph, sub_pub_map)
    else:
        raise AttributeError(
            """
            Provided graph is missing `set_topology` method to establish 
            its topology and possible real-time messsaging

            Please add the following method to your graph
            ```
            def set_topology(self, topology: SerializedGraph, sub_pub_map: Dict) -> None:
                self._topology = topology
                self._sub_pub_match = sub_pub_map
            ```
            """
        )