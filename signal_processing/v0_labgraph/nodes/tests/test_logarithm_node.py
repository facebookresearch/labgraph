#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
import unittest

import numpy as np
from ..common.nodes import LogarithmNode
from ..nodes.logarithm_node import EPSILON
from labgraph import Graph, TopicInfo, Sample


class LogarithmTestGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("log10", Sample))
        self.add_topic(TopicInfo("log12", Sample))
        self.add_topic(TopicInfo("samples", Sample))
        self.add_node(LogarithmNode("log10", "samples", "log10"))
        self.add_node(LogarithmNode("log12", "samples", "log12", base=12))


class LogarithmNodeTest(unittest.TestCase):
    def test_log_node(self) -> None:
        graph = LogarithmTestGraph()
        log10_outlet = graph.create_outlet_channel("log10")
        log12_outlet = graph.create_outlet_channel("log12")

        with graph:
            time.sleep(0.3)
            for _ in range(100):
                sample = np.random.rand(100)
                graph.broadcast("samples", Sample(time.time(), sample))
                log10 = log10_outlet.poll()
                log12 = log12_outlet.poll()

                self.assertTrue(np.allclose(log10.data, np.log10(sample)))
                self.assertTrue(np.allclose(log12.data, np.log(sample) / np.log(12)))


if __name__ == "__main__":
    unittest.main()
