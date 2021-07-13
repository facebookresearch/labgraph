#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import pickle
import struct
from abc import ABC, abstractmethod, abstractproperty
from enum import Enum
from io import BytesIO
from typing import Any, Generic, Optional, Tuple, Type, TypeVar

import numpy as np
import typeguard


DEFAULT_STR_LENGTH = 128


class ByteOrder(str, Enum):
    """
    Represents a byte order used by a message in memory.
    """

    BIG_ENDIAN = ">"
    LITTLE_ENDIAN = "<"


DEFAULT_BYTE_ORDER = ByteOrder.LITTLE_ENDIAN


class CIntType(str, Enum):
    """
    Represents a C integer type. The string value of the C type in this enum is the
    format string for that enum in the `struct` module.
    """

    CHAR = "b"
    UNSIGNED_CHAR = "B"
    SHORT = "h"
    UNSIGNED_SHORT = "H"
    INT = "i"
    UNSIGNED_INT = "I"
    LONG = "l"
    UNSIGNED_LONG = "L"
    LONG_LONG = "q"
    UNSIGNED_LONG_LONG = "Q"


class CFloatType(Enum):
    """
    Represents a C floating-precision type. The string value of the C type in this enum
    is the format string for that enum in the `struct` module.
    """

    FLOAT = "f"
    DOUBLE = "d"


T = TypeVar("T")


class FieldType(ABC, Generic[T]):
    """
    Represents a LabGraph field type. Subclasses implement methods that describe how to
    check for instances of the type and serialize the type.
    """

    @abstractmethod
    def isinstance(self, obj: Any) -> bool:
        """
        Returns true if `obj` conforms to this field type.

        Args:
            obj: The object to check against this field type.
        """
        raise NotImplementedError()

    @abstractproperty
    def description(self) -> str:
        """
        A string description of this field type.
        """
        raise NotImplementedError()

    @abstractproperty
    def python_type(self) -> type:
        """
        The raw Python type that this field type corresponds to.
        """
        raise NotImplementedError()

    @property
    def size(self) -> Optional[int]:
        """
        The size in memory that this field type takes. If None, then this field has a
        dynamic length.
        """
        raise NotImplementedError()

    def preprocess(self, value: T) -> Any:
        """
        Preprocesses a value of this field type so it can be serialized. The default
        implementation does nothing to the value; subclasses can override this to
        provide preprocessing behavior.

        Args:
            value: The value to preprocess.
        """
        return value

    def postprocess(self, value: Any) -> T:
        """
        Postprocesses a deserialized object to conform to this field type. The default
        implementation does nothing to the value; subclasses can override this to
        provide postprocessing behavior.

        Args:
            value: The value to postprocess.
        """
        assert self.isinstance(value)
        return value  # type: ignore


class StructType(FieldType[T]):
    """
    Represents a type that has fixed length and can be serialized using the built-in
    `struct` library.
    """

    @abstractproperty
    def format_string(self) -> str:
        """
        The format string of this field type, for the `struct` module.
        """
        raise NotImplementedError()

    @property
    def size(self) -> int:
        return struct.calcsize(f"{DEFAULT_BYTE_ORDER.value}{self.format_string}")


class IntType(StructType[int]):
    """
    Represents an integer type.

    Args:
        c_type:
            The corresponding C type to serialize this integer as. Defaults to
            `long`.
    """

    c_type: CIntType

    def __init__(self, c_type: CIntType = CIntType.LONG) -> None:
        self.c_type = c_type

    @property
    def format_string(self) -> str:
        return str(self.c_type.value)

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, int)

    @property
    def description(self) -> str:
        return "int"

    @property
    def python_type(self) -> type:
        return int


T_I = TypeVar("T_I", bound=Enum)  # Enumerated integer type


class IntEnumType(StructType[T_I]):
    """
    Represents an integer type.

    Args:
        c_type:
            The corresponding C type to serialize this integer as. Defaults to
            `long`.
    """

    c_type: CIntType

    def __init__(self, enum_type: Type[T_I], c_type: CIntType = CIntType.LONG) -> None:
        self.c_type = c_type
        self.enum_type: Type[T_I] = enum_type

    @property
    def format_string(self) -> str:
        return str(self.c_type.value)

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, self.enum_type)

    @property
    def description(self) -> str:
        return self.enum_type.__name__

    def postprocess(self, value: int) -> T_I:
        return self.enum_type(value)

    @property
    def python_type(self) -> type:
        return self.enum_type


