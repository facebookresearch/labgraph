# Copyright 2004-present Facebook. All Rights Reserved.

from collections import deque
from dataclasses import astuple, dataclass
from typing import Callable, List, Optional, Type

import labgraph as lg


TriggerWindowPredicate = Callable[[List[lg.TimestampedMessage]], bool]


@dataclass
class WindowTriggerMessageAndNode:
    message: lg.TimestampedMessage
    node: lg.Node

    def __iter__(self):
        return iter(astuple(self))


class WindowTriggerConfig(lg.Config):
    """Config for the node class produced by `make_window_trigger_node()`

    Members
    ----------
    length: int
        How many messages should be in a window.
    """

    length: int


@dataclass
class _WindowEmitter:
    """
    A stateful object that keeps track of `n` samples from a stream, and
    returns the `n` samples if some trigger predicate returns true for the
    current set of samples.
    """

    # Window lengths are in number of messages, since the time stamps for the
    # messages can vary and lead to uneven window sizes.
    length: int
    trigger_window_predicate: TriggerWindowPredicate

    def __post_init__(self):
        self._window = deque(maxlen=self.length)

    def __update_window(self, message: lg.TimestampedMessage):
        self._window.append(message)

    @property
    def __window_is_full(self):
        return len(self._window) >= self.length

    def __call__(
        self, message: lg.TimestampedMessage
    ) -> Optional[List[lg.TimestampedMessage]]:
        self.__update_window(message)
        if self.__window_is_full:
            if self.trigger_window_predicate(self._window):
                return list(self._window)
        return None


def make_window_trigger_message(message_type: Type[lg.TimestampedMessage]):
    class WindowTriggerMessage(lg.TimestampedMessage):
        sample: List[message_type]

    return WindowTriggerMessage


def make_window_trigger_node(
    message_type: Type[lg.TimestampedMessage],
    trigger_window_predicate: TriggerWindowPredicate,
) -> WindowTriggerMessageAndNode:
    """Generates a node that windows from a stream if some trigger fires.

    Parameters
    ----------
    message_type: type
        The type of the message for the stream to window/buffer
    trigger_window_predicate: TriggerWindowPredicate
        Whether to send out the current window to a stream or not.

    Returns
    -------
    WindowTriggerMessageAndNode
        A dataclass with a `message` field for the type of the output message
        from the node, and `node` field that holds the window triggering node.

    Example
    -------

    Say you are streaming simple messages and want to capture every 10 samples
    where the first sample is zero. First, define the messages that are going
    to be streamed.

    >>> import labgraph as lg
    >>> class SampleMessage(lg.TimestampedMessage):
    ...     field: int

    Now define the number of samples that are in a window

    >>> n_samples = 10

    Along with a trigger function, which determines when a list of those
    messages is a window that you want. We specified that we wanted the buffer
    to have the `SampleMessage` field be zero as the first message in the
    window, which can be presented as the following function.

    >>> def trigger(messages: List[SampleMessage]) -> bool:
    ...     return messages[0].field == 0
    >>>

    Finally, pass the window length and trigger function to the
    `make_window_trigger_node` function to generate a Labgraph node that will
    buffer a stream and return windows into that stream that cause the trigger
    function to return True.

    >>> message_and_node = make_window_trigger_node(n_samples, trigger)

    Now just unpack the result as you would like. If you want to use in a
    graph, you will likely need to assign the results of
    `make_window_trigger_node` to the top level of a module for Labgraph to be
    able to pick up the classes/types correctly.

    >>> WindowTriggerNode = message_and_node.node
    >>> WindowTriggerMessage = message_and_node.message
    """

    WindowTriggerMessage = make_window_trigger_message(message_type)

    class WindowTriggerNode(lg.Node):
        INPUT = lg.Topic(message_type)
        OUTPUT = lg.Topic(WindowTriggerMessage)

        window_emitter: _WindowEmitter

        config: WindowTriggerConfig

        def setup(self) -> None:
            self.window_emitter = _WindowEmitter(
                self.config.length, trigger_window_predicate
            )

        @lg.subscriber(INPUT)
        @lg.publisher(OUTPUT)
        async def run(self, message: message_type) -> lg.AsyncPublisher:
            optional_window = self.window_emitter(message)

            if optional_window is not None:
                yield self.OUTPUT, WindowTriggerMessage(
                    timestamp=message.timestamp, sample=optional_window
                )

    return WindowTriggerMessageAndNode(WindowTriggerMessage, WindowTriggerNode)
