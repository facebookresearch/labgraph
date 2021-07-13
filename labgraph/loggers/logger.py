#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import ctypes
import functools
import multiprocessing as mp
import tempfile
import threading
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Type

from .._cthulhu.cthulhu import Consumer, Mode, get_stream
from ..graphs.config import Config
from ..graphs.method import background
from ..graphs.node import Node
from ..graphs.stream import Stream
from ..messages.message import Message
from ..util.logger import get_logger
from ..util.random import random_string


logger = get_logger(__name__)


class LoggerConfig(Config):
    """
    Describes configuration for a logger.

    Args:
        output_directory: The directory in which to log streams to disk.
        recording_name:
            The name of the recording. Logger implementations will use this argument to
            build the filename(s) for the logs.
        buffer_size:
            The size of the buffer the logger will keep in memory before flushing to
            disk.
        flush_period:
            The time (in seconds) after which the logger will periodically flush to
            disk. Defaults to 1 second. If `None`, the logger will only flush when the
            buffer is full.
        streams_by_logging_id:
            A dictionary of the LabGraph stream objects by logging id. When specified,
            the logger will subscribe to the Cthulhu streams itself. This should always
            be provided unless the logger is being unit tested.
    """

    output_directory: str = field(default_factory=tempfile.gettempdir)
    recording_name: str = field(default_factory=functools.partial(random_string, 16))
    buffer_size: int = 100
    flush_period: Optional[float] = 1
    streams_by_logging_id: Dict[str, Stream] = field(default_factory=dict)


class Logger(Node):
    config: LoggerConfig

    def setup(self) -> None:
        self.buffer: List[Tuple[str, Message]] = []
        self.running: bool = False

        self.consumers: Dict[str, Consumer] = {}
        for logging_id, stream in self.config.streams_by_logging_id.items():
            callback = self._get_logger_callback(logging_id, stream)

            stream_interface = get_stream(stream.id)
            assert (
                stream_interface is not None
            ), f"Expected stream '{stream.id}' to be created"
            self.consumers[stream.id] = Consumer(
                stream_interface=stream_interface,
                sample_callback=callback,
                mode=Mode.SYNC,
                stream_id=stream.id,
            )

    @abstractmethod
    def write(self, messages_by_logging_id: Mapping[str, Sequence[Message]]) -> None:
        """
        Writes messages to disk.

        Args:
            messages_by_logging_id:
                The messages to write to disk, keyed by the logging id to write to.
        """
        raise NotImplementedError()

    @background
    async def run_logger(self) -> None:
        import asyncio

        loop = asyncio.get_event_loop()

        self.running = True
        buffer_size = self.config.buffer_size
        flush_period = self.config.flush_period
        last_flushed_at = time.perf_counter()
        while self.running:
            current_time = time.perf_counter()
            if len(self.buffer) >= buffer_size or (
                flush_period is not None
                and current_time - last_flushed_at >= flush_period
            ):
                last_flushed_at = current_time
                flushed_buffer = self.flush_buffer()
                if sum(len(messages) for messages in flushed_buffer.values()) > 0:
                    await loop.run_in_executor(None, self.write, flushed_buffer)
            await asyncio.sleep(0.01)

    def buffer_message(self, logging_id: str, message: Message) -> None:
        self.buffer.append((logging_id, message))

    def flush_buffer(self) -> Dict[str, List[Message]]:
        self.buffer, flushed_buffer = [], self.buffer
        result: Dict[str, List[Message]] = {}
        for logging_id, message in flushed_buffer:
            if logging_id not in result:
                result[logging_id] = [message]
            else:
                result[logging_id].append(message)
        return result

    def _get_logger_callback(
        self, logging_id: str, stream: Stream
    ) -> Callable[[Message], None]:
        # We add the correct type annotation so LabGraph knows what message type to
        # deserialize to
        assert stream.message_type is not None
        MessageType: Type[Message] = stream.message_type

        def callback(message: MessageType) -> None:  # type: ignore
            self.buffer_message(logging_id, message)

        return callback

    def cleanup(self) -> None:
        self.running = False
        if len(self.buffer) > 0:
            self.write(self.flush_buffer())
