from typing import List

import numpy as np
from labgraph import Node, Sample

EPSILON = 1e-16


# Node that publishes the log of incoming samples
# The input value to the log function has an epsilon value added to it to avoid
# taking the log of zero
class LogarithmNode(Node):
    def __init__(
        self, name: str, input_topic: str, output_topic: str, base: float = 10
    ) -> None:
        super(LogarithmNode, self).__init__(name)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.base = base

    def subscribe_topics(self) -> List[str]:
        return [self.input_topic]

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def process(self, topic: str, sample: Sample) -> None:
        new_data = np.log10(np.abs(sample.data) + EPSILON) * np.sign(sample.data)
        if self.base != 10:
            new_data /= np.log10(self.base)

        sample = self.create_processed_sample(sample, new_data)
        sample.sender = self.name
        self.publish(self.output_topic, sample)
