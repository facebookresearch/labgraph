#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple, Union

import h5py
import numpy as np

from ...graphs.parent_graph_info import ParentGraphInfo
from ...graphs.stream import Stream
from ...graphs.topic import PATH_DELIMITER
from ...messages.message import Message
from ...messages.types import (
    T_I,
    BoolType,
    BytesType,
    CFloatType,
    CIntType,
    DynamicType,
    FieldType,
    FloatType,
    IntEnumType,
    IntType,
    NumpyDynamicType,
    NumpyType,
    StrDynamicType,
    StrEnumType,
    StrType,
    T,
)
from ...util.error import LabGraphError
from ..logger import Logger


HDF5_PATH_DELIMITER = "/"

logger = logging.getLogger(__name__)


class HDF5Logger(Logger):
    """
    Represents a logger that writes messages to an HDF5 file.
    """

    def setup(self) -> None:
        super().setup()
        output_path = Path(self.config.output_directory) / Path(
            f"{self.config.recording_name}.h5"
        )
        logger.info(f"logging to {output_path}")
        self.file = h5py.File(str(output_path), "w")
        self.file_lock = threading.Lock()  # Prevents file close while writing

    def write(self, messages_by_logging_id: Mapping[str, Sequence[Message]]) -> None:
        with self.file_lock:
            if self.file is None:
                num_messages = sum(
                    len(messages) for messages in messages_by_logging_id.values()
                )
                logger.warn(f"dropping {num_messages} messages while stopping")
                return
            for logging_id, messages in messages_by_logging_id.items():
                hdf5_path = logging_id
                group_path = "/" + HDF5_PATH_DELIMITER.join(
                    hdf5_path.split(PATH_DELIMITER)[:-1]
                )
                group = self.file.require_group(group_path)

                dataset_dtype = np.dtype(
                    [
                        (field.name, *get_numpy_type_for_field_type(field.data_type))
                        for field in messages[0].__class__.__message_fields__.values()
                    ]
                )

                dataset_name = hdf5_path.split(PATH_DELIMITER)[-1]
                if dataset_name not in group:
                    dataset = group.create_dataset(
                        dataset_name,
                        shape=(len(messages),),
                        maxshape=(None,),
                        dtype=dataset_dtype,
                    )
                else:
                    dataset = group[dataset_name]
                    dataset.resize(len(dataset) + len(messages), 0)

                for i, message in enumerate(messages):
                    # Convert dynamic-length bytes fields into numpy arrays so h5py can
                    # read/write them
                    message_fields = list(message.astuple())
                    for j, value in enumerate(message_fields):
                        if not isinstance(
                            list(message.__class__.__message_fields__.values())[
                                j
                            ].data_type,
                            DynamicType,
                        ):
                            continue
                        if isinstance(value, bytes):
                            message_fields[j] = np.array(bytearray(value))
                        elif isinstance(value, bytearray):
                            message_fields[j] = np.array(value)

                    dataset[-len(messages) + i] = tuple(message_fields)

            self.file.flush()

    def cleanup(self) -> None:
        super().cleanup()
        if self.file is not None:
            with self.file_lock:
                output_path = Path(self.config.output_directory) / Path(
                    f"{self.config.recording_name}.h5"
                )
                logger.info(f"closing hdf5 file ({output_path})")
                self.file.close()
                self.file = None


def get_numpy_type_for_field_type(
    field_type: FieldType[T],
) -> Union[Tuple[np.dtype], Tuple[np.dtype, Tuple[int, ...]]]:
    if (
        isinstance(field_type, StrType)
        or isinstance(field_type, BytesType)
        or isinstance(field_type, StrEnumType)
    ):
        encoding = (
            field_type.encoding if field_type in (StrType, StrEnumType) else "ascii"
        )
        return (h5py.string_dtype(encoding=encoding, length=field_type.length),)
    elif isinstance(field_type, IntType) or isinstance(field_type, IntEnumType):
        return (get_numpy_type_for_int_type(field_type),)
    elif isinstance(field_type, FloatType):
        return (get_numpy_type_for_float_type(field_type),)
    elif isinstance(field_type, BoolType):
        return (np.bool,)
    elif isinstance(field_type, NumpyType):
        return (field_type.dtype, field_type.shape)
    elif isinstance(field_type, DynamicType):
        return (get_dynamic_type(field_type),)

    raise LabGraphError(f"No equivalent numpy type for field type: {field_type}")


def get_numpy_type_for_int_type(int_type: Union[IntType, IntEnumType[T_I]]) -> np.dtype:
    return {
        CIntType.CHAR: np.int8,
        CIntType.UNSIGNED_CHAR: np.uint8,
        CIntType.SHORT: np.int16,
        CIntType.UNSIGNED_SHORT: np.uint16,
        CIntType.INT: np.int32,
        CIntType.UNSIGNED_INT: np.uint32,
        CIntType.LONG: np.int64,
        CIntType.UNSIGNED_LONG: np.uint64,
        CIntType.UNSIGNED_LONG_LONG: np.uint64,
        CIntType.LONG_LONG: np.int64,
    }[int_type.c_type]


def get_numpy_type_for_float_type(float_type: FloatType) -> np.dtype:
    return {CFloatType.FLOAT: np.float32, CFloatType.DOUBLE: np.float64}[
        float_type.c_type
    ]


def get_dynamic_type(field_type: FieldType[Any]) -> np.dtype:
    if isinstance(field_type, StrDynamicType):
        return h5py.string_dtype(encoding=field_type.encoding)
    elif isinstance(field_type, NumpyDynamicType):
        return h5py.vlen_dtype(field_type.dtype)
    else:
        return h5py.vlen_dtype(np.uint8)
