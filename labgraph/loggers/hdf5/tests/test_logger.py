#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import sys

import h5py

from ....messages.types import (
    DynamicType,
    StrDynamicType,
    StrType,
)
from ..logger import HDF5Logger, SERIALIZABLE_DYNAMIC_TYPES
from .test_utils import LOGGING_IDS, write_logs_to_hdf5


def test_hdf5_logger() -> None:
    """
    Tests that we can write messages to an HDF5 file and then read them back.
    """

    if sys.version_info > (3, 8):
        str_types = (StrType, StrDynamicType)
    else:
        str_types = (StrType,)

    # Write the messages to a file
    output_path, logging_ids_and_messages = write_logs_to_hdf5(HDF5Logger)
    # Read the messages back from the file and compare to the messages array
    with h5py.File(str(output_path), "r") as h5py_file:
        for logging_id in LOGGING_IDS:
            messages = [l[1] for l in logging_ids_and_messages if l[0] == logging_id]
            for i, message in enumerate(messages):
                for field in message.__class__.__message_fields__.values():
                    expected_value = getattr(message, field.name)
                    actual_value = h5py_file[logging_id][i][field.name]

                    if isinstance(field.data_type, str_types):
                        assert (
                            actual_value.decode(field.data_type.encoding)
                            == expected_value
                        )
                    elif isinstance(field.data_type, SERIALIZABLE_DYNAMIC_TYPES):
                        actual_value = field.data_type.postprocess(bytes(actual_value))
                        assert actual_value == expected_value
                    elif isinstance(field.data_type, DynamicType) and not isinstance(
                        field.data_type, StrDynamicType
                    ):
                        assert bytes(actual_value) == expected_value
                    else:
                        assert actual_value == expected_value
