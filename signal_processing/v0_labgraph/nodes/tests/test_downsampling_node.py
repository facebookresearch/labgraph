import time
import unittest

import numpy as np
from ..nodes import DownSamplingNode
from labgraph import Graph, TopicInfo, Sample


class DownsampleNodeTestGraph(Graph):
    def setup(self) -> None:
        self.add_topic(TopicInfo("downsample_3", Sample))
        self.add_topic(TopicInfo("downsample_5", Sample))
        self.add_topic(TopicInfo("samples", Sample))
        self.add_node(
            DownSamplingNode("downsample_3_node", "samples", "downsample_3", rate=3)
        )
        self.add_node(
            DownSamplingNode("downsample_5_node", "samples", "downsample_5", rate=5)
        )


class DownsampleNodeTest(unittest.TestCase):
    def test_log_node(self) -> None:
        graph = DownsampleNodeTestGraph()
        downsample_3_outlet = graph.create_outlet_channel("downsample_3")
        downsample_5_outlet = graph.create_outlet_channel("downsample_5")

        downsample_3 = []
        downsample_5 = []

        with graph:
            print("TEST")
            time.sleep(0.3)
            for i in range(10):
                print(i)
                graph.broadcast("samples", Sample(time.time(), i))

            for i in range(3):
                downsample_3.append(downsample_3_outlet.poll())
            for i in range(2):
                downsample_5.append(downsample_5_outlet.poll())

            self.assertEqual([d.data for d in downsample_3], [2, 5, 8])
            self.assertEqual([d.data for d in downsample_5], [4, 9])


if __name__ == "__main__":
    unittest.main()
