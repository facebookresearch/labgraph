#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from .enums_base import ENUMS as ENUMS_base
class STREAM_LISTS:
    supported_stream_list = [
        "labgraph.monitor",
    ]

    sleep_pause_streams = supported_stream_list

class ENUMS:
    API = ENUMS_base.API
    WS_SERVER = ENUMS_base.WS_SERVER
    STREAM = ENUMS_base.STREAM
    STREAM_LISTS = STREAM_LISTS