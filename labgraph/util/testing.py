#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import os
import socket
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

import pytest

from .random import random_string


FILENAME_LENGTH = 16

# Flag used to indicate that we are running in Sandcastle, and therefore should skip
# local tests.
#
# Some documentation of this env var here: https://fburl.com/wiki/9is1b6ks
SANDCASTLE_TEST_FLAG = "SANDCASTLE_NEXUS"


def get_test_filename(extension: str = "txt") -> str:
    """
    Returns a filename for testing purposes in the system temporary directory.

    Args:
        extension: The extension for the file.
    """

    file_path = str(
        Path(tempfile.gettempdir())
        / Path(f"{random_string(FILENAME_LENGTH)}.{extension}")
    )

    # Create the file
    with open(file_path, "w"):
        pass

    return file_path


def async_test(test: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for running an async test in an asyncio event loop.

    Args:
        test: The test function to decorate.
    """

    def test_wrapped(*args: Any, **kwargs: Any) -> None:
        get_event_loop().run_until_complete(test(*args, **kwargs))

    return test_wrapped


def local_test(test: Callable[..., Any]) -> Callable[..., Any]:
    return pytest.mark.skipif(  # type: ignore
        SANDCASTLE_TEST_FLAG in os.environ, reason="local test, skipping in Sandcastle"
    )(test)


def get_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]  # type: ignore


def get_event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
