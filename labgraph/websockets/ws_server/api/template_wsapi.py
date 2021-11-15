#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

start_stream_request = {
    "api_event": {
        "request_id": 1,
        "start_stream_event": {"stream_id": "STREAM_ID"},
    },
    "api_version": "API_VERSION",
}

end_stream_request = {
    "api_event": {
        "request_id": 2,
        "end_stream_event": {"stream_id": "STREAM_ID"},
    },
    "api_version": "API_VERSION",
}

start_stream_request_client = {
    "api_request": {
        "start_stream_request": {
            "stream_id": "STREAM_ID",
            "app_id": "APP_ID",
            "STREAM_NAME": {},
        },
        "request_id": 1,
    },
    "api_version": "API_VERSION",
}

stream_msg_sample = {
    "stream_batch": {
        "STREAM_NAME": {
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
        "STREAM_ID": "stream1-000-11ok",
    },
    "api_version": "API_VERSION",
}
