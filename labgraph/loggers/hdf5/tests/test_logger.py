#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import functools
import random
import tempfile
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import h5py

from ....graphs.graph import Graph
from ....graphs.method import AsyncPublisher, publisher, subscriber
from ....graphs.node_test_harness import run_with_harness
from ....graphs.stream import Stream
from ....graphs.topic import Topic
from ....messages.message import Message
from ....messages.types import (
    BytesType,
    DynamicType,
    StrDynamicType,
    StrEnumType,
    StrType,
)
from ....util.random import random_string
from ...logger import LoggerConfig
from ..logger import HDF5Logger


NUM_MESSAGES = 100


class MyIntEnum(int, Enum):
    A = 1
    B = 2


class MyStrEnum(str, Enum):
    A = "A"
    B = "B"


class MyMessage(Message):
    int_field: int
    str_field: str
    float_field: float
    bool_field: bool
    bytes_field: bytes
    int_enum_field: MyIntEnum
    str_enum_field: MyStrEnum
    fixed_bytes_field: BytesType(length=10)  # type: ignore


def test_hdf5_logger() -> None:
    """
    Tests that we can write messages to an HDF5 file and then read them back.
    """

    logging_ids = ("test1", "test2")
    logging_ids_and_messages = []
    for i in range(NUM_MESSAGES):
        message = MyMessage(
            int_field=i,
            str_field=str(i),
            float_field=float(i),
            bool_field=i % 2 == 0,
            bytes_field=str(i).encode("ascii"),
            int_enum_field=list(MyIntEnum)[i % 2],
            str_enum_field=list(MyStrEnum)[i % 2],
            fixed_bytes_field=b"0123456789",
        )
        for logging_id in random.sample(logging_ids, k=len(logging_ids)):
            logging_ids_and_messages.append((logging_id, message))

    output_directory = tempfile.gettempdir()
    recording_name = random_string(16)
    config = LoggerConfig(
        output_directory=output_directory, recording_name=recording_name
    )
    run_with_harness(
        HDF5Logger,
        functools.partial(_test_fn, logging_ids_and_messages=logging_ids_and_messages),
        config=config,
    )

    # Read the messages back from the file and compare to the messages array
    output_path = Path(output_directory) / Path(f"{recording_name}.h5")
    with h5py.File(str(output_path), "r") as h5py_file:
        for logging_id in logging_ids:
            messages = [l[1] for l in logging_ids_and_messages if l[0] == logging_id]
            for i, message in enumerate(messages):
                for field in message.__class__.__message_fields__.values():
                    expected_value = getattr(message, field.name)
                    actual_value = h5py_file[logging_id][i][field.name]

                    if isinstance(field.data_type, StrType) or isinstance(
                        field.data_type, StrEnumType
                    ):
                        assert (
                            actual_value.decode(field.data_type.encoding)
                            == expected_value
                        )
                    elif isinstance(field.data_type, DynamicType) and not isinstance(
                        field.data_type, StrDynamicType
                    ):
                        assert bytes(actual_value) == expected_value
                    else:
                        assert actual_value == expected_value


async def _test_fn(
    logger: HDF5Logger, logging_ids_and_messages: List[Tuple[str, Message]]
) -> None:
    await asyncio.gather(
        logger.run_logger(), _write_messages(logger, logging_ids_and_messages)
    )


async def _write_messages(
    logger: HDF5Logger, logging_ids_and_messages: List[Tuple[str, Message]]
) -> None:
    for logging_id, message in logging_ids_and_messages:
        logger.buffer_message(logging_id, message)
        await asyncio.sleep(0.01)
    logger.running = False