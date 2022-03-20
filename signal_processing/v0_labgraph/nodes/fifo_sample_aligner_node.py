from collections import deque
from functools import reduce
from typing import List

import numpy as np
from labgraph import Node, Sample

EPSILON = 1e-16


class FIFOSampleAlignerNode(Node):
    """
    Node that publishes the first-in-first-out (FIFO) alignment of a set
    of input topics.

    FIFO alignment aligns multiple topics of messages such that the oldest full
    set of messages pushed to each topic is aligned into a single vector and
    output by this node.

    Note: This assumes that the node has WSD data
    (wavelength, source, detector) as a 3 dimensional numpy array
    """

    def __init__(
        self,
        name: str,
        input_topics: [str],
        output_topic: str,
        concatenate_axis: int = 2,
    ) -> None:
        """Keyword arguments:
        name: The name of the node
        input_topics: The set of topics to align
        output_topic: The topic used to publish the aligned sample
        concatenate_axis: The axis in the numpy array which is used for
                          concatenating aligned samples
        """
        super(FIFOSampleAlignerNode, self).__init__(name)
        self.input_topics = input_topics
        self.output_topic = output_topic
        self.concatenate_axis = concatenate_axis
        self.deque_index = {}
        self.deques = []
        for index, input_topic in enumerate(input_topics):
            self.deques.append(deque())
            self.deque_index[input_topic] = index

    def subscribe_topics(self) -> List[str]:
        return self.input_topics

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def process(self, topic: str, sample: Sample) -> None:
        assert topic in self.deque_index.keys()
        self.deques[self.deque_index[topic]].append(sample)

        if not any(len(current_deque) == 0 for current_deque in self.deques):
            # Filter all sources by source type
            num_sources = 0
            num_detectors = 0
            for current_deque in self.deques:
                data_shape = np.shape(current_deque[0].data)
                num_sources += data_shape[0]
                num_detectors += data_shape[1]
            new_data = np.zeros(
                (num_sources, num_detectors, 2)  # 2 wavelengths, R and IR
            )

            source_offset = 0
            detector_offset = 0
            for deque_index in range(len(self.deques)):
                inserted_sample = self.deques[deque_index][0]
                data_shape = np.shape(inserted_sample.data)
                new_data[
                    source_offset : source_offset + data_shape[0],
                    detector_offset : detector_offset + data_shape[1],
                    :,
                ] = inserted_sample.data

                source_offset += data_shape[0]
                detector_offset += data_shape[1]

                self.deques[deque_index].popleft()

            new_sample = self.create_processed_sample(sample, new_data)
            new_sample.sender = self.name
            self.publish(self.output_topic, new_sample)
