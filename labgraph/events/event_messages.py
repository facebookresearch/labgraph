#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ..messages import TimestampedMessage


class WaitBeginMessage(TimestampedMessage):
    """
    Message sent by an EventGeneratorNode to signal the start of
    an expected wait on its recipient.

    Args:
        timeout: The maximum amount of time the wait may last.
    """

    timeout: float


class WaitEndMessage(TimestampedMessage):
    """
    Message sent back to an EventGeneratorNode to indicate that
    the sender has finished waiting.

    Args:
        wait_length: The actual length of the wait, in seconds.
    """

    wait_length: float


class TerminationMessage(TimestampedMessage):
    """
    Message sent by an EventGeneratorNode to signal the end of the
    experiment.  Publisher nodes waiting indefinitely to send out
    wait-end messages should stop publishing once received.
    """

    pass
