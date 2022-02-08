#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from labgraph.graphs.stream import Stream
from typing import List, Dict
from ..lg_monitor_node.lg_monitor_node import LabgraphMonitorNode
from ..lg_monitor_node.lg_monitor_message import LabgraphMonitorMessage
from ..aliases.aliases import SerializedGraph
from ..server.lg_monitor_server import run_server


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
        topics[in_edge]._name,
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


def serialize_graph(
    name: str,
    nodes: List[LabgraphMonitorNode]
) -> SerializedGraph:
    """
    A function that returns a serialized version of the graph topology.

    @params:
        name: The name of the graph
        nodes: The list of nodes of the graph

    @return: A serialized version of the graph topology
    """
    serialized_graph: SerializedGraph = {
        "name": name,
        "nodes": {}
    }

    for node in nodes:
        if node.grouping not in serialized_graph["nodes"]:
            serialized_graph["nodes"][node.grouping] = {
                "inputs": [],
                "upstreams": []
            }

        if node.upstream_node:
            serialized_graph["nodes"][node.grouping]["inputs"].append({
                "name": node.upstream_message.name,
                "type": node.upstream_message.type.__name__
            })

            serialized_graph["nodes"][node.grouping]["upstreams"].append(
                node.upstream_node.grouping
            )

    return serialized_graph


def generate_labgraph_monitor(graph: lg.Graph) -> None:
    """
    A function that serialize the graph topology
    and send it using to LabGraphMonitor Front-End
    using Labgraph Websocket API

    @params:
        graph: An instance of the computational graph
    """
    # Local variables
    nodes: List[LabgraphMonitorNode] = []

    # Identify graph nodes
    nodes = identify_graph_nodes(graph)

    # Connect graph edges
    nodes = connect_to_upstream(nodes, graph.__streams__.values())

    # Serialize the graph topology
    serialized_graph = serialize_graph(
        type(graph).__name__,
        nodes
    )

    # Send the serialized graph to Front-End
    # using LabGraph Websockets API
    run_server(serialized_graph)
