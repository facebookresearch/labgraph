#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import functools
import inspect
from contextlib import contextmanager
from typing import (
    Any,
    AsyncIterable,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from ..messages.message import Message
from ..util.testing import get_event_loop
from .config import Config
from .method import AsyncPublisher
from .node import Node
from .state import State
from .topic import Topic


N = TypeVar("N", bound=Node)  # Node type
T = TypeVar("T", bound=Tuple[Topic, Message])  # Type yielded by async functions


class NodeTestHarness(Generic[N]):
    """
    Utility class for testing LabGraph nodes. This allows a user to test some behavior
    of a node in an asyncio event loop, with the harness taking care of setting up and
    cleaning up the node.

    Args:
        node_type: The type of node this harness will test.
    """

    def __init__(self, node_type: Type[N]) -> None:
        self.node_type: Type[N] = node_type

    @contextmanager
    def get_node(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> Iterator[N]:
        """
        Context manager to create, configure and yield a node of specified type.
        Node is cleaned up when the context manager exits.

        Args:
            config: The configuration to set on the node, if provided.
            state: The state to set on the Node, if provided.
        """
        node = None
        try:
            node = self.node_type(config=config, state=state)
            node.setup()
            yield node
        finally:
            if node is not None:
                node.cleanup()


@overload
def run_with_harness(
    node_type: Type[N],
    fn: Callable[[N], AsyncIterable[T]],
    config: Optional[Config],
    state: Optional[State],
    max_num_results: Optional[int] = None,
) -> List[T]:
    ...


@overload
def run_with_harness(
    node_type: Type[N],
    fn: Callable[[N], Awaitable[T]],
    config: Optional[Config],
    state: Optional[State],
) -> T:
    ...


def run_with_harness(node_type, fn, config=None, state=None, max_num_results=None):
    """
    Runs an async function on a new node of the provided type using `NodeTestHarness`.

    Args:
        node_type: The type of node to create.
        fn:
            The async function to run. An instance of a node typed `node_type` will be
            provided to the function as an argument.
        config: The configuration to set on the node, if provided.
        state: The state to set on the node, if provided.
        max_num_results:
          If `fn` is an async generator, the maximum number of results it will generate.
          If this is `None`, then the generator can produce an unbounded number of
          results.
    """
    # Check whether the max_num_results argument was improperly provided
    _check_max_num_results_arg(run_with_harness.__name__, fn, max_num_results)

    test_harness = NodeTestHarness(node_type=node_type)
    with test_harness.get_node(config=config, state=state) as node:
        return run_async(fn, args=[node], max_num_results=max_num_results)


@overload
def run_async(
    fn: Callable[..., Awaitable[T]],
    args: Optional[Sequence[Any]] = None,
    kwargs: Optional[Mapping[str, Any]] = None,
) -> T:
    ...


@overload
def run_async(
    fn: Callable[..., AsyncIterable[T]],
    args: Optional[Sequence[Any]] = None,
    kwargs: Optional[Mapping[str, Any]] = None,
    max_num_results: Optional[int] = None,
) -> List[T]:
    ...


def run_async(fn, args=None, kwargs=None, max_num_results=None):
    """
    Runs an async function to completion. Uses the current thread's event loop. Blocks
    until the async function has finished executing. Forwards all arguments after `fn`
    to the async function.

    Args:
        fn: The async function to run.
        args: Positional arguments to forward to the function.
        kwargs: Keyword arguments to forward to the function.
        max_num_results:
          If `fn` is an async generator, the maximum number of results it will generate.
          If this is `None`, then the generator can produce an unbounded number of
          results.
    """
    # Check whether the max_num_results argument was improperly provided
    _check_max_num_results_arg(run_async.__name__, fn, max_num_results)

    # Unwrap functools.partial so we can check whether it is async
    if isinstance(fn, functools.partial):
        test_fn = fn.func
    else:
        test_fn = fn
    if inspect.isasyncgenfunction(test_fn):
        return get_event_loop().run_until_complete(
            _async_generator_to_list(
                fn=fn,
                args=args or [],
                kwargs=kwargs or {},
                max_num_results=max_num_results,
            )
        )
    elif asyncio.iscoroutinefunction(test_fn):
        return get_event_loop().run_until_complete(fn(*(args or []), **(kwargs or {})))
    else:
        raise TypeError(f"{run_async.__name__}: function '{fn}' is not async")


def _check_max_num_results_arg(
    called_fn_name: str,
    fn: Union[Callable[..., Awaitable[Any]], Callable[..., AsyncIterable[Any]]],
    max_num_results: Optional[int] = None,
) -> None:
    if not inspect.isasyncgenfunction(fn) and max_num_results is not None:
        raise TypeError(
            f"{called_fn_name}: function '{fn}' is not an async generator but "
            "max_num_results was provided"
        )


async def _async_generator_to_list(
    fn: Callable[..., AsyncIterable[T]],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
    max_num_results: Optional[int] = None,
) -> List[T]:
    if max_num_results is not None and max_num_results < 0:
        raise ValueError("max_num_results must be non-negative")
    result = []
    async for retval in fn(*args, **kwargs):
        result.append(retval)
        if max_num_results is not None and len(result) >= max_num_results:
            return result
    return result
