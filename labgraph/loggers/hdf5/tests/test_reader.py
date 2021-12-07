#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ..logger import HDF5Logger
from ..reader import HDF5Reader
from .test_utils import (
    MyDataclass,
    MyIntEnum,
    MyMessage,
    MyStrEnum,
    NUM_MESSAGES,
    write_logs_to_hdf5,
)


def test_hdf5_reader() -> None:
    path, _ = write_logs_to_hdf5(HDF5Logger)
    log_types = {
        "test1": MyMessage,
        "test2": MyMessage,
    }
    reader = HDF5Reader(path, log_types)
    for index in range(NUM_MESSAGES):
        expected = MyMessage(
            int_field=index,
            str_field=str(index),
            float_field=float(index),
            bool_field=index % 2 == 0,
            bytes_field=str(index).encode("ascii"),
            int_enum_field=list(MyIntEnum)[index % 2],
            str_enum_field=list(MyStrEnum)[index % 2],
            fixed_bytes_field=b"0123456789",
            list_field=[5, 6, 7],
            dict_field={"test_key": "test_val"},
            dataclass_field=MyDataclass(sub_int_field=7, sub_str_field="seven"),
        )
        assert reader.logs["test1"][index] == expected
        assert reader.logs["test2"][index] == expected
