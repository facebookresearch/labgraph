#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import TypeVar, Generic, List, Optional

HeapEntry = TypeVar("HeapEntry")


@dataclass
class MinHeap(Generic[HeapEntry]):
    count = 0
    heap: List[HeapEntry] = field(default_factory=list)

    def push(self, entry: HeapEntry) -> None:
        heappush(self.heap, entry)
        self.count += 1

    def pop(self) -> HeapEntry:
        return heappop(self.heap)

    def __getitem__(self, index: int) -> HeapEntry:
        return self.heap[index]

    def __len__(self) -> int:
        return len(self.heap)
