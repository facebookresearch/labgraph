#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging
import sys
from typing import Any, BinaryIO, Dict, List, Optional, Type, Union

import h5py

from ...messages.message import Message
from ...messages.types import (
    BoolType,
    BytesDynamicType,
    BytesType,
    FieldType,
    FloatType,
    IntEnumType,
    IntType,
    NumpyDynamicType,
    NumpyType,
    StrDynamicType,
    StrType,
    T,
)
from .logger import SERIALIZABLE_DYNAMIC_TYPES

FILELIKE_T = Union[str, BinaryIO]
LOGGER = logging.getLogger(__name__)
if sys.version_info > (3, 8):
    STR_TYPES = (StrType, StrDynamicType)
else:
    STR_TYPES = (StrType,)


class HDF5Reader:
    def __init__(self, path: FILELIKE_T, log_types: Dict[str, Type[Message]]) -> None:
        self.path = path
        self.log_types = log_types
        self._logs: Optional[Dict[str, List[Message]]] = None

    @property
    def logs(self) -> Optional[Dict[str, List[Message]]]:
        if self._logs is None:
            self._parse()
        return self._logs

    def _parse(self) -> None:
        self._logs = {}
        with h5py.File(self.path, "r") as f:
            for key, type_ in self.log_types.items():
                if key not in f:
                    LOGGER.warning(f"{key} not found in h5 file, skipping.")
                    continue
                messages = []
                for raw in f[key]:
                    kwargs = {}
                    raw_values = tuple(raw)
                    for index, field in enumerate(type_.__message_fields__.values()):
                        if isinstance(field.data_type, SERIALIZABLE_DYNAMIC_TYPES):
                            value = field.data_type.postprocess(
                                bytes(raw_values[index])
                            )
                        else:
                            value = get_deserialized_value(
                                raw_values[index], field.data_type
                            )
                        kwargs[field.name] = value
                    messages.append(type_(**kwargs))
                self._logs[key] = messages


def get_deserialized_value(value: Any, field_type: FieldType[T]) -> Any:
    if isinstance(field_type, BoolType):
        return bool(value)
    elif isinstance(field_type, (BytesDynamicType, BytesType)):
        return bytes(value)
    elif isinstance(field_type, FloatType):
        return float(value)
    elif isinstance(field_type, IntEnumType):
        return field_type.enum_type(int(value))
    elif isinstance(field_type, IntType):
        return int(value)
    elif isinstance(field_type, NumpyDynamicType):
        return field_type.postprocess(bytes(value))
    elif isinstance(field_type, NumpyType):
        return value
    elif isinstance(field_type, STR_TYPES):
        return bytes(value).decode(field_type.encoding)  # type: ignore
    else:
        return value
