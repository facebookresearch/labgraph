#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# Defines simple messaging constructs for LabGraph

import dataclasses
import hashlib
import logging
import struct
from collections import OrderedDict
from typing import Any, Dict, Generic, Optional, Tuple, Type, TypeVar, Union

from .._cthulhu.bindings import (
    Field as CthulhuField,
    memoryPool,
    StreamSample,
    TypeDefinition,
    typeRegistry,
)
from ..util.error import LabGraphError
from .types import DEFAULT_BYTE_ORDER, FieldType, StructType, get_field_type


logger = logging.getLogger(__name__)

T = TypeVar("T")

# Internal fields that are present on Message instances but are not included when
# serializing the message for streaming
LOCAL_INTERNAL_FIELDS = (
    "__sample__",
    "__original_message__",
    "__original_message_type__",
)


class Field(Generic[T]):
    """
    Represents a field in a LabGraph message.

    Args:
        name: The name of the field.
        data_type: The data type of the field.
        offset: The offset of the field's data within a message in memory.
    """

    name: str
    data_type: FieldType[T]
    offset: int
    dataclasses_field: dataclasses.Field  # type: ignore

    def __init__(
        self,
        name: str,
        data_type: FieldType[T],
        offset: int,
        dataclasses_field: dataclasses.Field,  # type: ignore
    ) -> None:
        self.name = name
        self.data_type = data_type
        self.offset = offset
        self.dataclasses_field = dataclasses_field

    @property
    def required(self) -> bool:
        return (
            self.dataclasses_field.default == dataclasses.MISSING
            and self.dataclasses_field.default_factory  # type: ignore
            == dataclasses.MISSING
        )

    def get_default_value(self) -> T:
        assert not self.required
        if self.dataclasses_field.default != dataclasses.MISSING:
            value = self.dataclasses_field.default
        else:
            value = self.dataclasses_field.default_factory()  # type: ignore

        assert self.data_type.isinstance(value), (
            f"Expected default value for field '{self.name}' to match type "
            f"'{self.data_type.description}', got value {value}"
        )
        return value  # type: ignore


class MessageMeta(type):
    """
    Metaclass for messages. Responsible for collecting field information from the
    class's type annotations. Works similarly to the builtin `dataclasses` module but is
    not compatible with it. When any class is defined using this metaclass, we also
    register a corresponding Cthulhu type.
    """

    __message_size__: int
    __message_fields__: "OrderedDict[str, Field[Any]]"
    __format_string__: str
    __num_dynamic_fields__: int

    def __init__(
        cls, name: str, bases: Tuple[type, ...], members: Dict[str, Any]
    ) -> None:
        super(MessageMeta, cls).__init__(name, bases, members)

        # Make the class a dataclass
        dataclasses.dataclass(frozen=True, init=False, eq=False)(cls)  # type: ignore
        assert dataclasses.is_dataclass(cls)

        # Emulate the __post_init__ method from a normal dataclasses
        if not hasattr(cls, "__post_init__"):
            cls.__post_init__ = lambda self: None

        # Use big endian by default for all IPC communications
        cls.__format_string__ = DEFAULT_BYTE_ORDER.value
        cls.__message_fields__ = OrderedDict([])
        cls.__num_dynamic_fields__ = 0

        # Collect field information using the dataclass's fields
        if hasattr(cls, "__annotations__"):
            for field in dataclasses.fields(cls):
                if field.name in LOCAL_INTERNAL_FIELDS:
                    # Skip local internal fields (not serialized)
                    continue

                # Add a field, substituting a primitive Python type for a `FieldType`
                # when possible

                data_type = (
                    field.type
                    if isinstance(field.type, FieldType)
                    else get_field_type(field.type)
                )

                if data_type.size is None:
                    my_field = Field(
                        name=field.name,
                        data_type=data_type,
                        offset=cls.__num_dynamic_fields__,
                        dataclasses_field=field,
                    )
                    cls.__num_dynamic_fields__ += 1
                elif isinstance(data_type, StructType):
                    my_field = Field(
                        name=field.name,
                        data_type=data_type,
                        offset=struct.calcsize(cls.__format_string__),
                        dataclasses_field=field,
                    )
                    cls.__format_string__ += data_type.format_string
                else:
                    raise NotImplementedError(
                        f"Unexpected field type {data_type.__class__}"
                    )

                cls.__message_fields__[my_field.name] = my_field

        cls.__message_size__ = struct.calcsize(cls.__format_string__)

        logger.debug(
            f"{cls.__name__}:registering cthulhu type with length "
            f"{cls.__message_size__}"
        )

        # Register this message type with Cthulhu
        type_definition = TypeDefinition()
        type_definition.typeName = cls.versioned_name
        type_definition.sampleParameterSize = cls.__message_size__
        type_definition.sampleNumberDynamicFields = cls.__num_dynamic_fields__
        type_definition.hasContentBlock = True
        type_definition.sampleFields = {
            field.name: CthulhuField(
                field.offset,
                field.data_type.size or 1,  # 1 if pointer to dynamic field
                "uint8_t",
                field.data_type.size or 1,  # 1 if pointer to dynamic field
                field.data_type.size is None,
            )
            for field in cls.__message_fields__.values()
        }
        typeRegistry().registerType(type_definition)

        type_id = typeRegistry().findTypeName(cls.versioned_name).typeID
        logger.debug(f"{cls.__name__}:registered cthulhu type with ID {type_id}")

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        instance = type.__call__(cls, *args, **kwds)
        instance.__post_init__()
        return instance

    @property
    def full_name(cls) -> str:
        """
        Returns the fully qualified name of the message type (i.e., including
        its module name).
        """
        return f"{cls.__module__}.{cls.__name__}"

    def __eq__(cls, other: Any) -> bool:
        """
        Returns true if this message type is equivalent to the other message type.
        Message types are equivalent if they have the same number of fields, and the
        length of each field is the same.
        """
        if not isinstance(other, MessageMeta):
            return False
        if len(cls.__message_fields__) != len(other.__message_fields__):
            return False
        for arg1, arg2 in zip(
            cls.__message_fields__.values(), other.__message_fields__.values()
        ):
            if arg1.data_type.python_type != arg2.data_type.python_type:
                return False
            if (
                arg1.data_type.size is not None
                and arg2.data_type.size is not None
                and arg1.data_type.size != arg2.data_type.size
            ):
                return False
        return True

    def __hash__(cls) -> int:
        """
        Returns the hash of the message type.
        """
        return hash(tuple(cls.__message_fields__.values()))

    @property
    def versioned_name(cls) -> str:
        """
        Returns a name for the message type that is versioned. When the memory layout
        of the message type (i.e., its format string) changes, the versioned name
        changes as well.
        """
        # TODO: Remove dependency on `versioned_name` for message equivalency (see
        # T64643702, https://fb.quip.com/1dcNAmzas8No)
        hash_input = f"{cls.__format_string__},{cls.__num_dynamic_fields__}"
        fields_hash = hashlib.sha256(hash_input.encode("ascii")).hexdigest()
        return f"{cls.full_name}:{fields_hash}"

    def _index_of_field(cls, field_name: str) -> int:
        """
        Returns the index of the field named `field_name`.

        Args:
            field_name: The name of the field.
        """
        for i, (_, field) in enumerate(cls.__message_fields__.items()):
            if field.name == field_name:
                return i
        raise LabGraphError(f"{cls.__name__} has no field '{field_name}'")


