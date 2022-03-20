#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
import unittest

import numpy as np
from ..nodes import FIFOSampleAlignerNode
from ..nodes.logarithm_node import EPSILON
from labgraph import Graph, TopicInfo, Sample


class FIFOSampleAlignerTestGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("log10", Sample))
        self.add_topic(TopicInfo("log12", Sample))
        self.add_topic(TopicInfo("samples.left", Sample))
        self.add_topic(TopicInfo("samples.right", Sample))
        self.add_topic(TopicInfo("aligned_samples", Sample))
        self.add_node(
            FIFOSampleAlignerNode(
                "fifo_aligner", ["samples.left", "samples.right"], "aligned_samples"
            )
        )


class FIFOSampleAlignerNodeTest(unittest.TestCase):
    def test_log_node(self) -> None:
        graph = FIFOSampleAlignerTestGraph()
        aligned_samples_outlet = graph.create_outlet_channel("aligned_samples")

        with graph:
            time.sleep(0.3)
            for _ in range(100):
                left_data = (np.random.rand(54, 26, 2) * 4096).astype(int)
                right_data = (np.random.rand(54, 26, 2) * 4096).astype(int)
                aligned_data = np.zeros((108, 52, 2))
                aligned_data[:54, :26, :] = left_data
                aligned_data[54:, 26:, :] = right_data
                graph.broadcast("samples.left", Sample(time.time(), left_data))
                graph.broadcast("samples.right", Sample(time.time(), right_data))
                aligned_samples = aligned_samples_outlet.poll()

                self.assertTrue(
                    np.shape(aligned_samples.data) == np.shape(aligned_data)
                )
                self.assertTrue(np.allclose(aligned_samples.data, aligned_data))


if __name__ == "__main__":
    unittest.main()
