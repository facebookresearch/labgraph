#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from strenum import StrEnum


class LabGraphBuiltinUnits(StrEnum):

    MESSAGE = "Message"
    CONFIG = "Config"
    STATE = "State"
    NODE = "Node"
    GROUP = "Group"
    GRAPH = "Graph"
