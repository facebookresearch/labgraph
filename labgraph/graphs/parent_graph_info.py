#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import multiprocessing as mp
from dataclasses import dataclass


@dataclass
class ParentGraphInfo:
    """
    Contains information about a module or logger's parent graph.

    Args:
        graph_id: The id of the parent graph, determined at runtime.
        barrier: The barrier to use to coordinate startup with other modules.
    """

    graph_id: str
    startup_barrier: mp.Barrier  # type: ignore