class BoolType(StructType[bool]):
    """
    Represents a boolean type.

    Args:
        c_type:
            The corresponding C type to serialize this integer as. Defaults to
            `long`.
    """

    @property
    def format_string(self) -> str:
        return "?"

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, bool)

    @property
    def description(self) -> str:
        return "bool"

    @property
    def python_type(self) -> type:
        return bool


class FloatType(StructType[float]):
    """
    Represents a floating-precision type.

    Args:
        c_type:
            The corresponding C type to serialize this float as. Defaults to
            `double`.
    """

    c_type: CFloatType

    def __init__(self, c_type: CFloatType = CFloatType.DOUBLE) -> None:
        self.c_type = c_type

    @property
    def format_string(self) -> str:
        return str(self.c_type.value)

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, float)

    @property
    def description(self) -> str:
        return "float"

    @property
    def python_type(self) -> type:
        return float


class StrType(StructType[str]):
    """
    Represents a string type.

    Args:
        length:
            The maximum length of a string that conforms to this type. Necessary to
            allow this field to be serialized with fixed length.
        encoding: The encoding to use to serialize strings for this field.
    """

    length: int
    encoding: str

    def __init__(
        self, length: int = DEFAULT_STR_LENGTH, encoding: str = "utf-8"
    ) -> None:
        self.length = length
        self.encoding = encoding

    @property
    def format_string(self) -> str:
        return f"{self.length}s"

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, str) and len(obj) <= self.length

    @property
    def description(self) -> str:
        return f"str({self.length})"

    def preprocess(self, value: str) -> bytes:
        return value.encode(self.encoding)

    def postprocess(self, value: bytes) -> str:
        return value.decode(self.encoding).rstrip("\0")

    @property
    def python_type(self) -> type:
        return str


T_S = TypeVar("T_S", bound=Enum)  # Enumerated string type


class StrEnumType(StructType[T_S]):
    """
    Represents an enumerated string type.

    Args:
        encoding: The encoding to use to serialize strings for this field.
    """

    length: int
    encoding: str

    def __init__(self, enum_type: Type[T_S], encoding: str = "utf-8") -> None:
        self.length = max(len(item.value) for item in enum_type)
        self.encoding = encoding
        self.enum_type = enum_type

    @property
    def format_string(self) -> str:
        return f"{self.length}s"

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, self.enum_type)

    @property
    def description(self) -> str:
        return self.enum_type.__name__

    def preprocess(self, value: T_S) -> bytes:
        str_value: str = value.value
        return str_value.encode(self.encoding)

    def postprocess(self, value: bytes) -> T_S:
        str_value = value.decode(self.encoding).rstrip("\0")
        return self.enum_type(str_value)

    @property
    def python_type(self) -> type:
        return self.enum_type


class BytesType(StructType[bytes]):
    """
    Represents a bytes type.

    Args:
        length:
            The maximum length of a byte string that conforms to this type. Necessary to
            allow this field to be serialized with fixed length.
    """

    length: int

    def __init__(self, length: int = DEFAULT_STR_LENGTH) -> None:
        self.length = length

    @property
    def format_string(self) -> str:
        return f"{self.length}s"

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, bytes) and len(obj) <= self.length

    @property
    def description(self) -> str:
        return f"bytes({self.length})"

    def postprocess(self, value: bytes) -> bytes:
        return value.rstrip(b"\0")

    @property
    def python_type(self) -> type:
        return bytes


class NumpyOrder(str, Enum):
    C = "C"
    F = "F"


class NumpyType(StructType[np.ndarray]):
    """
    Represents a numpy array type.

    Args:
        shape: The shape of a numpy array of this type.
        dtype: The dtype of a numpy array of this type.
        order: The order of the numpy array's data for multidimensional arrays ("C" or "F")
    """

    shape: Tuple[int]
    dtype: np.dtype
    order: NumpyOrder

    def __init__(
        self,
        shape: Tuple[int],
        dtype: np.dtype = np.float64,
        order: NumpyOrder = NumpyOrder.C,
    ) -> None:
        self.shape = shape
        self.dtype = dtype
        self.order = order

    @property
    def format_string(self) -> str:
        arr = np.zeros(shape=self.shape, dtype=self.dtype)
        bytes_length = arr.size * arr.itemsize
        return f"{bytes_length}s"

    def isinstance(self, obj: Any) -> bool:
        return (
            isinstance(obj, np.ndarray)
            and obj.shape == self.shape
            and obj.dtype == self.dtype
        )

    @property
    def description(self) -> str:
        return f"numpy.ndarray({self.shape}, {self.dtype})"

    def preprocess(self, arr: np.ndarray) -> bytes:
        return arr.tobytes(order=self.order)  # type: ignore

    def postprocess(self, arr_bytes: bytes) -> np.ndarray:
        return np.frombuffer(buffer=arr_bytes, dtype=self.dtype).reshape(self.shape)

    @property
    def python_type(self) -> type:
        return np.ndarray  # type: ignore


