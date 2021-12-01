#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import json
from typing import Dict, Any


def get_start_stream_request(
    target: str, stream_id: str, request_id: int, api_version: str, app_id: str = ""
) -> str:
    """
    Parameters
    ----------
    target:
        Type of data stream
        (device.stream1)
    stream_id:
        ID for the data stream
    request_id:
        ID for StartStreamRequest

    Returns
    -------
    Serialized StartStreamRequest with specified target
    """
    api_message: Dict[str, Any] = {
        "api_version": api_version,
        "api_request": {
            "request_id": request_id,
            "start_stream_request": {"stream_id": stream_id, target: {}},
        },
    }

    if app_id:
        api_message["api_request"]["start_stream_request"]["app_id"] = app_id

    return json.dumps(api_message)


def get_end_stream_request(stream_id: str, request_id: int, api_version: str) -> str:
    """
    Parameters
    ----------
    stream_id:
        ID of stream we want to stop
    request_id:
        ID of EndStreamRequest

    Returns
    -------
    Serialized EndStreamRequest
    """
    api_message = {
        "api_version": api_version,
        "api_request": {
            "request_id": request_id,
            "end_stream_request": {"stream_id": stream_id},
        },
    }

    return json.dumps(api_message)
