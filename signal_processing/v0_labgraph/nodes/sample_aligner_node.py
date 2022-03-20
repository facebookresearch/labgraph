# Copyright 2004-present Facebook. All Rights Reserved.

import collections
import json
import time
from heapq import heappush, heappop
from typing import List, Any, Optional, Dict, Union

from labgraph.graph.node import Node
from labgraph.sample import Sample, AlignedSample
from labgraph.state import State, StateChange


class PriorityQueue(object):
    def __init__(self) -> None:
        self.pq = []
        self.item_dict = {}
        self.count = 0

    def push(self, item: Union[StateChange, Sample]) -> None:
        assert hasattr(item, "timestamp")
        self.count += 1
        heap_entry = [item.timestamp, self.count, item]
        self.item_dict[item] = heap_entry
        heappush(self.pq, heap_entry)

    def pop(self) -> Union[StateChange, Sample]:
        timestamp, count, item = heappop(self.pq)
        del self.item_dict[item]
        return item

    def is_empty(self) -> bool:
        return len(self.pq) == 0

    def clear(self) -> None:
        self.count = 0


class SampleAlignerNode(Node):
    def __init__(self, delay: float) -> None:
        super(SampleAlignerNode, self).__init__("aligner")
        self.delay = delay

    def setup(self) -> None:
        self.message_queue = collections.defaultdict()
        for topic in self.subscribe_topics():
            self.message_queue[topic] = []
        self.publishing_queue = PriorityQueue()
        self.current_state: State = None

    def subscribe_topics(self) -> List[str]:
        return ["experiment_state_changes", "demod_sample"]

    def publish_topics(self) -> List[str]:
        return ["aligned_sample"]

    def process(self, topic: str, result: Any) -> None:
        self.message_queue[topic].append(result)
        self.align_streams()

    def align_streams(self) -> None:
        assert self.publishing_queue.is_empty()
        t = time.time()
        # For each input stream
        for topic, messages in self.message_queue.items():
            # Push messages that have been waited enough to priority queue
            cutoff = 0
            num_msg = len(messages)
            while cutoff < num_msg and messages[cutoff].timestamp + self.delay < t:
                self.publishing_queue.push(messages[cutoff])
                cutoff += 1
            self.message_queue[topic] = messages[cutoff:]

        while not self.publishing_queue.is_empty():
            message = self.publishing_queue.pop()
            if isinstance(message, StateChange):
                self.current_state = message.new_state
            else:
                if self.current_state:
                    self.publish(
                        "aligned_sample",
                        AlignedSample(
                            self.current_state,
                            self.create_processed_sample(message, message.data),
                            sender=self.name,
                        ),
                    )

        # Resets the count of the queue
        self.publishing_queue.clear()

    def cleanup(self) -> None:
        pass