class DynamicType(FieldType[T]):
    """
    Represents a dynamic field type.
    """

    def isinstance(self, obj: Any) -> bool:
        try:
            typeguard.check_type("", obj, self.python_type)
            return True
        except TypeError:
            return False

    @abstractproperty
    def python_type(self) -> Type[T]:
        raise NotImplementedError()

    @property
    def size(self) -> Optional[int]:
        return None


class ObjectDynamicType(DynamicType[Any]):
    """
    Represents a dynamic field type for any object. This is a fallback type for when we
    don't know how else to serialize a field. This type simply uses pickling to
    serialize objects.
    """

    @property
    def python_type(self) -> Type[object]:
        return object

    @property
    def description(self) -> str:
        return "object"

    def preprocess(self, obj: T) -> bytes:
        return pickle.dumps(obj)

    def postprocess(self, obj_bytes: bytes) -> T:
        return pickle.loads(obj_bytes)  # type: ignore


class NumpyDynamicType(DynamicType[np.ndarray]):
    """
    Represents a numpy dynamic field type.

    Args:
        dtype: The dtype of a numpy array of this type.
    """

    dtype: np.dtype

    def __init__(self, dtype: np.dtype = np.float64) -> None:
        self.dtype = dtype

    @property
    def python_type(self) -> type:
        return np.ndarray  # type: ignore

    def isinstance(self, obj: Any) -> bool:
        return isinstance(obj, np.ndarray) and obj.dtype == self.dtype

    def preprocess(self, obj: np.ndarray) -> bytes:
        assert self.isinstance(obj)
        buf = BytesIO()
        np.save(buf, obj)
        buf.seek(0)
        return buf.read()

    def postprocess(self, obj_bytes: bytes) -> np.ndarray:
        buf = BytesIO(obj_bytes)
        arr = np.load(buf)
        assert isinstance(arr, np.ndarray)
        return arr.astype(self.dtype)

    @property
    def description(self) -> str:
        return f"numpy.ndarray({self.dtype})"


class StrDynamicType(DynamicType[str]):
    """
    Represents a string dynamic field type.
    """

    encoding: str

    def __init__(self, encoding: str = "utf-8") -> None:
        super().__init__()
        self.encoding = encoding

    @property
    def python_type(self) -> type:
        return str

    def preprocess(self, obj: str) -> bytes:
        return obj.encode(self.encoding)

    def postprocess(self, obj_bytes: bytes) -> str:
        return obj_bytes.decode(self.encoding)

    @property
    def description(self) -> str:
        return "str"


class BytesDynamicType(DynamicType[bytes]):
    """
    Represents a bytes dynamic field type.
    """

    @property
    def python_type(self) -> type:
        return bytes

    @property
    def description(self) -> str:
        return "bytes"


PRIMITIVE_TYPES = {
    int: IntType,
    float: FloatType,
    str: StrDynamicType,
    bool: BoolType,
    bytes: BytesDynamicType,
}


def get_field_type(python_type: Type[T]) -> FieldType[T]:
    """
    Returns a `FieldType` that contains all the information LabGraph needs for a field.

    Args:
        `python_type`: A Python type to get a `FieldType` for.
    """

    if not isinstance(python_type, type):
        return ObjectDynamicType()
    if issubclass(python_type, Enum):
        if issubclass(python_type, str):
            return StrEnumType(python_type)  # type: ignore
        elif issubclass(python_type, int):
            return IntEnumType(python_type)  # type: ignore
        else:
            raise TypeError(
                "Message field enums must be a subtype of either int or str."
            )
    elif python_type in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[python_type]()  # type: ignore
    elif python_type == np.ndarray:
        return NumpyDynamicType()

    return ObjectDynamicType()