class IsOriginalMessage:
    pass


M = TypeVar("M", bound="Message", covariant=True)


class Message(metaclass=MessageMeta):
    """
    Represents a LabGraph message. A message is a collection of data that can be sent
    between nodes via topics. The fields available to every message of a certain type
    are defined via type annotations on the corresponding subclass of `Message`.
    Subclasses recursively include their superclasses' fields.

    Messages can be thought of as similar to (but not compatible with) instances of
    dataclasses in the builtin `dataclasses` module.

    Messages' data are stored in shared memory via Cthulhu, meaning the transmission of
    messages between nodes requires no copying of data.
    """

    # If __original_message_type__ is set, then we cache an instance of that class for
    # faster message reading
    __original_message__: Optional[Union["Message", IsOriginalMessage]]

    # Cthulhu sample that backs this message - the Cthulhu sample manages this message's
    # shared memory
    __sample__: StreamSample

    __original_message_type__: Optional[Type["Message"]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__setattr__("__original_message__", None)
        super().__setattr__("__original_message_type__", None)
        if 1 <= len(kwargs) <= 2 and "__sample__" in kwargs.keys():
            # Option to create a message directly from Cthulhu sample
            # Bypasses frozen check due to `frozen=True` by calling `__setattr__` on
            # `object`
            if "__original_message_type__" in kwargs.keys():
                super().__setattr__(
                    "__original_message_type__", kwargs["__original_message_type__"]
                )
            super().__setattr__("__sample__", kwargs["__sample__"])
            return

        # Otherwise, build up a Cthulhu sample using the provided arguments

        cls = type(self)

        # Build a dictionary of values
        values: Dict[str, Any] = {}

        # Add to the dictionary from the positional arguments
        for i, arg in enumerate(args):
            # Check that there are as many kwargs as non-internal fields on this message
            # type
            if len(values) == len(cls.__message_fields__):
                raise TypeError(
                    f"__init__() takes {len(cls.__message_fields__)} positional "
                    f"arguments but {len(args)} were given"
                )
            values[list(cls.__message_fields__.keys())[i]] = arg

        # Add to the dictionary from the keyword arguments
        for key, value in kwargs.items():
            if key in values:
                raise TypeError(
                    f"__init__() for {cls.__name__} got multiple values for argument "
                    f"'{key}'"
                )
            elif key not in cls.__message_fields__:
                raise TypeError(
                    f"__init__() for {cls.__name__} got an unexpected keyword argument "
                    f"'{key}'"
                )

            values[key] = value

        # Ensure we have all required values, and fill in default values
        for field in cls.__message_fields__.values():
            if field.name not in values.keys():
                if field.required:
                    raise TypeError(f"__init__() missing argument: '{field.name}'")
                else:
                    values[field.name] = field.get_default_value()

        # Validate all the values
        for field in cls.__message_fields__.values():
            value = values[field.name]
            if not field.data_type.isinstance(value):
                raise TypeError(
                    f"__init__() for {cls.__name__} got invalid value for argument "
                    f"'{field.name}': {value} (expected a "
                    f"{field.data_type.description})"
                )

        # Allocate shared memory for a Cthulhu sample
        sample = StreamSample()

        if cls.__message_size__ > 0:
            sample.parameters = memoryPool().getBufferFromPool("", cls.__message_size__)

            # Preprocess the fixed-length field values and put them in the correct sequence
            # for serialization
            fixed_values = [
                field.data_type.preprocess(values[field.name])
                for field in cls.__message_fields__.values()
                if field.data_type.size is not None
            ]

            # Serialize the fixed-length field values
            fixed_bytes = struct.pack(cls.__format_string__, *fixed_values)

            # Write the serialized fixed-length field values to shared memory
            memoryview(sample.parameters)[
                : cls.__message_size__
            ] = fixed_bytes  # type: ignore

        if cls.__num_dynamic_fields__ > 0:
            # Preprocess the dynamic-length field values
            dynamic_values = [
                field.data_type.preprocess(values[field.name])
                for field in cls.__message_fields__.values()
                if field.data_type.size is None
            ]

            # Allocate shared memory for the dynamic-length field values
            dynamic_buffers = [
                memoryPool().getBufferFromPool("", len(value))
                for value in dynamic_values
            ]

            # Write the serialized dynamic-length field values to shared memory
            for value, buffer in zip(dynamic_values, dynamic_buffers):
                memoryview(buffer)[: len(value)] = value

            # Set the sample's dynamic parameters
            if len(dynamic_buffers) > 0:
                sample.dynamicParameters = dynamic_buffers

        # Bypasses frozen check due to `frozen=True` by calling `__setattr__` on
        # `object`
        super().__setattr__("__sample__", sample)

    def asdict(self) -> "OrderedDict[str, Any]":
        """
        Serialize the message as a dictionary.
        """
        return OrderedDict(
            (field.name, getattr(self, field.name))
            for field in self.__message_fields__.values()
        )

    def astuple(self) -> Tuple[Any, ...]:
        """
        Serialize the message as a tuple.
        """
        return tuple(
            getattr(self, field.name) for field in self.__message_fields__.values()
        )

    @classmethod
    def fromdict(cls: Type[M], data: Dict[str, Any]) -> M:
        """
        Deserialize a message from a dictionary.

        Args:
            data: The dictionary to deserialize.
        """
        return cls(**data)

    def replace(self: M, **kwargs: Dict[str, Any]) -> M:
        """
        Returns a new message with the fields replaced by the provided keyword
        arguments.
        """
        values = self.asdict()
        values.update(kwargs)
        return self.__class__(**values)

    def __getstate__(self) -> Dict[str, Any]:
        return self.asdict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__class__.__init__(self, **state)

    def __getattribute__(self, name: str) -> Any:
        all_fields = super().__getattribute__("__class__").__message_fields__
        if name not in all_fields:
            return super().__getattribute__(name)
        cls = type(self)
        field = all_fields[name]

        # Use __original_message__ if necessary
        if not isinstance(self.__original_message__, IsOriginalMessage):
            message_cls = self.__original_message_type__
            if message_cls is None or message_cls is cls:
                super().__setattr__("__original_message__", IsOriginalMessage())
            else:
                if self.__original_message__ is None:
                    super().__setattr__(
                        "__original_message__", message_cls(__sample__=self.__sample__)
                    )
                original_field_name = list(message_cls.__message_fields__.items())[
                    cls._index_of_field(name)
                ][0]
                result = getattr(self.__original_message__, original_field_name)
                if not field.data_type.isinstance(result):
                    raise LabGraphError(
                        f"Could not convert from {message_cls.__name__}."
                        f"{original_field_name} to {cls.__name__}.{name}: invalid "
                        f"value {result}"
                    )
                return result

        if field.data_type.size is None:
            # Dynamic field
            field_buffer = bytearray(self.__sample__.dynamicParameters[field.offset])
            return field.data_type.postprocess(field_buffer)
        elif isinstance(field.data_type, StructType):
            field_memoryview = memoryview(self.__sample__.parameters)[
                field.offset : field.offset + field.data_type.size
            ]
            return field.data_type.postprocess(
                struct.unpack(
                    DEFAULT_BYTE_ORDER.value + field.data_type.format_string,
                    field_memoryview,
                )[0]
            )
        else:
            raise NotImplementedError(
                f"Unexpected field type {field.data_type.__class__}"
            )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Message):
            raise NotImplementedError()
        if type(self) != type(other):
            return False
        return self.asdict() == other.asdict()


class TimestampedMessage(Message):
    """
    Represents a simple timestamped LabGraph message.  All messages which
    may be aligned using a timestamp should inherit from this class.
    """

    # Convention: units of seconds.
    timestamp: float
