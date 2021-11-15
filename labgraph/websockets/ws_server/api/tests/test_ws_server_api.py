#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import json

from ...tests.enums import ENUMS, WS_SERVER, STREAM, API
from ..api_request import APIRequest
from ..ws_api_message_constructor import (
    get_start_stream_request,
    get_end_stream_request,
)
from .example_wsapi import (
    start_stream_request,
    end_stream_request,
    start_stream_request_client,
)


class TestWSServerAPI:
    def test_get_start_stream_request(self) -> None:
        api_start_stream_request = get_start_stream_request(
            stream_id=STREAM.LABGRAPH_MONITOR_ID,
            request_id=1,
            api_version=WS_SERVER.DEFAULT_API_VERSION,
        )

        assert api_start_stream_request == start_stream_request

    def test_get_end_stream_request(self) -> None:
        api_end_stream_request = get_end_stream_request(
            stream_id=STREAM.LABGRAPH_MONITOR_ID,
            request_id=1,
            api_version=WS_SERVER.DEFAULT_API_VERSION,
        )

        assert api_end_stream_request == end_stream_request

    def test_api_request(self) -> None:
        api_request = APIRequest(
            msg=json.dumps(start_stream_request_client),
            enums=ENUMS,
        )

        assert api_request.api_version == WS_SERVER.DEFAULT_API_VERSION

        assert (
            api_request.request_id
            == start_stream_request_client[API.API_REQUEST][API.REQUEST_ID]
        )

        assert api_request.stream_id == STREAM.DEVICE_STREAM1_ID

        assert api_request.stream_name == STREAM.DEVICE_STREAM1

        assert api_request.request_type == API.START_STREAM_REQUEST

        assert (
            api_request.app_id
            == start_stream_request_client[API.API_REQUEST][API.START_STREAM_REQUEST][
                API.APP_ID
            ]
        )
