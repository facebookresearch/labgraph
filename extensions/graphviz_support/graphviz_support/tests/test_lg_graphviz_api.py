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
    find_connections,
    generate_graphviz
)


class TestLabgraphGraphvizAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir: str = pathlib.Path(__file__).parent.absolute()
        self.graph: lg.Graph = Demo()

    def test_generate_graphviz_invalid_graph_instance(self) -> None:
        with self.assertRaises(GenerateGraphvizError):
            generate_graphviz(None, 'test.svg')

    def test_generate_graphviz_invalid_output_file(self) -> None:
        with self.assertRaises(GenerateGraphvizError):
            generate_graphviz(None, '')

    def test_identify_graph_nodes(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        expected_node_count = 3
        self.assertEqual(expected_node_count, len(nodes))

    def test_find_connections(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        streams = self.graph.__streams__.values()
        nodes = find_connections(nodes, streams)
        self.assertEqual(0, len(nodes[0].downstream_nodes))
        self.assertEqual(1, len(nodes[1].downstream_nodes))
        self.assertEqual(1, len(nodes[2].downstream_nodes))

    def test_generate_graphviz(self) -> None:
        output_dir = f"{self.test_dir}/output"
        output_file = f"{output_dir}/test.svg"
        generate_graphviz(self.graph, output_file)
        self.assertEqual(True, os.path.exists(output_file))


if __name__ == "__main__":
    unittest.main()
