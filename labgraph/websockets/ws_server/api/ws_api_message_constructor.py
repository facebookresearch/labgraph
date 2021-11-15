#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

"""
This file defines functions for building LabGraph WS API compliant messages.
"""

import time
from typing import Dict, Any

import numpy


def get_start_stream_request(
    stream_id: str,
    request_id: int,
    api_version: str,
) -> str:
    """
    Parameters
    ----------
    stream_id:
        ID for the data stream
    request_id:
        ID for StartStreamRequest

    Returns
    -------
    API Message.
    """
    api_message: Dict[str, Any] = {
        "api_version": api_version,
        "api_event": {
            "request_id": request_id,
            "start_stream_event": {"stream_id": stream_id},
        },
    }

    return api_message


def get_start_stream_request_error(
    stream_id: str,
    request_id: int,
    api_version: str,
) -> str:
    """
    Parameters
    ----------
    stream_id:
        ID for the data stream
    request_id:
        ID for StartStreamRequest

    Returns
    -------
    API Message.
    """
    api_message: Dict[str, Any] = {
        "api_version": api_version,
        "api_event": {
            "error_event": {
                "desc": "Session used stream name: "
                + stream_id
                + ", which does not exist",
                "error_code": "NonExistentStream",
            },
            "request_id": request_id,
        },
    }

    return api_message


def get_end_stream_request(
    stream_id: str,
    request_id: int,
    api_version: str,
) -> str:
    """
    Parameters
    ----------
    stream_id:
        ID for the data stream
    request_id:
        ID for EndStreamRequest

    Returns
    -------
    API Message.
    """
    api_message: Dict[str, Any] = {
        "api_version": api_version,
        "api_event": {
            "request_id": request_id,
            "end_stream_event": {"stream_id": stream_id},
        },
    }

    return api_message


def get_sample_data(data: numpy.ndarray, produced_timestamp_s: float) -> Dict:
    """
    Parameters
    ----------
    target:
        Type of data stream
        (raw_emg_target, hand_skeleton_target, or raw_imu_target)
    stream_id:
        ID for the data stream
    request_id:
        ID for StartStreamRequest

    Returns
    -------
    Serialized StartStreamRequest with specified target
    """
    sample_data_message: Dict = {
        "data": data,
        "produced_timestamp_s": produced_timestamp_s,
        "timestamp_s": time.time(),
    }

    return sample_data_message
