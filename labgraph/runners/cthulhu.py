#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from .._cthulhu.cthulhu import register_stream
from ..graphs.module import Module
from ..util.logger import get_logger


logger = get_logger(__name__)


def create_module_streams(module: Module) -> None:
    """
    Creates the Cthulhu streams defined on the module.

    Args:
        module: The module to create Cthulhu streams for.
    """
    logger.debug(f"{module}:creating cthulhu streams")

    # Create the streams
    for stream in module.__streams__.values():
        if stream.message_type is None:
            warning_message = (
                "Found no message types for a stream. This could be because the "
                "topic is never used in Python. Consume a topic with a message "
                "type in Python to make this stream work. This stream contains the "
                "following topics:\n"
            )
            for topic_path in stream.topic_paths:
                warning_message += f"- {topic_path}\n"

            logger.warning(warning_message)

            continue

        logger.debug(
            f"{module}:{stream.id}:creating cthulhu stream for topics "
            f"{', '.join(stream.topic_paths)}"
        )
        register_stream(stream.id, stream.message_type)
