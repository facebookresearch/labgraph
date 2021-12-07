#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import labgraph as lg
from .test_lg_unit_node import MyNode
from .test_lg_unit_group import MyGroup
from typing import Tuple


class MyGraph(lg.Graph):
    GROUP: MyGroup
    NODE: MyNode

    def setup(self) -> None:
        pass

    def connections(self) -> lg.Connections:
        pass

    def process_modules(self) -> Tuple[lg.Module, ...]:
        pass
