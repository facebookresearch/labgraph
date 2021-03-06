#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.


class API:
    API_EVENT = "api_event"
    API_REQUEST = "api_request"
    API_VERSION = "api_version"

    REQUEST_ID = "request_id"
    STREAM_ID = "stream_id"
    APP_ID = "app_id"

    START_STREAM_EVENT = "start_stream_event"
    END_STREAM_EVENT = "end_stream_event"
    START_STREAM_REQUEST = "start_stream_request"
    END_STREAM_REQUEST = "end_stream_request"


class WS_SERVER:
    DEFAULT_API_VERSION = "0.1"
    DEFAULT_IP = "127.0.0.1"
    DEFAULT_PORT = 9000


class STREAM:
    LABGRAPH_MONITOR = "labgraph.monitor"
    LABGRAPH_MONITOR_ID = "LABGRAPH.MONITOR"


class ENUMS:
    API = API()
    WS_SERVER = WS_SERVER()
    STREAM = STREAM()
