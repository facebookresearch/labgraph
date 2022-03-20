#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import math
import time
import unittest

import numpy as np
from ..nodes.gaussian_noise_node import GaussianNoiseNode
from labgraph.graph import Graph, TopicInfo
from labgraph.sample import Sample

SLEEP_TIME = 0.3


class TestNoiseGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("std_gaussian", Sample))
        self.add_node(
            GaussianNoiseNode(
                name="std_gaussian",
                output_topic="std_gaussian",
                mean=np.array([0]),
                cov=np.array([[1]]),
                size=np.array([500]),
            )
        )

        self.add_topic(TopicInfo("mv_gaussian", Sample))
        self.add_node(
            GaussianNoiseNode(
                name="mv_gaussian",
                output_topic="mv_gaussian",
                mean=np.array([0, 100]),
                cov=np.array([[4, 0], [0, 1]]),
                size=np.array([500]),
            )
        )


class TestGaussianNoiseNode(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = TestNoiseGraph()

    def test_gaussian_noise_node(self) -> None:
        graph = self.graph
        outlet_1 = graph.create_outlet_channel("std_gaussian")
        outlet_2 = graph.create_outlet_channel("mv_gaussian")

        graph.start()
        time.sleep(SLEEP_TIME)

        outlet_1_samples = np.concatenate(
            (outlet_1.poll().data, outlet_1.poll().data), axis=0
        )
        self.assertEqual((1000, 1), outlet_1_samples.shape)
        self.assertTrue(np.isclose(0, np.mean(outlet_1_samples), atol=0.5))
        self.assertTrue(np.isclose(1, np.var(outlet_1_samples), atol=0.5))

        outlet_2_samples = np.concatenate(
            (outlet_2.poll().data, outlet_2.poll().data), axis=0
        )
        self.assertEqual((1000, 2), outlet_2_samples.shape)
        self.assertTrue(
            np.allclose([0, 100], np.mean(outlet_2_samples, axis=0), atol=0.5)
        )
        self.assertTrue(
            np.allclose(
                [[4, 0], [0, 1]], np.cov(outlet_2_samples, rowvar=False), atol=0.5
            )
        )

    def tearDown(self) -> None:
        self.graph.stop()


if __name__ == "__main__":
    unittest.main()
