#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# Unit tests for the Message class.

from enum import Enum
from typing import Any, Dict, List

import numpy as np
import pytest

from ..message import Message
from ..types import NumpyDynamicType, NumpyType


NUMPY_SHAPE = (10, 10)


class MyStrEnum(str, Enum):
    A = "A"
    B = "B"


class MyIntEnum(int, Enum):
    A = 1
    B = 2


class MyMessage(Message):
    """
    Simple message type with primitive fields for testing.
    """

    int_field: int
    str_field: str
    float_field: float
    bool_field: bool
    bytes_field: bytes


class MyDefaultMessage(Message):
    """
    Simple message type with some default fields.
    """

    field1: int
    field2: str
    field3: bool = True
    field4: bool = False
    field5: int = 10


class MyEnumMessage(Message):
    """
    Simple message type with different enumerated fields for testing.
    """

    str_enum_field: MyStrEnum
    int_enum_field: MyIntEnum


class MyNestedMessage(MyMessage):
    """
    Simple nested message type with primitive fields for testing.
    """

    b_extra_field: str
    a_extra_field: int


class MyNumpyMessage(Message):
    """
    Simple message type with a numpy field for testing numpy serialization.
    """

    field1: str
    field2: NumpyType(shape=NUMPY_SHAPE, dtype=np.float64)  # type: ignore
    field3: int


class MyNumpyMessage2(Message):
    """
    Simple message type with some fields for testing message type equality to
    `MyNumpyMessage`.
    """

    field1: str
    field2: NumpyType(shape=NUMPY_SHAPE, dtype=np.float64)  # type: ignore
    field3: int


class MyNumpyMessage3(Message):
    """
    Simple message type with some fields for testing message type equality to
    `MyNumpyMessage`.
    """

    field1: int
    field2: NumpyType(shape=NUMPY_SHAPE, dtype=np.float64)  # type: ignore
    field3: str


class MyNumpyMessage4(Message):
    """
    Simple message type with some fields for testing message type equality to
    `MyNumpyMessage`.
    """

    field1: str
    field2: NumpyType(shape=(5,), dtype=np.float64)  # type: ignore
    field3: int


class MyDynamicNumpyMessage(Message):
    """
    Simple message type with a dynamic numpy field for testing serialization and type
    comparisons.
    """

    field1: str
    field2: np.ndarray
    field3: int


class MyDynamicNumpyIntMessage(Message):
    """
    Simple message type with a dynamic numpy field for testing serialization and type
    comparisons.
    """

    field1: str
    field2: NumpyDynamicType(dtype=np.int64)  # type: ignore
    field3: int


class MyDynamicMessage(Message):
    """
    Simple message type with some arbitrary dynamic fields.
    """

    field1: Dict[str, Any]
    field2: int
    field3: List[Any]


class MyInvalidDefaultMessage(Message):
    """
    Message type with an invalid default value for testing this error case.
    """

    field1: str = 5  # type: ignore


def test_enum_message_creation() -> None:
    """
    Tests that we can create instances of MyEnumMessage.
    """
    message = MyEnumMessage(str_enum_field=MyStrEnum.A, int_enum_field=MyIntEnum.B)

    assert message.str_enum_field == MyStrEnum.A
    assert message.int_enum_field == MyIntEnum.B


def test_message_creation() -> None:
    """
    Tests that we can create instances of MyMessage.
    """
    message = MyMessage(
        int_field=5,
        str_field="hello",
        float_field=5.0,
        bool_field=True,
        bytes_field=b"world",
    )

    assert message.int_field == 5
    assert message.str_field == "hello"
    assert message.float_field == 5.0
    assert message.bool_field is True
    assert message.bytes_field == b"world"


def test_default_message_creation() -> None:
    """
    Tests that we can create instances of `MyDefaultMessage` which has default fields.
    """
    message1 = MyDefaultMessage(field1=5, field2="hello")
    message2 = MyDefaultMessage(field1=10, field2="world", field3=False, field5=40)
    assert message1.asdict() == {
        "field1": 5,
        "field2": "hello",
        "field3": True,
        "field4": False,
        "field5": 10,
    }
    assert message2.asdict() == {
        "field1": 10,
        "field2": "world",
        "field3": False,
        "field4": False,
        "field5": 40,
    }


