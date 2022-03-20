#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
import unittest

import numpy as np
from ..common.nodes import SampleBufferingNode
from labgraph import Graph, TopicInfo, Sample


class SampleBufferingTestGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("samples", Sample))
        self.add_topic(TopicInfo("buffered_samples", Sample))
        self.add_node(
            SampleBufferingNode("sample_buffer", "samples", "buffered_samples", 150)
        )


class SampleBufferingNodeTest(unittest.TestCase):
    def test_buffering_node(self) -> None:
        graph = SampleBufferingTestGraph()
        buffered_samples_outlet = graph.create_outlet_channel("buffered_samples")

        with graph:
            time.sleep(0.3)
            for _ in range(100):
                sent_data_0 = np.array([[np.random.rand(100)]])
                sent_data_1 = np.array([[np.random.rand(100)]])
                sent_data_2 = np.array([[np.random.rand(100)]])
                buffered_data_0 = np.concatenate(
                    (sent_data_0, sent_data_1[:, :, :50]), axis=2
                )
                buffered_data_1 = np.concatenate(
                    (sent_data_1[:, :, 50:], sent_data_2), axis=2
                )
                graph.broadcast("samples", Sample(time.time(), sent_data_0))
                graph.broadcast("samples", Sample(time.time(), sent_data_1))
                graph.broadcast("samples", Sample(time.time(), sent_data_2))

                buffered_samples_0 = buffered_samples_outlet.poll()
                buffered_samples_1 = buffered_samples_outlet.poll()

                self.assertTrue(
                    np.shape(buffered_samples_0.data) == np.shape(buffered_data_0)
                )
                self.assertTrue(
                    np.allclose(
                        buffered_samples_0.data[0, 0, :], buffered_data_0[0, 0, :]
                    )
                )
                self.assertTrue(
                    np.shape(buffered_samples_1.data) == np.shape(buffered_data_1)
                )
                self.assertTrue(
                    np.allclose(
                        buffered_samples_1.data[0, 0, :], buffered_data_1[0, 0, :]
                    )
                )


if __name__ == "__main__":
    unittest.main()
