from typing import List, Callable

import numpy as np
from labgraph import Node, Sample


class SampleBufferingNode(Node):
    """
    Node that collects a set of messages into a queue and buffers it until
    the queue exceeds its threshold size. Once the threshold is met, the
    node outputs a message containing data of the threshold size.
    """

    def __init__(
        self,
        name: str,
        input_topic: str,
        output_topic: str,
        threshold: int,
        concatenate_axis: int = 2,
    ) -> None:
        """Keyword arguments:
        name: The name of the node
        input_topics: The input topic to buffer
        output_topic: The topic used to publish the buffered sample
        threshold: The threshold number of data to buffer
        concatenate_axis: The axis in the numpy array which is used for
                          concatenating aligned samples
        """
        super(SampleBufferingNode, self).__init__(name)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.threshold = threshold
        self.concatenate_axis = concatenate_axis

        # Data stored as SDW values (source, detector, wavelength)
        self.data = None

    def subscribe_topics(self) -> List[str]:
        return [self.input_topic]

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def process(self, topic: str, sample: Sample) -> None:
        assert topic == self.input_topic
        # The length of the sample data must be less than or
        # equal to the threshold for buffering to be valid,
        # otherwise some messages will be delayed.
        assert np.shape(sample.data)[self.concatenate_axis] <= self.threshold

        if self.data is None:
            self.data = sample.data
        else:
            self.data = np.concatenate(
                (self.data, sample.data), axis=self.concatenate_axis
            )

        if (
            not self.data is None
            and np.shape(self.data)[self.concatenate_axis] >= self.threshold
        ):
            # Publish buffered data
            new_data = self.data[:, :, : self.threshold]
            new_sample = self.create_processed_sample(sample, new_data)
            new_sample.sender = self.name
            self.publish(self.output_topic, new_sample)

            # Remove old buffer, preserving the remainder
            self.data = self.data[:, :, self.threshold :]
