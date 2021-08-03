#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import numpy as np
import time
import zmq

SAMPLE_RATE = 10.0
NUM_FEATURES = 100
ENDPOINT = "tcp://*:5555"
TOPIC = b"randomstream"

# Send samples at the sample rate using zmq. 
def stream_samples(socket):
    c = "|/-\\"
    n = 0
    while True:
        arr = np.random.rand(NUM_FEATURES)
        socket.send_multipart([
            TOPIC,
            arr
        ])
        time.sleep(1 / SAMPLE_RATE)
        n += 1
        print(f"\r{c[n % 4]}", end="")

# Create a sample zmq PUB which publishes to TOPIC at address ENDPOINT
if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(ENDPOINT)

    stream_samples(socket)
