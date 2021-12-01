#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

sample_stream_mock_data = [
    0.318167576566339e-03,
    1.426322215702385e-03,
    2.426322215702385e-03,
    3.855793329421431e-03,
    4.462373883347027e-03,
    5.390270911855623e-03,
    6.354219608008862e-03,
    7.105006468715146e-03,
    8.747638690285385e-03,
    9.105006468715146e-03,
    0.783689994132146e-03,
    1.498425914789555e-03,
    2.711586658842862e-03,
    3.462373883347027e-03,
    4.711586658842862e-03,
    5.462373883347027e-03,
]

samples_labgraph_monitor_mock_data = [
    {
        "data": {
            "streamer": {
                "device.stream1": {
                    "active": True,
                    "api_stream_name": "device.stream1",
                    "batch_interval_avg_ms": 10.97996867275964,
                    "batch_interval_jitter_ms": 5.5137354718031384,
                    "batch_size_avg": 100.320561486122386,
                    "sample_frequency": 500.3515645434395,
                    "sample_input_lag_ms": 0,
                    "source": {"device": "stream1"},
                    "streaming_to_api": False,
                    "targets": {},
                    "total_batch_count": 1000,
                    "total_sample_count": 50000,
                },
            },
            "transform": {
                "device": {
                    "active": True,
                    "input_ports": [],
                    "node_latency": 20969.667210362495,
                    "output_ports": [
                        "stream1",
                    ],
                    "path_latency": 10969.667210362495,
                    "transform_latency_avg_ms": 11.15662476670685,
                    "transform_latency_jitter_ms": 1.9629780462581925,
                    "type": "source",
                },
            },
        },
        "produced_timestamp_s": 1633210288.030802,
        "timestamp_s": 1633210288.030802,
    },
]
