#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
import labgraph as lg
from extensions.graphviz_support.graphviz_support.tests.demo_graph.demo import Demo
from ..generate_lg_monitor.generate_lg_monitor import (
    identify_upstream_message,
    identify_graph_nodes,
    out_edge_node_mapper,
    in_out_edge_mapper,
    connect_to_upstream,
    serialize_graph,
)


class TestLabgraphMonitorAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.graph: lg.Graph = Demo()

    def test_identify_upstream_message(self) -> None:
        upstream_message = identify_upstream_message(
            'ROLLING_AVERAGER/ROLLING_AVERAGER_INPUT',
            self.graph.__topics__
        )

        self.assertEqual('RandomMessage', upstream_message.name())

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

    def test_serialize_graph(self) -> None:
        serialized_graph = serialize_graph(self.graph)

        self.assertEqual('Demo', serialized_graph["name"])
        self.assertEqual(5, len(serialized_graph["nodes"]))


if __name__ == "__main__":
    unittest.main()
