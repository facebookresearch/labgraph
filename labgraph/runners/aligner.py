#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import collections
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .._cthulhu.cthulhu import LabGraphCallback, LabGraphCallbackParams
from ..messages.message import TimestampedMessage
from ..util.error import LabGraphError
from ..util.min_heap import MinHeap


class Aligner(ABC):
    """
    Base aligner class which all future aligners should inherit from.
    All runners may optionally carry an aligner.

    Methods:
        register(stream_id, callback):
            Called to register a subscribing callback onto the stream
            with the given id.
        push(stream_id, message):
            Called to add a message to the aligner's message buffer.
        get_aligned():
            Periodically called in order to re-publish messages
            to subscribing callbacks, if applicable.
        wait_for_completion():
            Called at the end of the runner's lifecycle to terminate
            the aligner, waiting first for remaining messages to be published.
    """

    @abstractmethod
    def register(self, stream_id: str, callback: LabGraphCallback) -> None:
        pass

    @abstractmethod
    def push(self, params: LabGraphCallbackParams[Any]) -> None:
        pass

    @abstractmethod
    async def get_aligned(self) -> None:
        pass

    @abstractmethod
    def wait_for_completion(self) -> None:
        pass

    @abstractmethod
    async def run(self) -> None:
        pass


TimestampedHeapEntry = Tuple[
    float, int, str, LabGraphCallbackParams[TimestampedMessage]
]

TimestampedHeap = MinHeap[TimestampedHeapEntry]
"""
The heap used by a TimestampAligner to determine the order of aligned messages.
"""


class TimestampAligner(Aligner):
    """
    Default aligner used to align messages from multiple incoming streams.
    Subscribers which intend to receive messages from the aligner must
    first register themselves to the aligner; after the provided lag period,
    any messages in the buffer will be re-published in chronological order.

    Unless explicitly told to terminate, the aligner continues running until
    either i) all messages in the buffer have been delivered, or if ii) the
    runner associated with the aligner is still "active"--i.e. more messages
    are likely to require processing by the aligner in the future.

    Args:
        lag: The time lag during which incoming messages are buffered.
    """

    def __init__(self, lag: float) -> None:
        # Min-heap containing all messages, sorted by timestamp
        # HACK: Avoiding pickling issues by deferring construction of heap
        self._pq: Optional[TimestampedHeap] = None

        # Lag (in seconds) during which incoming messages are buffered
        self.lag: float = lag
        # Callbacks keyed by the id of the stream they're subscribing to
        self.callbacks: Dict[str, List[LabGraphCallback]] = collections.defaultdict(
            list
        )

        self.active: bool = True  # Current state of associated runner
        self.terminate: bool = False  # Flag to quit immediately

    def register(self, stream_id: str, callback: LabGraphCallback) -> None:
        self.callbacks[stream_id].append(callback)

    def push(self, params: LabGraphCallbackParams[TimestampedMessage]) -> None:
        message = params.message
        if params.stream_id is None:
            raise LabGraphError(
                "TimestampAligner::push expected stream id, but got None."
            )
        heap_entry: TimestampedHeapEntry = (
            message.timestamp,
            self.pq.count,
            params.stream_id,
            params,
        )
        self.pq.push(heap_entry)

    async def get_aligned(self) -> None:
        now = time.time()
        while self.pq and (self.pq[0][0] + self.lag < now):
            _, _, stream_id, next_params = self.pq.pop()
            for callback in self.callbacks[stream_id]:
                callback(next_params.message)

    def wait_for_completion(self) -> None:
        self.active = False

    def stop(self) -> None:
        self.terminate = True

    async def run(self) -> None:
        # Continue running as long as runner is active/buffer not empty
        while not self.terminate and (self.active or self.pq):
            await asyncio.sleep(0.001)
            await self.get_aligned()

    @property
    def pq(self) -> TimestampedHeap:
        if self._pq is None:
            self._pq = TimestampedHeap()
        return self._pq
