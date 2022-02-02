#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from labgraph.graphs.stream import Stream
from graphviz import Digraph
from typing import List
from ..graphviz_node.graphviz_node import GraphVizNode
from ..errors.errors import GenerateGraphvizError


def identify_graph_nodes(graph: lg.Graph) -> List[GraphVizNode]:
    """
    Function that identifies the graph methods
    and return them as individual nodes

    @params:
        graph: instance of the running computational graph

    @return: List of nodes
    """
    nodes: List[GraphVizNode] = []

    for method in graph.__methods__.values():
        node: GraphVizNode = GraphVizNode(method.name)

        if hasattr(method, 'subscribed_topic_path'):
            node.in_edge = method.subscribed_topic_path

        if hasattr(method, 'published_topic_paths'):
            for published_topic_path in method.published_topic_paths:
                node.out_edges.append(published_topic_path)

        if len(node.in_edge) or len(node.out_edges):
            nodes.append(node)

    return nodes


def find_connections(
    nodes: List[GraphVizNode],
    streams: Stream
) -> List[GraphVizNode]:
    """
    Function that finds the node that are connected

    @params:
        nodes: The list of nodes of the graph
        stream: sequence of messages that are accessible in real-time

    @return: The new list of nodes after update
    """
    for node_1 in nodes:
        out_edge = set(node_1.out_edges)
        for node_2 in nodes:
            if node_1 != node_2:
                for stream in streams:
                    # Check downstream nodes
                    intersection = out_edge.union(
                        set((node_2.in_edge, ))
                        ).intersection(stream.topic_paths)

                    if len(intersection) == 2:
                        node_1.downstream_nodes.append(node_2)

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
        for downstream_node in node.downstream_nodes:
            graph_viz.edge(node.name, downstream_node.name)

    graph_viz.render()
