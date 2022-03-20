#! /usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
from typing import List, Tuple, Optional, Any

import numpy as np
from labgraph.graph import Node
from labgraph.sample import Sample

SAMPLE_RATE = 10  # Hz


# Publishes Gaussian noise to some specified topics
class GaussianNoiseNode(Node):
    def __init__(
        self,
        name: str,
        output_topic: str,
        mean: np.ndarray,
        cov: np.ndarray,
        size: np.ndarray,
    ) -> None:
        """
        :arg mean: 1-d, of length N
        :arg cov: 2-d, of shape (N, N). Must be symmetric and PSD.
        """
        super(GaussianNoiseNode, self).__init__(name)
        self.output_topic = output_topic
        self.mean = mean
        self.cov = cov
        self.size = size

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def main(self) -> None:
        last_data_send = None
        while self.is_running():
            # Impose a max sampling rate
            if last_data_send:
                current_time = time.time()
                expected_wait = 1 / SAMPLE_RATE
                actual_wait = current_time - last_data_send
                if actual_wait < expected_wait:
                    time.sleep(expected_wait - actual_wait)
            self.publish(self.output_topic, self._generate_sample())
            last_data_send = time.time()

    def _generate_sample(self) -> Sample:
        data = np.random.multivariate_normal(
            mean=self.mean, cov=self.cov, size=self.size
        )
        sample = Sample(timestamp=time.time(), data=data)
        return sample
