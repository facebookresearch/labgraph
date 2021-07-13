#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time

import pytest

from ...messages.message import Message
from ...util.random import random_string
from ...util.testing import local_test
from ..cthulhu import Consumer, LabGraphCallbackParams, Producer, register_stream


RANDOM_ID_LENGTH = 128
NUM_MESSAGES = 100
SAMPLE_RATE = 100


class MyMessage(Message):
    int_field: int


@local_test
def test_producer_and_consumer() -> None:
    """
    Tests that we can use the LabGraph wrappers around the Cthulhu APIs to publish
    and subscribe to messages.
    """
    stream_name = random_string(length=RANDOM_ID_LENGTH)
    stream_interface = register_stream(name=stream_name, message_type=MyMessage)

    received_messages = []

    with Producer(stream_interface=stream_interface) as producer:

        def callback(params: LabGraphCallbackParams[MyMessage]) -> None:
            received_messages.append(params.message)

        with Consumer(stream_interface=stream_interface, sample_callback=callback):

            for i in range(NUM_MESSAGES):
                producer.produce_message(MyMessage(int_field=i))
                time.sleep(1 / SAMPLE_RATE)

    assert len(received_messages) == NUM_MESSAGES

    for i in range(NUM_MESSAGES):
        assert received_messages[i].int_field == i


@local_test
def test_complex_graph() -> None:
    """
    Tests that we can use the LabGraph wrappers around the Cthulhu APIs to stream
    messages in a more complex graph.
    """
    stream_name1 = random_string(length=RANDOM_ID_LENGTH)
    stream_name2 = random_string(length=RANDOM_ID_LENGTH)
    stream1 = register_stream(name=stream_name1, message_type=MyMessage)
    stream2 = register_stream(name=stream_name2, message_type=MyMessage)

    received_messages = []

    with Producer(stream_interface=stream1) as producer1:

        with Producer(stream_interface=stream2) as producer2:

            def transform_callback(params: LabGraphCallbackParams[MyMessage]) -> None:
                producer2.produce_message(
                    MyMessage(int_field=params.message.int_field * 2)
                )

            with Consumer(stream_interface=stream1, sample_callback=transform_callback):

                def sink_callback(params: LabGraphCallbackParams[MyMessage]) -> None:
                    received_messages.append(params.message)

                with Consumer(stream_interface=stream2, sample_callback=sink_callback):
                    for i in range(NUM_MESSAGES):
                        producer1.produce_message(MyMessage(int_field=i))
                        time.sleep(1 / SAMPLE_RATE)

    assert len(received_messages) == NUM_MESSAGES

    for i in range(NUM_MESSAGES):
        assert received_messages[i].int_field == i * 2
