#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
import os
import pathlib
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

class TestLabgraphGraphvizAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.graph: lg.Graph = Demo()


    def test_identify_upstream_message(self) -> None:
        upstream_message = identify_upstream_message(
            'ROLLING_AVERAGER/INPUT',
            self.graph.__topics__
        )

        self.assertEqual('INPUT', upstream_message.name)
        self.assertEqual('RandomMessage', upstream_message.type.__name__)
        

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
            out_edge_node_map['NOISE_GENERATOR/OUTPUT'].name
        )
        self.assertEqual(
            'average',
            out_edge_node_map['ROLLING_AVERAGER/OUTPUT'].name
        )
        self.assertEqual(
            'amplify',
            out_edge_node_map['AMPLIFIER/OUTPUT'].name
        )
        self.assertEqual(
            'attenuate',
            out_edge_node_map['ATTENUATOR/OUTPUT'].name
        )

    def test_in_out_edge_mapper(self) -> None:
        in_out_edge_map = in_out_edge_mapper(self.graph.__streams__.values())
        self.assertEqual(6, len(in_out_edge_map))
        self.assertEqual(
            'NOISE_GENERATOR/OUTPUT',
            in_out_edge_map['ROLLING_AVERAGER/INPUT']
        )
        self.assertEqual(
            'NOISE_GENERATOR/OUTPUT',
            in_out_edge_map['AMPLIFIER/INPUT']
        )
        self.assertEqual(
            'NOISE_GENERATOR/OUTPUT',
            in_out_edge_map['ATTENUATOR/INPUT']
        )
        self.assertEqual(
            'ROLLING_AVERAGER/OUTPUT',
            in_out_edge_map['SINK/INPUT_1']
        )
        self.assertEqual(
            'AMPLIFIER/OUTPUT',
            in_out_edge_map['SINK/INPUT_2']
        )
        self.assertEqual(
            'ATTENUATOR/OUTPUT',
            in_out_edge_map['SINK/INPUT_3']
        )

    def test_connect_to_upstream(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        streams = self.graph.__streams__.values()
        nodes = connect_to_upstream(nodes, streams)
        expected_node_count = 7
        self.assertEqual(expected_node_count, len(nodes))

    def test_serialize_graph(self) -> None:
        nodes = identify_graph_nodes(self.graph)
        nodes = connect_to_upstream(nodes, self.graph.__streams__.values())
        serialized_graph = serialize_graph("Demo", nodes)
        
        self.assertEqual('Demo', serialized_graph["name"])
        self.assertEqual(5, len(serialized_graph["nodes"]))


if __name__ == "__main__":
    unittest.main()
