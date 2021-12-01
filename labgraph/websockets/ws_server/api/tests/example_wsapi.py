#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

start_stream_request = {
    "api_event": {
        "request_id": 1,
        "start_stream_event": {"stream_id": "LABGRAPHMONITOR"},
    },
    "api_version": "0.1",
}

start_stream_msg = {
    "api_event": {
        "request_id": 2,
        "start_stream_event": {"stream_id": "DEVICE.STREAM1"},
    },
    "api_version": "0.1",
}

end_stream_request = {
    "api_event": {
        "request_id": 1,
        "end_stream_event": {"stream_id": "LABGRAPHMONITOR"},
    },
    "api_version": "0.1",
}

start_stream_request_client = {
    "api_version": "0.1",
    "api_request": {
        "start_stream_request": {
            "stream_id": "DEVICE.STREAM1",
            "app_id": "test_app_id",
            "device.stream1": {},
        },
        "request_id": 1,
    },
}

stream_msg_sample = {
    "stream_batch": {
        "device.stream1": {
            "batch_num": 1,
            "samples": [
                {
                    "data": [
                        1.1,
                        -2.2,
                        3.3,
                        4.4,
                        5.5,
                        -6.6,
                        7.7,
                        -8.8,
                    ],
                    "produced_timestamp_s": 1636699176.74837,
                    "timestamp_s": 1636699176.74837,
                },
                {
                    "data": [
                        -1.1,
                        -2.2,
                        3.3,
                        4.4,
                        -5.5,
                        -6.6,
                        -7.7,
                        8.8,
                    ],
                    "produced_timestamp_s": 1635456691.07837,
                    "timestamp_s": 1635456691.07837,
                },
            ],
        },
        "stream_id": "stream1-000-11ok",
    },
    "api_version": "0.1",
}
