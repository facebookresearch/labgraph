# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, List

from labgraph import Node


class DownSamplingNode(Node):
    """
    DownSamplingNode
    Subscribes to a topic and downsamples according to a given rate

    Ex.
    input_topic_samples = [0,1,2,3,4,5,6,7,8,9]

    rate=3 -> [2,5,8]
    rate=5 -> [4,9]

    The rest of the samples are not published to the output_topic
    """

    def __init__(
        self, name: str, input_topic: str, output_topic: str, rate: int
    ) -> None:

        super(DownSamplingNode, self).__init__(name)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.rate = rate
        self.n = 0

    def subscribe_topics(self) -> List[str]:
        return [self.input_topic]

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def process(self, topic: str, result: Any) -> None:
        self.n += 1
        if self.n >= self.rate:
            self.n = 0
            self.publish(self.output_topic, result)
            return