def test_nested_message_creation() -> None:
    """
    Tests that we can create instances of MyNestedMessage.
    """
    message = MyNestedMessage(
        int_field=6,
        str_field="goodbye",
        float_field=10.0,
        bool_field=False,
        bytes_field=b"world",
        a_extra_field=5,
        b_extra_field="test",
    )

    assert message.int_field == 6
    assert message.str_field == "goodbye"
    assert message.float_field == 10.0
    assert message.bool_field is False
    assert message.bytes_field == b"world"
    assert message.a_extra_field == 5
    assert message.b_extra_field == "test"


def test_asdict() -> None:
    """
    Tests that we can serialize a message as a dictionary.
    """
    message = MyNestedMessage(
        int_field=6,
        str_field="goodbye",
        float_field=10.0,
        bool_field=False,
        bytes_field=b"world",
        a_extra_field=5,
        b_extra_field="test",
    )

    assert message.asdict() == {
        "int_field": 6,
        "str_field": "goodbye",
        "float_field": 10.0,
        "bool_field": False,
        "bytes_field": b"world",
        "a_extra_field": 5,
        "b_extra_field": "test",
    }


def test_equality() -> None:
    """
    Tests that we can check the equality of different message instances.
    """
    message1 = MyMessage(
        int_field=5,
        str_field="hello",
        float_field=5.0,
        bool_field=True,
        bytes_field=b"world",
    )
    message2 = MyMessage(
        int_field=5,
        str_field="hello",
        float_field=5.0,
        bool_field=True,
        bytes_field=b"world",
    )
    message3 = MyMessage(
        int_field=6,
        str_field="hello",
        float_field=5.0,
        bool_field=True,
        bytes_field=b"world",
    )
    assert message1 == message2
    assert message1 != message3


def test_fromdict() -> None:
    """
    Tests that we can deserialize a message from a dictionary.
    """
    message = MyNestedMessage.fromdict(
        {
            "int_field": 6,
            "str_field": "goodbye",
            "float_field": 10.0,
            "bool_field": False,
            "bytes_field": b"world",
            "a_extra_field": 5,
            "b_extra_field": "test",
        }
    )

    assert message == MyNestedMessage(
        int_field=6,
        str_field="goodbye",
        float_field=10.0,
        bool_field=False,
        bytes_field=b"world",
        a_extra_field=5,
        b_extra_field="test",
    )


def test_numpy() -> None:
    """
    Tests that we can serialize and deserialize messages with numpy fields.
    """

    arr = np.random.rand(*NUMPY_SHAPE)
    message = MyNumpyMessage(field1="hello", field2=arr, field3=3)
    assert message.field1 == "hello"
    assert (message.field2 == arr).all()
    assert message.field3 == 3


def test_invalid_field_error() -> None:
    """
    Tests that setting an invalid field value on a message raises a `TypeError`.
    """
    with pytest.raises(TypeError) as err:
        MyMessage(
            int_field="bad field",  # bad field
            str_field="hello",
            float_field=5.0,
            bool_field=True,
            bytes_field=b"world",
        )
    assert str(err.value) == (
        "__init__() for MyMessage got invalid value for argument 'int_field': bad "
        "field (expected a int)"
    )


def test_invalid_field_error_positional() -> None:
    """
    Tests that setting an invalid field value (as a positional argument) on a message
    raises a `TypeError`.
    """
    with pytest.raises(TypeError) as err:
        MyMessage("bad field", "hello", 5.0, True, b"world")
    assert str(err.value) == (
        "__init__() for MyMessage got invalid value for argument 'int_field': bad "
        "field (expected a int)"
    )


def test_message_type_equality() -> None:
    """
    Tests message type equality. Only `MyNumpyMessage` and `MyNumpyMessage2` are
    equivalent; all other comparison should return false.
    """
    assert MyNumpyMessage == MyNumpyMessage2
    assert MyNumpyMessage != MyNumpyMessage3
    assert MyNumpyMessage != MyNumpyMessage4
    assert MyNumpyMessage2 != MyNumpyMessage3
    assert MyNumpyMessage2 != MyNumpyMessage4
    assert MyNumpyMessage3 != MyNumpyMessage4


def test_dynamic_numpy_field() -> None:
    """
    Tests that we can define and construct a message type with a dynamic numpy field.
    """

    assert isinstance(
        MyDynamicNumpyMessage.__message_fields__["field2"].data_type, NumpyDynamicType
    )
    array = np.random.rand(3, 3)
    message = MyDynamicNumpyMessage(field1="hello", field2=array, field3=5)
    assert message.field1 == "hello"
    assert (message.field2 == array).all()
    assert message.field3 == 5


