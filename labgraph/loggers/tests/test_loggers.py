#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import random
import time
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..._cthulhu.cthulhu import Mode, Producer, register_stream
from ...graphs.parent_graph_info import ParentGraphInfo
from ...graphs.stream import Stream
from ...messages.message import Message
from ...util.random import random_string
from ...util.testing import get_event_loop, local_test
from ..logger import Logger, LoggerConfig


NUM_MESSAGES_PER_STREAM = 100
MESSAGE_RATE = 100


class MyMessage1(Message):
    int_field: int


class MyMessage2(Message):
    str_field: str


class MyMessage3(Message):
    bool_field: bool


class NaiveLogger(Logger):
    """
    Naive logger for testing that simply appends messages to a buffer. Also adds a @main
    method that kills the
    """

    def setup(self) -> None:
        super().setup()
        self.output: Dict[str, List[Message]] = {}

    def write(self, messages_by_logging_id: Mapping[str, Sequence[Message]]) -> None:
        for logging_id, messages in messages_by_logging_id.items():
            if logging_id not in self.output:
                self.output[logging_id] = list(messages)
            else:
                self.output[logging_id] += list(messages)


@local_test
def test_logger() -> None:
    """
    Test that the naive logger receives all messages sent via Cthulhu.
    """
    logging_ids = (random_string(16), random_string(16), random_string(16))
    stream_ids = (random_string(16), random_string(16), random_string(16))
    message_types = (MyMessage1, MyMessage2, MyMessage3)
    streams_by_logging_id = {
        logging_ids[i]: Stream(
            id=stream_ids[i],
            topic_paths=(f"MY_NODE/{'ABC'[i]}",),
            message_type=message_types[i],
        )
        for i in range(3)
    }

    cthulhu_streams_by_id = {
        stream_ids[i]: register_stream(
            name=stream_ids[i], message_type=message_types[i]
        )
        for i in range(3)
    }

    producers = {
        stream_id: Producer(stream_interface=stream_interface, mode=Mode.SYNC)
        for stream_id, stream_interface in cthulhu_streams_by_id.items()
    }

    producers_and_messages: List[Tuple[Producer, Message]] = []
    for i in range(NUM_MESSAGES_PER_STREAM):
        producers_and_messages.append(
            (producers[stream_ids[0]], MyMessage1(int_field=i))
        )
        producers_and_messages.append(
            (producers[stream_ids[1]], MyMessage2(str_field=str(i)))
        )
        producers_and_messages.append(
            (producers[stream_ids[2]], MyMessage3(bool_field=i % 2 == 0))
        )
    random.shuffle(producers_and_messages)
    messages = [p[1] for p in producers_and_messages]

    config = LoggerConfig(streams_by_logging_id=streams_by_logging_id)
    logger = NaiveLogger()
    logger.configure(config)
    logger.setup()

    import asyncio

    loop = get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            logger.run_logger(), _write_messages(logger, producers_and_messages)
        )
    )

    logger.cleanup()

    for producer in producers.values():
        producer.close()

    expected_int_values = [
        message.int_field for message in messages if isinstance(message, MyMessage1)
    ]
    actual_int_values = [message.int_field for message in logger.output[logging_ids[0]]]
    assert sorted(expected_int_values) == sorted(actual_int_values)

    expected_str_values = [
        message.str_field for message in messages if isinstance(message, MyMessage2)
    ]
    actual_str_values = [message.str_field for message in logger.output[logging_ids[1]]]
    assert sorted(expected_str_values) == sorted(actual_str_values)

    expected_bool_values = [
        message.bool_field for message in messages if isinstance(message, MyMessage3)
    ]
    actual_bool_values = [
        message.bool_field for message in logger.output[logging_ids[2]]
    ]
    assert sorted(expected_bool_values) == sorted(actual_bool_values)


async def _write_messages(
    logger: Logger, producers_and_messages: List[Tuple[Producer, Message]]
) -> None:
    import asyncio

    for producer, message in producers_and_messages:
        producer.produce_message(message)
        await asyncio.sleep(1.0 / MESSAGE_RATE)

    logger.running = False
