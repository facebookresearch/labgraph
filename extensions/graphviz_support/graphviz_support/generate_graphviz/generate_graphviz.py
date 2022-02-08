#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from labgraph.graphs.stream import Stream
from graphviz import Digraph
from typing import List, Dict
from ..graphviz_node.graphviz_node import GraphVizNode
from ..errors.errors import GenerateGraphvizError


def identify_graph_nodes(graph: lg.Graph) -> List[GraphVizNode]:
    """
    A function that identifies the graph methods
    and return them as individual nodes

    @params:
        graph: Instance of the running computational graph

    @return: List of nodes
    """
    nodes: List[GraphVizNode] = []

    for key, method in graph.__methods__.items():
        node: GraphVizNode = GraphVizNode(method.name)

        # Find grouping name
        group_path = '/'.join(key.split('/')[:-1])
        node.grouping = type(graph.__descendants__[group_path]).__name__

        if hasattr(method, 'subscribed_topic_path'):
            node.in_edge = method.subscribed_topic_path

        if hasattr(method, 'published_topic_paths'):
            for published_topic_path in method.published_topic_paths:
                node.out_edges.append(published_topic_path)

        if len(node.in_edge) or len(node.out_edges):
            nodes.append(node)

    return nodes


def out_edge_node_mapper(
    nodes: List[GraphVizNode]
) -> Dict[str, List[GraphVizNode]]:
    """
    A function that maps a published topic to the publisher node

    @params:
        nodes: The list of nodes of the graph

    @return: A dictionary where the key is the published topic path
             and the value is the publisher node
    """
    out_edge_node_map: Dict[str, List[GraphVizNode]] = {}

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
        difference = set(stream.topic_paths).difference(GraphVizNode.in_edges)

        if difference:
            upstream_edge = max(difference, key=len)
            for edge in stream.topic_paths:
                if edge != upstream_edge:
                    in_out_edge_map[edge] = upstream_edge

    return in_out_edge_map


def connect_to_upstream(
    nodes: List[GraphVizNode],
    streams: Stream
) -> List[GraphVizNode]:
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


def build_graph(
    name: str,
    nodes: List[GraphVizNode],
    filename: str,
    format: str
) -> None:
    """
    A function that generates a graphviz visualization

    @params:
        name: The name of the graph
        nodes: The list of nodes of the graph
        filename: The name of the output file
        format: The format of the output file
    """
    graph_viz: Digraph = Digraph(
        name,
        filename=filename,
        format=format
    )
    graph_viz.attr(rankdir='LR', center="true")
    graph_viz.attr(
        'node',
        shape='circle',
        fontsize="12",
        width="1.5",
        height="1.5"
    )

    for node in nodes:
        graph_viz.node(node.grouping)

    for node in nodes:
        if node.upstream_node:
            graph_viz.edge(
                node.upstream_node.grouping,
                node.grouping
            )

    graph_viz.render()


def generate_graphviz(graph: lg.Graph, output_file: str) -> None:
    """
    A function that generates a graphviz visualization of the LabGraph topology
    @params:
        graph: An instance of the computational graph
        output_file: Filename for saving the source
    """
    # Check args
    if not isinstance(graph, lg.Graph):
        raise GenerateGraphvizError(
            "Parameter 'graph' should be of type labgraph.Graph"
        )

    if not output_file:
        raise GenerateGraphvizError(
            "Parameter 'output_file' cannot be null or empty string."
        )
    filename, format = output_file.split('.')

    # Local variables
    nodes: List[GraphVizNode] = []

    # Identify graph nodes
    nodes = identify_graph_nodes(graph)

    # Connect graph edges
    nodes = connect_to_upstream(nodes, graph.__streams__.values())

    # Build graph visualization
    build_graph(
        type(graph).__name__,
        nodes,
        filename,
        format
    )
