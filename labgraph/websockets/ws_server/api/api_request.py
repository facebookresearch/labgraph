#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import json
from json.decoder import JSONDecodeError

from ....util.logger import get_logger


logger = get_logger(__name__)


class APIRequest:
    def __init__(self, msg: str, enums: object):
        self.enums: object = enums
        self.API: object = enums.API
        API = enums.API
        self.STREAM: object = self.enums.STREAM

        request = self.json_decode_msg(msg)
        self.msg: str = msg

        self.api_version: str = request[API.API_VERSION]
        for field, value in request[API.API_REQUEST].items():
            if field == API.REQUEST_ID:
                self.request_id: int = value
            else:
                self.request_type: str = field
                for request_type, request_value in value.items():
                    if request_type == API.STREAM_ID:
                        self.stream_id: str = request_value
                    elif request_type == API.APP_ID:
                        self.app_id: str = request_value
                    else:
                        self.stream_name: str = request_type

    def json_decode_msg(self, msg: str) -> str:
        try:
            request = json.loads(msg)
        except JSONDecodeError as e:
            raise JSONDecodeError(e)
        except TypeError as e:
            raise TypeError(e)

        if self.enums.API.API_VERSION not in request:
            raise JSONDecodeError("Api version is not available.")

        if self.enums.API.API_REQUEST not in request.keys():
            raise JSONDecodeError("Api request is not available.")

        return request

    def update_stream_request(self, base_stream_msg: str) -> str:
        API = self.API
        base_stream_msg[API.API_EVENT][API.REQUEST_ID] = self.request_id
        base_stream_msg[API.API_EVENT][API.START_STREAM_EVENT][
            API.STREAM_ID
        ] = self.stream_id
        return base_stream_msg

    def is_labgraph_monitor(self) -> bool:
        return self.stream_name == self.STREAM.LABGRAPH_MONITOR

    def is_start_stream_request(self) -> bool:
        return self.request_type == self.API.START_STREAM_REQUEST

    def is_end_stream_request(self) -> bool:
        return self.request_type == self.API.END_STREAM_REQUEST
