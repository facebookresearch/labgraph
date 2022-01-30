#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from labgraph.graphs.stream import Stream
from graphviz import Digraph
from typing import List
from ..method.method import Method
from ..errors.errors import GenerateGraphiz


def identify_graph_nodes(graph: lg.Graph) -> List[Method]:
    """
    Function that identifies the graph methods
    and return them as individual nodes

    @params:
        graph: instance of the running computational graph

    @return: List of nodes(methods)
    """
    nodes: List[Method] = []

    for method in graph.__methods__.values():
        node: Method = Method(method.name)
        if hasattr(method, 'subscribed_topic_path'):
            node.in_edge = method.subscribed_topic_path

        if hasattr(method, 'published_topic_paths'):
            for publishe_path in method.published_topic_paths:
                node.out_edges.append(publishe_path)

        if bool(len(node.in_edge) or len(node.out_edges)):
            nodes.append(node)

    return nodes


def find_connections(nodes: List[Method], streams: Stream) -> List[Method]:
    """
    Function the find the node that are connected

    @params:
        nodes: The list of nodes of the graph
        stream: sequence of messages that is accessible in real-time

    @return: The new list of nodes after update
    """
    for node_1 in nodes:
        out_edge = set(node_1.out_edges)
        for node_2 in nodes:
            if node_1 != node_2:
                for stream in streams:
                    # Check in_adjacents
                    intersection = set((node_1.in_edge, )).union(
                        set(node_2.out_edges)
                        ).intersection(stream.topic_paths)

                    if len(intersection) == 2:
                        node_1.in_adjacents.append(node_2)

                    # Check out_adjacents
                    intersection = out_edge.union(
                        set((node_2.in_edge, ))
                        ).intersection(stream.topic_paths)

                    if len(intersection) == 2:
                        node_1.out_adjacents.append(node_2)

    return nodes


def generate_graphviz(graph: lg.Graph, output_file: str) -> None:
    """
    Generates a graphviz visualization of the LabGraph topology
    @params:
        graph: An instance of the computational graph
        output_file: Filename for saving the source
    """
    # Check args
    if not isinstance(graph, lg.Graph):
        raise GenerateGraphiz(
            "Parameter 'graph' should be of type labgraph.Graph"
        )

    if not output_file:
        raise GenerateGraphiz(
            "Value cannot be null or empty string. Parameter name: output_file"
        )

    filename, format = output_file.split('.')

    # Local variables
    nodes: List[Method] = []
    graph_viz: Digraph = Digraph('graph', filename=filename, format=format)

    # Identify graph nodes
    nodes = identify_graph_nodes(graph)

    # Connect graph edges
    nodes = find_connections(nodes, graph.__streams__.values())

    # Build graph visualization
    graph_viz.attr(rankdir='LR')
    graph_viz.attr('node', shape='circle')

    for node in nodes:
        graph_viz.node(node.name)

    for node in nodes:
        for adj_node in node.out_adjacents:
            graph_viz.edge(node.name, adj_node.name)

    graph_viz.render()
    graph.__streams__.values()
