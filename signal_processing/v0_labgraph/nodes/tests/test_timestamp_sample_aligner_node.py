#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
import unittest

import numpy as np
from ..common.nodes import TimestampSampleAlignerNode
from labgraph import Graph, TopicInfo, Sample


class TimestampSampleAlignerTestGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("samples.left", Sample))
        self.add_topic(TopicInfo("samples.right", Sample))
        self.add_topic(TopicInfo("timestamp_aligned_samples", Sample))
        self.add_node(
            TimestampSampleAlignerNode(
                "timestamp_aligner",
                ["samples.left", "samples.right"],
                "timestamp_aligned_samples",
                threshold=1.0,
            )
        )


class TimestampSampleAlignerNodeTest(unittest.TestCase):
    def test_timestamp_aligner_node(self) -> None:
        graph = TimestampSampleAlignerTestGraph()
        aligned_samples_outlet = graph.create_outlet_channel(
            "timestamp_aligned_samples"
        )

        with graph:
            time.sleep(0.3)
            current_time = 0.0
            timestep = 4.0
            for _ in range(100):
                left_data = (np.random.rand(54, 26, 2) * 4096).astype(int)
                right_data = (np.random.rand(54, 26, 2) * 4096).astype(int)
                second_left_data = (np.random.rand(54, 26, 2) * 4096).astype(int)
                aligned_data = np.zeros((108, 52, 2))
                aligned_data[:54, :26, :] = second_left_data
                aligned_data[54:, 26:, :] = right_data

                graph.broadcast("samples.left", Sample(current_time + 1.0, left_data))
                graph.broadcast("samples.right", Sample(current_time + 3.0, right_data))
                graph.broadcast(
                    "samples.left", Sample(current_time + 3.0, second_left_data)
                )
                aligned_samples = aligned_samples_outlet.poll()

                self.assertTrue(aligned_samples.timestamp == current_time + 3.0)
                self.assertTrue(np.shape(aligned_samples.data) == (108, 52, 2))
                self.assertTrue(np.isclose(aligned_samples.data, aligned_data).all())
                current_time += timestep


if __name__ == "__main__":
    unittest.main()
