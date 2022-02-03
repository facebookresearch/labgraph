#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
import os
import pathlib
import labgraph as lg
from labgraph.examples.simple_viz import Demo
from ..errors.errors import GenerateGraphvizError
from ..generate_graphviz.generate_graphviz import (
    identify_graph_nodes,
    out_edge_node_mapper,
    in_out_edge_mapper,
    connect_to_upstream,
    build_graph,
    generate_graphviz
)


class TestLabgraphGraphvizAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir: str = pathlib.Path(__file__).parent.absolute()
        self.graph: lg.Graph = Demo()

    def test_identify_graph_nodes(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        expected_node_count = 3
        self.assertEqual(expected_node_count, len(nodes))

    def test_out_edge_node_mapper(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        out_edge_node_map = out_edge_node_mapper(nodes)
        self.assertEqual(2, len(out_edge_node_map))
        self.assertEqual(
            'generate_noise',
            out_edge_node_map['AVERAGED_NOISE/GENERATOR/OUTPUT'].name
        )
        self.assertEqual(
            'average',
            out_edge_node_map['AVERAGED_NOISE/ROLLING_AVERAGER/OUTPUT'].name
        )

    def test_in_out_edge_mapper(self) -> None:
        in_out_edge_map = in_out_edge_mapper(self.graph.__streams__.values())
        self.assertEqual(2, len(in_out_edge_map))
        self.assertEqual(
            'AVERAGED_NOISE/GENERATOR/OUTPUT',
            in_out_edge_map['AVERAGED_NOISE/ROLLING_AVERAGER/INPUT']
        )
        self.assertEqual(
            'AVERAGED_NOISE/ROLLING_AVERAGER/OUTPUT',
            in_out_edge_map['PLOT/INPUT']
        )

    def test_connect_to_upstream(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        streams = self.graph.__streams__.values()
        nodes = connect_to_upstream(nodes, streams)
        self.assertEqual('average', nodes[0].upstream_node.name)
        self.assertIsNone(nodes[1].upstream_node)
        self.assertEqual('generate_noise', nodes[2].upstream_node.name)

    def test_build_graph(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        nodes = connect_to_upstream(nodes, self.graph.__streams__.values())
        output_dir = f"{self.test_dir}/output"
        output_file_name = f"{output_dir}/test"
        output_file_format = "svg"

        build_graph(nodes, output_file_name, output_file_format)
        self.assertTrue(
            os.path.exists(f"{output_file_name}.{output_file_format}")
        )

    def test_generate_graphviz_invalid_graph_instance(self) -> None:
        with self.assertRaises(GenerateGraphvizError):
            generate_graphviz(None, 'test.svg')

    def test_generate_graphviz_invalid_output_file(self) -> None:
        with self.assertRaises(GenerateGraphvizError):
            generate_graphviz(None, '')


if __name__ == "__main__":
    unittest.main()
