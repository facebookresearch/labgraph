#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve


import labgraph as lg
from graphviz import Digraph
from typing import List
from ..method.method import Method
from ..errors.errors import GenerateGraphiz


def generate_graphviz(graph: lg.Graph, output_file: str) -> None:
    """
    Generates a graphviz visualization of the LabGraph topology
    @params:
        graph: An instance of the computational graph
        output_file: Filename for saving the source
    """
    # Check args
    if graph is None:
        raise GenerateGraphiz(
            "Value cannot be null. Parameter name: graph"
        )

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
    for method in graph.__methods__.values():
        node: Method = Method(method.name)
        if hasattr(method, 'subscribed_topic_path'):
            node.in_edge = method.subscribed_topic_path

        if hasattr(method, 'published_topic_paths'):
            for publishe_path in method.published_topic_paths:
                node.out_edges.append(publishe_path)

        if bool(len(node.in_edge) or len(node.out_edges)):
            nodes.append(node)

    # Identify graph edges
    for node_1 in nodes:
        out_edge = set(node_1.out_edges)
        for node_2 in nodes:
            if node_1 != node_2:
                for stream in graph.__streams__.values():
                    # Check out_adjacents
                    intersection = out_edge.union(
                        set((node_2.in_edge, ))
                        ).intersection(stream.topic_paths)

                    if len(intersection) > 1:
                        node_1.out_adjacents.append(node_2)

    # Build graph visualization
    graph_viz.attr(rankdir='LR')
    graph_viz.attr('node', shape='circle')

    for node in nodes:
        graph_viz.node(node.name)

    for node in nodes:
        for adj_node in node.out_adjacents:
            graph_viz.edge(node.name, adj_node.name)

    graph_viz.view()
