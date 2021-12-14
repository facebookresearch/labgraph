#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import heapq
import itertools
import typing
from threading import Lock


class Empty(Exception):
    pass


class Full(Exception):
    pass


class PriorityQueue:
    """
    A priority queue implementation that keeps track of entries.
    Re-queueing an existing entry will update it's priority.
    """

    def __init__(
        self,
        max_size: int = 500,
        tie_breaker: typing.Optional[typing.Generator[float, None, None]] = None,
    ) -> None:
        self._max_size = max_size
        self._tie_breaker = tie_breaker if tie_breaker else itertools.count()
        self._queue = []
        self._lock = Lock()

    def push(self, data: typing.Any, priority: int) -> None:
        with self._lock:
            if len(self._queue) == self._max_size:
                raise Full("Priority queue is full")
            curr = [priority, next(self._tie_breaker), data]
            heapq.heappush(self._queue, curr)

    def pop(self) -> typing.Any:
        with self._lock:
            if not self._queue:
                raise Empty("Priority queue is empty")
            priority, tie_breaker, data = heapq.heappop(self._queue)
            return data
