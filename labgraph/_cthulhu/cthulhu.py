#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from enum import Enum, auto
from types import TracebackType
from typing import Callable, Generic, Optional, Type, TypeVar

from ..messages.message import Message
from ..util.error import LabgraphError
from ..util.typing import is_generic_subclass
from .bindings import (  # type: ignore
    PerformanceSummary,
    StreamConsumer,
    StreamDescription,
    StreamInterface,
    StreamProducer,
    StreamSample,
    streamRegistry,
    typeRegistry,
)


T = TypeVar("T")


class LabgraphCallbackParams(Generic[T]):
    def __init__(self, message: T, stream_id: Optional[str]) -> None:
        self.message = message
        self.stream_id = stream_id

    message: T
    stream_id: Optional[str]


LabgraphCallback = Callable[..., None]
CthulhuCallback = Callable[[StreamSample], None]


class Mode(Enum):
    SYNC = auto()
    ASYNC = auto()


class Consumer(StreamConsumer):  # type: ignore
    """
    Convenience wrapper of Cthulhu's `StreamConsumer` that allows us to specify a
    callback accepting Labgraph `Message`s.

    Args:
        stream_interface: The stream interface to use.
        sample_callback: The callback to use (uses Labgraph messages).
    """

    def __init__(
        self,
        stream_interface: StreamInterface,
        sample_callback: LabgraphCallback,
        mode: Mode = Mode.SYNC,
        stream_id: Optional[str] = None,
    ) -> None:
        super(Consumer, self).__init__(
            **{
                "si": stream_interface,
                "sampleCb": self._to_cthulhu_callback(sample_callback),
                "async": mode == Mode.ASYNC,
            }
        )
        self.stream_id = stream_id

    def _to_cthulhu_callback(self, callback: LabgraphCallback) -> CthulhuCallback:
        """
        Given a Labgraph callback, creates a Cthulhu callback (accepting
        `StreamSample`s).
        """

        def wrapped_callback(sample: StreamSample) -> None:
            assert hasattr(callback, "__annotations__")
            annotated_types = {
                arg: arg_type
                for arg, arg_type in callback.__annotations__.items()
                if not arg == "return"
            }

            message_types = [
                arg_type
                for arg_type in annotated_types.values()
                if is_generic_subclass(arg_type, LabgraphCallbackParams)
                or issubclass(arg_type, Message)
            ]
            assert len(message_types) == 1

            message_type = message_types[0]
            if is_generic_subclass(message_type, LabgraphCallbackParams):
                (arg_type,) = message_type.__args__
                message = arg_type(__sample__=sample)
                params = LabgraphCallbackParams(message, self.stream_id)
                callback(params)
            elif issubclass(message_type, Message):
                message = message_type(__sample__=sample)
                callback(message)
            else:
                raise TypeError(
                    f"Expected callback taking type '{Message.__name__}' or '{LabgraphCallbackParams.__name__}', got '{message_type.__name__}'"
                )

        return wrapped_callback

    def __enter__(self) -> "Consumer":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()


class Producer(StreamProducer):  # type: ignore
    """
    Convenience wrapper of Cthulhu's `StreamProducer` that accepts a Labgraph message.

    Args:
        stream_interface: The stream interface to use.
    """

    def __init__(
        self, stream_interface: StreamInterface, mode: Mode = Mode.SYNC
    ) -> None:
        super(Producer, self).__init__(
            **{"si": stream_interface, "async": mode == Mode.ASYNC}
        )
        self.stream_interface = stream_interface

    def produce_message(self, message: Message) -> None:
        """
        Produces a Labgraph message to the Cthulhu stream.

        Args:
            message: The message to produce.
        """
        self.produceSample(message.__sample__)

    def __enter__(self) -> "Producer":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()


def register_stream(name: str, message_type: Type[Message]) -> StreamInterface:
    """
    Registers a stream with a Labgraph message type to the Cthulhu stream registry.

    Args:
        name: The name of the stream.
        message_type: The type of the stream.
    """
    cthulhu_type = typeRegistry().findTypeName(message_type.versioned_name)
    assert cthulhu_type is not None
    existing_stream = streamRegistry().getStream(name)
    if existing_stream is not None:
        type_id = existing_stream.description.type
        existing_type = typeRegistry().findTypeID(type_id)
        if existing_type.typeName != message_type.versioned_name:
            raise LabgraphError(
                f"Tried to register stream '{name}' with type "
                f"'{message_type.versioned_name}', but it already exists with type "
                f"'{existing_type.typeName}'"
            )
        return existing_stream
    return streamRegistry().registerStream(StreamDescription(name, cthulhu_type.typeID))


def get_stream(name: str) -> Optional[StreamInterface]:
    """
    Returns the stream with the given name.

    Args:
        name: The name of the stream.
    """
    return streamRegistry().getStream(name)


def format_performance_summary(summary: PerformanceSummary) -> str:
    return (
        f"Callback runtime: {summary.min_runtime} min {summary.max_runtime} max "
        f"{summary.mean_runtime} mean\n"
        f"Total runtime: {summary.total_runtime}\n"
        f"{summary.num_calls} calls\n"
        f"{summary.num_samples_dropped} samples dropped"
    )
