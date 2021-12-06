#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

"""
Module containing utilities used in HDF5 unit tests.

This includes a Message that has all known field types.
- When a new field type is added it should be updated here to unit test correctly.
"""


import asyncio
import functools
import random
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Type

from ....graphs.node_test_harness import run_with_harness
from ....messages.message import Message
from ....messages.types import BytesType
from ....util.random import random_string
from ...logger import Logger, LoggerConfig

LOGGING_IDS = ("test1", "test2")
NUM_MESSAGES = 100


class MyIntEnum(int, Enum):
    A = 1
    B = 2


class MyStrEnum(str, Enum):
    A = "A"
    B = "B"


@dataclass
class MyDataclass:
    sub_int_field: int
    sub_str_field: str


class MyMessage(Message):
    int_field: int
    str_field: str
    float_field: float
    bool_field: bool
    bytes_field: bytes
    int_enum_field: MyIntEnum
    str_enum_field: MyStrEnum
    fixed_bytes_field: BytesType(length=10)  # type: ignore
    list_field: List[int]
    dict_field: Dict[str, str]
    dataclass_field: MyDataclass


async def _test_fn(
    logger: Logger, logging_ids_and_messages: List[Tuple[str, Message]]
) -> None:
    await asyncio.gather(
        logger.run_logger(), _write_messages(logger, logging_ids_and_messages)
    )


async def _write_messages(
    logger: Logger, logging_ids_and_messages: List[Tuple[str, Message]]
) -> None:
    for logging_id, message in logging_ids_and_messages:
        logger.buffer_message(logging_id, message)
        await asyncio.sleep(0.01)
    logger.running = False


def write_logs_to_hdf5(logger: Type[Logger]) -> Tuple[Path, List[Tuple[str, Message]]]:
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
            list_field=[5, 6, 7],
            dict_field={"test_key": "test_val"},
            dataclass_field=MyDataclass(sub_int_field=7, sub_str_field="seven"),
        )
        for logging_id in random.sample(LOGGING_IDS, k=len(LOGGING_IDS)):
            logging_ids_and_messages.append((logging_id, message))

    output_directory = tempfile.gettempdir()
    recording_name = random_string(16)
    config = LoggerConfig(
        output_directory=output_directory, recording_name=recording_name
    )
    run_with_harness(
        logger,
        functools.partial(_test_fn, logging_ids_and_messages=logging_ids_and_messages),
        config=config,
    )
    return (
        Path(output_directory) / Path(f"{recording_name}.h5"),
        logging_ids_and_messages,
    )
