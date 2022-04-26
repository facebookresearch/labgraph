#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
import os
import pathlib
import labgraph as lg
from .demo_graph.demo import Demo
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
        self.graph: lg.Graph = Demo()

    def test_identify_graph_nodes(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        expected_node_count = 7
        self.assertEqual(expected_node_count, len(nodes))

    def test_out_edge_node_mapper(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        out_edge_node_map = out_edge_node_mapper(nodes)
        self.assertEqual(4, len(out_edge_node_map))
        self.assertEqual(
            'generate_noise',
            out_edge_node_map['NOISE_GENERATOR/NOISE_GENERATOR_OUTPUT'].name
        )
        self.assertEqual(
            'average',
            out_edge_node_map['ROLLING_AVERAGER/ROLLING_AVERAGER_OUTPUT'].name
        )
        self.assertEqual(
            'amplify',
            out_edge_node_map['AMPLIFIER/AMPLIFIER_OUTPUT'].name
        )
        self.assertEqual(
            'attenuate',
            out_edge_node_map['ATTENUATOR/ATTENUATOR_OUTPUT'].name
        )

    def test_in_out_edge_mapper(self) -> None:
        in_out_edge_map = in_out_edge_mapper(self.graph.__streams__.values())
        self.assertEqual(6, len(in_out_edge_map))
        self.assertEqual(
            'NOISE_GENERATOR/NOISE_GENERATOR_OUTPUT',
            in_out_edge_map['ROLLING_AVERAGER/ROLLING_AVERAGER_INPUT']
        )
        self.assertEqual(
            'NOISE_GENERATOR/NOISE_GENERATOR_OUTPUT',
            in_out_edge_map['AMPLIFIER/AMPLIFIER_INPUT']
        )
        self.assertEqual(
            'NOISE_GENERATOR/NOISE_GENERATOR_OUTPUT',
            in_out_edge_map['ATTENUATOR/ATTENUATOR_INPUT']
        )
        self.assertEqual(
            'ROLLING_AVERAGER/ROLLING_AVERAGER_OUTPUT',
            in_out_edge_map['SINK/SINK_INPUT_1']
        )
        self.assertEqual(
            'AMPLIFIER/AMPLIFIER_OUTPUT',
            in_out_edge_map['SINK/SINK_INPUT_2']
        )
        self.assertEqual(
            'ATTENUATOR/ATTENUATOR_OUTPUT',
            in_out_edge_map['SINK/SINK_INPUT_3']
        )

    def test_connect_to_upstream(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        streams = self.graph.__streams__.values()
        nodes = connect_to_upstream(nodes, streams)
        expected_node_count = 7
        self.assertEqual(expected_node_count, len(nodes))

    def test_build_graph(self) -> None:
        self.test_dir: str = pathlib.Path(__file__).parent.absolute()
        nodes = identify_graph_nodes(self.graph)
        nodes = connect_to_upstream(nodes, self.graph.__streams__.values())
        output_dir = f"{self.test_dir}/output"
        output_file_name = f"{output_dir}/test"
        output_file_format = "svg"

        build_graph("Demo", nodes, output_file_name, output_file_format)
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
