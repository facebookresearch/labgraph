#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.


from .enums import ENUMS as ENUMS_base


class STREAM_LISTS:
    supported_stream_list = [
        "device.stream1",
    ]

    sleep_pause_streams = supported_stream_list


class ENUMS:
    API = ENUMS_base.API
    WS_SERVER = ENUMS_base.WS_SERVER
    STREAM = ENUMS_base.STREAM
    MOCK = ENUMS_base.MOCK
    STREAM_LISTS = STREAM_LISTS