def test_dynamic_numpy_field_with_type() -> None:
    """
    Tests that we can define and construct a message type with a dynamic numpy field
    with a dtype.
    """

    assert isinstance(
        MyDynamicNumpyIntMessage.__message_fields__["field2"].data_type,
        NumpyDynamicType,
    )
    array = np.random.randint(5, size=(3, 3), dtype=np.int64)
    message = MyDynamicNumpyIntMessage(field1="hello", field2=array, field3=5)
    assert message.field1 == "hello"
    assert (message.field2 == array).all()
    assert message.field3 == 5


def test_dynamic_numpy_field_with_invalid_type() -> None:
    """
    Tests that we throw an error when we construct a message type with an incorrect
    dtype for the dynamic numpy field.
    """

    with pytest.raises(TypeError):
        MyDynamicNumpyIntMessage(field1="hello", field2=np.random.rand(3, 3), field3=5)


def test_static_to_dynamic_conversion() -> None:
    """
    Tests that we can convert a static field to a dynamic field between equivalent
    message types.
    """
    array = np.random.rand(*NUMPY_SHAPE)
    message1 = MyNumpyMessage(field1="hello", field2=array, field3=5)
    message2 = MyDynamicNumpyMessage(
        __sample__=message1.__sample__, __original_message_type__=MyNumpyMessage
    )
    assert message2.field1 == "hello"
    assert (message2.field2 == array).all()
    assert message2.field3 == 5


def test_dynamic_to_static_conversion() -> None:
    """
    Tests that we can convert a dynamic field to a static field between equivalent
    message types.
    """
    array = np.random.rand(*NUMPY_SHAPE)
    message1 = MyDynamicNumpyMessage(field1="hello", field2=array, field3=5)
    message2 = MyNumpyMessage(
        __sample__=message1.__sample__, __original_message_type__=MyDynamicNumpyMessage
    )
    assert message2.field1 == "hello"
    assert (message2.field2 == array).all()
    assert message2.field3 == 5


def test_dynamic_fields() -> None:
    """
    Tests that we can serialize some more dynamic field types.
    """
    field1 = {"key1": 5, "key2": "value2"}
    field2 = 12
    field3 = [5, "hello", 6.2]
    message = MyDynamicMessage(field1=field1, field2=field2, field3=field3)
    assert message.field1 == field1
    assert message.field2 == field2
    assert message.field3 == field3


def test_invalid_default_field() -> None:
    """
    Tests that a badly-typed default field value raises an error.
    """
    with pytest.raises(AssertionError) as err:
        MyInvalidDefaultMessage()
    assert (
        str(err.value)
        == "Expected default value for field 'field1' to match type 'str', got value 5"
    )


class TestPostInit:
    """
    Tests that
    1. a message that has a __post_init__ method is triggered upon message
       object creation.
    2. `super().__post_init__()` works when the parent message class has not
       defined the method (class Pos).
    3. the inherited stack of __post_init__ calls all fire.
    """

    positive_error_string = "Pos.positive_int must be positive"
    negative_error_string = "PosNeg.negative_int must be negative"

    class Pos(Message):
        positive_int: int

        def __post_init__(self) -> None:
            super().__post_init__()  # type: ignore

            if self.positive_int <= 0:
                raise ValueError(TestPostInit.positive_error_string)

    class PosNeg(Pos):
        negative_int: int

        def __post_init__(self) -> None:
            super().__post_init__()

            if self.negative_int >= 0:
                raise ValueError(TestPostInit.negative_error_string)

    def test_post_init_runs(self) -> None:
        """Tests objectives 1 and 2 above."""

        # We can make an object correctly.
        self.Pos(1)

        # Pos's constraint violated
        with pytest.raises(ValueError, match=TestPostInit.positive_error_string):
            self.Pos(0)

        with pytest.raises(ValueError, match=TestPostInit.positive_error_string):
            self.Pos(-1)

    def test_post_init_runs_all_inherited(self) -> None:
        """Tests objective 3 above."""

        # We can make a valid object.
        self.PosNeg(1, -1)

        # Pos's constraint violated
        with pytest.raises(ValueError, match=TestPostInit.positive_error_string):
            self.PosNeg(0, -1)

        with pytest.raises(ValueError, match=TestPostInit.positive_error_string):
            self.PosNeg(-1, -1)

        # PosNeg's constraint violated
        with pytest.raises(ValueError, match=TestPostInit.negative_error_string):
            self.PosNeg(1, 0)

        with pytest.raises(ValueError, match=TestPostInit.negative_error_string):
            self.PosNeg(1, 1)

        # Pos's and PosNeg's constraint violated
        with pytest.raises(ValueError, match=TestPostInit.positive_error_string):
            self.PosNeg(-1, 1)
