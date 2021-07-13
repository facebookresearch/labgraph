#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import contextlib
import functools
import inspect
import os
import pickle
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterable,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
)

import yappi
from labgraph_cpp import NodeBootstrapInfo, NodeTopic  # type: ignore

# HACK: Import from LabGraph's wrapper of Cthulhu before importing dynamic libs to set
# the shared memory name
from .._cthulhu.cthulhu import (
    Consumer,
    LabGraphCallbackParams,
    Mode,
    Producer,
    format_performance_summary,
    get_stream,
)
from ..graphs.cpp_node import CPPNode
from ..graphs.method import SubscriberType, Transformer
from ..graphs.module import Module
from ..graphs.topic import PATH_DELIMITER, Topic
from ..messages.message import Message
from ..util.logger import get_logger
from .cthulhu import create_module_streams
from .exceptions import ExceptionMessage, NormalTermination
from .process_manager import ProcessPhase
from .profiling import should_profile, write_profiling_results
from .runner import Runner, RunnerOptions


logger = get_logger(__name__)

BARRIER_TIMEOUT = 60
ASYNCIO_SHUTDOWN_POLL_TIME = 1
ASYNCIO_SHUTDOWN_TIME = 10
DEFAULT_QUEUE_CAPACITY = 10000

EXCEPTION_STREAM_SUFFIX = "_EXCEPTION"


@dataclass
class LocalRunnerState:
    """
    Describes the state of a `LocalRunner`.

    Args:
        lock:
            Lock that can be used for synchronizing access to state between the
            `LocalRunner`'s threads.
        producers: The Cthulhu producers used by the module.
        consumers: The Cthulhu consumers used by the module.
        callbacks: The callbacks registered by the module's asyncio thread.
        setup_barrier:
            Barrier for coordinating startup between the `LocalRunner`'s threads.
        ready_event:
            A signal that the background thread waits on to know that the main thread
            has completed all its startup tasks.
        setup_complete: A flag indicating whether setup is complete for this module.
        cleanup_started: A flag indicating whether cleanup has started for this module.
    """

    lock: threading.Lock = field(default_factory=threading.Lock)
    producers: Dict[str, Producer] = field(default_factory=dict)
    consumers: Dict[str, Consumer] = field(default_factory=dict)
    callbacks: Dict[str, SubscriberType] = field(default_factory=dict)
    setup_barrier: threading.Barrier = field(
        default_factory=functools.partial(threading.Barrier, 2, timeout=BARRIER_TIMEOUT)
    )
    ready_event: threading.Event = field(default_factory=threading.Event)
    setup_complete: bool = False
    cleanup_started: bool = False


class LocalRunner(Runner):
    """
    A utility for running LabGraph modules. Given a module, runs the computation it
    describes by creating two threads, one for its foreground processing and one for
    its event loop processing.

    Foreground processing consists of:

    - Cthulhu stream setup
    - Graph setup and cleanup
    - Methods on nodes decorated with @main

    Background processing consists of:

    - Methods on nodes decorated with @publisher and/or @subscriber
    - Methods on nodes decorated with @background

    Args:
        module: The module to run.
        options: Options describing how the module will be run.
    """

    def __init__(self, module: Module, options: Optional[RunnerOptions] = None) -> None:
        self._module = module
        self._options = options or RunnerOptions()

        self._running = False
        self._exception: Optional[BaseException] = None
        self._handled_exception: bool = False

    def run(self) -> None:
        """
        Starts the LabGraph module. Returns when the module has terminated.
        """
        try:
            if should_profile():
                yappi.set_clock_type("cpu")
                yappi.start()
            self._running = True
            logger.debug(f"{self._module}:started")
            self._state = LocalRunnerState()

            # Start the background thread (runs the event loop)
            async_thread = _AsyncThread(runner=self)
            async_thread.start()
            logger.debug(f"{self._module}:asyncio thread starting")

            # Start the monitor thread (monitors the graph for termination)
            monitor_thread = _MonitorThread(runner=self)
            monitor_thread.start()
            logger.debug(f"{self._module}:monitor thread started")

            # Run nodes' setup() functions
            logger.debug(f"{self._module}:setup running")
            self._run_setup()
            self._state.setup_complete = True
            logger.debug(f"{self._module}:setup done")

            # Thread barrier: signal nodes' setup is done + wait for background thread
            # to set up callbacks
            self._state.setup_barrier.wait()
            logger.debug(f"{self._module}:asyncio thread ready")

            # Set up Cthulhu
            logger.debug(f"{self._module}:cthulhu setting up")
            self._setup_cthulhu()
            logger.debug(f"{self._module}:cthulhu ready")

            # Coordinate process readiness with other processes, if present
            if self._options.bootstrap_info is not None:
                # Signal that this process is ready
                self._options.bootstrap_info.process_manager_state.update(
                    self._options.bootstrap_info.process_name, ProcessPhase.READY
                )
                logger.debug(f"{self._module}:waiting for other processes in graph")
                self._wait_for_ready()
                logger.debug(f"{self._module}:graph ready")
                self._options.bootstrap_info.process_manager_state.update(
                    self._options.bootstrap_info.process_name, ProcessPhase.RUNNING
                )

            # Thread event: signal to background thread that Cthulhu and graph are
            # set up
            self._state.ready_event.set()

            # Run @main method, if any
            logger.debug(f"{self._module}:@main running")
            self._run_main()
            logger.debug(f"{self._module}:@main complete")

            # Wait for the background thread to finish (this will happen shortly after
            # producers stop producing, causing the task queue to clear up, or when an
            # exception is raised)
            logger.debug(f"{self._module}:waiting for async thread")
            async_thread.join()
            logger.debug(f"{self._module}:async thread complete")

            # If the background thread raised an exception, re-raise it on the main
            # thread
            if self._exception is not None:
                raise self._exception
        except BaseException:
            self._handle_exception()
        finally:
            self._running = False
            if self._options.bootstrap_info is not None:
                # Signal that this process is ready
                self._options.bootstrap_info.process_manager_state.update(
                    self._options.bootstrap_info.process_name, ProcessPhase.STOPPING
                )
            if not self._state.cleanup_started and self._state.setup_complete:
                # Run nodes' cleanup() functions
                self._state.cleanup_started = True
                logger.debug(f"{self._module}:running cleanup in main thread")
                self._run_cleanup()
                logger.debug(f"{self._module}:cleanup complete")

            logger.debug(f"{self._module}:waiting for monitor thread")
            monitor_thread.join()
            logger.debug(f"{self._module}:monitor thread complete")

            if should_profile():
                yappi.stop()
                write_profiling_results(self._module)

                for stream_id, consumer in self._state.consumers.items():
                    performance_summary = consumer.get_performance_summary()
                    if performance_summary.num_calls > 0:
                        logger.info(
                            f"PERFORMANCE SUMMARY FOR {stream_id}:\n"
                            f"{format_performance_summary(performance_summary)}"
                        )

            logger.debug(f"{self._module}:terminating")

            if self._options.bootstrap_info is not None:
                # Signal that this process is ready
                self._options.bootstrap_info.process_manager_state.update(
                    self._options.bootstrap_info.process_name, ProcessPhase.TERMINATED
                )
            else:
                # If there is an exception, raise it to the caller
                if self._exception is not None:
                    raise self._exception

    def _setup_cthulhu(self) -> None:
        """
        Sets up Cthulhu as the transport for the LabGraph graph. Creates streams only
        if the module has no parent graph. Then creates producers and consumers
        according to the publishers and subscribers in the module.
        """
        if self._options.bootstrap_info is None:
            create_module_streams(self._module)
        self._create_producers()
        self._create_consumers()
        self._bootstrap_cpp_nodes()

    def _bootstrap_cpp_nodes(self) -> None:
        module_tuples = list(self._module.__descendants__.items())
        module_tuples.append(("", self._module))
        for node_path, node in module_tuples:
            if not isinstance(node, CPPNode):
                continue
            node_topics: List[Tuple[str, str]] = []
            for topic_name in node.__topics__.keys():
                if node_path == "":
                    topic_path = topic_name
                else:
                    topic_path = PATH_DELIMITER.join((node_path, topic_name))
                stream = self._module._stream_for_topic_path(topic_path)
                if stream.message_type is None:
                    continue
                root_stream_id = stream.id
                if self._options.bootstrap_info is not None:
                    if self._options.bootstrap_info.stream_namespace is not None:
                        root_stream_id = (
                            self._options.bootstrap_info.stream_ids_by_topic_path[
                                f"{self._options.bootstrap_info.stream_namespace}"
                                f"{PATH_DELIMITER}{topic_path}"
                            ]
                        )
                    else:
                        root_stream_id = (
                            self._options.bootstrap_info.stream_ids_by_topic_path[
                                topic_path
                            ]
                        )
                node_topics.append((topic_name, root_stream_id))
            bootstrap_info = NodeBootstrapInfo(
                topics=[
                    NodeTopic(topic_name, stream_id)
                    for topic_name, stream_id in node_topics
                ]
            )
            node._bootstrap(bootstrap_info)

    def _wait_for_ready(self) -> None:
        if self._options.bootstrap_info is None:
            return
        while (
            self._options.bootstrap_info.process_manager_state.get_overall().value
            < ProcessPhase.READY.value
        ):
            time.sleep(0.1)

    def _run_main(self) -> None:
        """
        Runs the @main-decorated method in this module, if any.
        """
        main_path, _ = self._module.main
        if main_path is None:
            return
        main_method = self._module._get_main_method(main_path)
        main_method()

    def _create_producers(self) -> None:
        """
        Creates a Cthulhu `StreamProducer` for each stream published to in this module.
        """
        logger.debug(f"{self._module}:creating cthulhu producers")
        produced_topic_paths = set()
        for publisher in self._module.publishers.values():
            for topic_path in publisher.published_topic_paths:
                produced_topic_paths.add(topic_path)

        for topic_path in produced_topic_paths:
            # If running as a subprocess, get the topic path relative to the graph root
            root_topic_path = topic_path
            local_stream_id = self._module._stream_for_topic_path(topic_path).id
            root_stream_id = local_stream_id
            if self._options.bootstrap_info is not None:
                if self._options.bootstrap_info.stream_namespace is not None:
                    root_topic_path = (
                        f"{self._options.bootstrap_info.stream_namespace}"
                        f"{PATH_DELIMITER}{root_topic_path}"
                    )
                root_stream_id = self._options.bootstrap_info.stream_ids_by_topic_path[
                    root_topic_path
                ]

            cthulhu_stream = get_stream(root_stream_id)
            assert cthulhu_stream is not None, (
                f"Cthulhu stream for topic {root_topic_path} ({root_stream_id}) was "
                "not created"
            )
            producer = Producer(stream_interface=cthulhu_stream, mode=Mode.ASYNC)
            with self._state.lock:
                self._state.producers[local_stream_id] = producer

    def _callback_for_stream(self, stream_id: str) -> Callable[..., None]:
        """
        Returns a callback for the given stream id. The actual callbacks are registered
        in the `LocalRunner`'s state object by the asyncio thread. This returns a
        callback that looks up the registered callback and then calls it.
        """
        # Typing `callback` with `MessageType` allows us to know how to deserialize
        # the incoming message in shared memory

        MessageType = self._module.__streams__[stream_id].message_type
        assert MessageType is not None
        if self._options.aligner is not None:
            # Type with extra information for the aligner
            MessageType = LabGraphCallbackParams[MessageType]  # type: ignore

        def callback(message: MessageType) -> None:  # type: ignore
            with self._state.lock:
                callback_fn = self._state.callbacks[stream_id]
            callback_fn(message)

        return callback

    def _create_consumers(self) -> None:
        """
        Creates a Cthulhu `StreamConsumer` for every stream subscribed to in this
        module.
        """
        logger.debug(f"{self._module}:creating cthulhu consumers")

        # Register a `StreamConsumer` for each stream
        for subscriber in self._module.subscribers.values():
            # If running as a subprocess, get the topic path relative to the graph root
            root_topic_path = subscriber.subscribed_topic_path
            local_stream_id = self._module._stream_for_topic_path(
                subscriber.subscribed_topic_path
            ).id
            root_stream_id = local_stream_id
            if self._options.bootstrap_info is not None:
                if self._options.bootstrap_info.stream_namespace is not None:
                    root_topic_path = (
                        f"{self._options.bootstrap_info.stream_namespace}"
                        f"{PATH_DELIMITER}{root_topic_path}"
                    )
                root_stream_id = self._options.bootstrap_info.stream_ids_by_topic_path[
                    root_topic_path
                ]
            cthulhu_stream = get_stream(root_stream_id)
            assert cthulhu_stream is not None, (
                f"Cthulhu stream for topic {root_topic_path} ({root_stream_id}) was "
                "not created"
            )
            consumer = Consumer(
                stream_interface=cthulhu_stream,
                sample_callback=self._callback_for_stream(local_stream_id),
                mode=Mode.ASYNC,
                stream_id=local_stream_id,
            )
            consumer.queue_capacity = DEFAULT_QUEUE_CAPACITY
            with self._state.lock:
                self._state.consumers[local_stream_id] = consumer

    def _run_setup(self) -> None:
        """
        Runs the `setup()` function on each descendant module of this `LocalRunner`'s
        module, ensuring that every parent has `setup()` called before any of its
        descendants.
        """
        setup_stack: List[Module] = [self._module]
        while len(setup_stack) > 0:
            module = setup_stack.pop()
            module.setup()
            for child_module in module.__children__.values():
                setup_stack.append(child_module)

    def _run_cleanup(self) -> None:
        """
        Runs the `cleanup()` function on each descendant module of this `LocalRunner`'s
        module, ensuring that every parent has `cleanup()` called before any of its
        descendants.
        """
        cleanup_stack: List[Module] = [self._module]
        while len(cleanup_stack) > 0:
            module = cleanup_stack.pop()
            module.cleanup()
            if isinstance(module, Module):
                for child_module in module.__children__.values():
                    cleanup_stack.append(child_module)

    def _handle_exception(self) -> None:
        if self._handled_exception:
            return
        else:
            self._handled_exception = True

        self._running = False

        _, exception, _ = sys.exc_info()

        if isinstance(exception, NormalTermination):
            logger.info(f"{self._module}:shutting down normally")
        else:
            # Log exception info
            logger.critical(f"{self._module}:UNCAUGHT EXCEPTION")
            logger.critical(traceback.format_exc())
            self._exception = exception

        if self._options.bootstrap_info is not None:
            if not isinstance(exception, NormalTermination):
                self._options.bootstrap_info.process_manager_state.set_exception(
                    self._options.bootstrap_info.process_name, repr(exception)
                )


class _AsyncThread(threading.Thread):
    """
    A thread for the asyncio event loop used by a `LocalRunner`. This frees the
    `LocalRunner`'s main thread for code that needs the main thread, e.g., UI code.

    Args:
        module: The module being run.
        options: The options used to configure the `LocalRunner`.
        state: The state shared with the `LocalRunner`.
    """

    def __init__(self, runner: LocalRunner) -> None:
        super().__init__()
        self.runner = runner
        self.module = runner._module
        self.options = runner._options or RunnerOptions()
        self.state = runner._state
        self.original_stream_types = self.get_original_stream_types()

    def run(self) -> None:
        """
        Runs the `_AsyncThread`'s event loop.
        """

        logger.debug(f"{self.module}:started background thread")

        # We import asyncio here and keep asyncio object construction within this method
        # in order to ensure that no asyncio state leaks into the global state,
        # guaranteeing it will never be pickled. We want this because subtle bugs can
        # arise when asyncio objects are transported across process boundaries. Many
        # of the objects in this method are kept as locals rather than being set as
        # properties in order to avoid accidentally accessing them from the main thread,
        # e.g., in the `LocalRunner`.

        import asyncio

        # Create event loop
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(self.handle_exception)
        asyncio.set_event_loop(loop)

        try:
            # Create callback methods that run in the event loop
            with self.state.lock:
                for stream in self.module.__streams__.values():
                    callbacks = []
                    for subscriber_path, subscriber in self.module.subscribers.items():
                        if subscriber.subscribed_topic_path in stream.topic_paths:
                            if isinstance(subscriber, Transformer):
                                callbacks.append(
                                    self.wrap_transformer_callback(
                                        transformer_path=subscriber_path, loop=loop
                                    )
                                )
                            else:
                                callbacks.append(
                                    self.wrap_subscriber_callback(
                                        subscriber_path=subscriber_path, loop=loop
                                    )
                                )

                    stream_callback = self.wrap_all_callbacks(callbacks, loop=loop)

                    if self.options.aligner is not None:
                        # Inject aligner into callback if present
                        self.options.aligner.register(stream.id, stream_callback)
                        stream_callback = self.options.aligner.push

                    self.state.callbacks[stream.id] = stream_callback

            # Thread barrier: wait for nodes' setup + signal to main thread that
            # callbacks are ready
            self.state.setup_barrier.wait()

            # Thread event: wait for main thread to set up Cthulhu
            self.state.ready_event.wait()

            # Schedule startup coroutines in event loop
            for awaitable in self.get_startup_methods():
                asyncio.ensure_future(awaitable, loop=loop)

            # Schedule aligner task
            if self.options.aligner is not None:
                logger.debug(f"{self.module}:background thread:run aligner")
                loop.create_task(self.options.aligner.run())

            logger.debug(f"{self.module}:background thread:run event loop")

            with contextlib.ExitStack() as run_stack:
                if "PROFILE" in os.environ:
                    # Run yappi profiling
                    run_stack.enter_context(yappi.run())

                # Run event loop
                while self.runner._running:
                    loop.run_until_complete(asyncio.sleep(0.01))
        except BaseException:
            logger.debug(f"{self.module}:handling exception in background thread")
            self.runner._handle_exception()

        if not self.state.cleanup_started and self.state.setup_complete:
            # The main thread may not be able to run cleanup if it is blocked by a
            # @main function. So we try to run cleanup in the background thread
            # first.
            self.state.cleanup_started = True
            logger.debug(f"{self.module}:running cleanup in background thread")
            self.runner._run_cleanup()
            logger.debug(f"{self.module}:cleanup complete")

        # Terminate the aligner
        if self.options.aligner is not None:
            logger.debug(f"{self.module}:background thread:terminate aligner")
            self.options.aligner.wait_for_completion()
        logger.debug(f"{self.module}:background thread:shutting down async gens")
        loop.run_until_complete(loop.shutdown_asyncgens())

        logger.debug(f"{self.module}:background thread:waiting for pending tasks")
        pending_start_time = time.perf_counter()
        while True:
            time.sleep(ASYNCIO_SHUTDOWN_POLL_TIME)
            pending = [
                task for task in asyncio.Task.all_tasks(loop=loop) if not task.done()
            ]
            if len(pending) == 0:
                logger.debug(f"{self.module}:background thread:closing event loop")
                loop.close()
                return
            elif time.perf_counter() - pending_start_time >= ASYNCIO_SHUTDOWN_TIME:
                logger.warning(
                    f"{self.module}:background thread:closing event loop with "
                    f"{len(pending)} tasks left"
                )
                # Suppress exception handling - otherwise the handler catches "Task
                # was destroyed but it is pending!"
                loop.set_exception_handler(lambda _l, _c: None)
                try:
                    loop.close()
                except Exception:
                    # Exception expected with pending tasks
                    pass
                return
            logger.debug(f"{self.module}:{len(pending)} tasks left")
            loop.run_until_complete(asyncio.sleep(1))

    def get_original_stream_types(self) -> Dict[str, Type[Message]]:
        stream_types = {}
        for stream in self.module.__streams__.values():
            publishers = [
                publisher
                for publisher in self.module.publishers.values()
                if len(
                    set(publisher.published_topic_paths).intersection(
                        stream.topic_paths
                    )
                )
                > 0
            ]
            if len(publishers) != 1:
                continue
            publisher = publishers[0]
            topic_path = list(
                set(publisher.published_topic_paths).intersection(stream.topic_paths)
            )[0]
            topic = self.module.__topics__[topic_path]

            subscriber_paths = [
                subscriber_path
                for subscriber_path, subscriber in self.module.subscribers.items()
                if subscriber.subscribed_topic_path in stream.topic_paths
            ]
            for subscriber_path in subscriber_paths:
                stream_types[subscriber_path] = topic.message_type
        return stream_types

    def get_startup_methods(self) -> List[Coroutine[None, None, None]]:
        return [
            self.run_publisher_method(publisher_method)
            for publisher_method in self.get_publisher_methods()
        ] + self.get_background_methods()  # type: ignore

    async def run_publisher_method(
        self, publisher_method: Callable[[], AsyncIterable[Tuple[Topic, Message]]]
    ) -> None:
        import asyncio

        async for topic, message in publisher_method():
            topic_path = self.module._get_topic_path(topic)
            stream = self.module._stream_for_topic_path(topic_path)
            producer = self.state.producers[stream.id]
            producer.produce_message(message)

    def get_publisher_methods(
        self,
    ) -> List[Callable[[], AsyncIterable[Tuple[Topic, Message]]]]:
        return [
            self.module._get_publisher_method(publisher_path)
            for publisher_path, publisher in self.module.publishers.items()
            # Transformers don't run on graph startup
            if not isinstance(publisher, Transformer)
        ]

    def get_background_methods(self) -> List[Awaitable[None]]:
        return [
            self.module._get_background_method(background_path)()
            for background_path in self.module.backgrounds.keys()
        ]

    def wrap_subscriber_callback(
        self, subscriber_path: str, loop: Any
    ) -> Callable[[Message], Awaitable[None]]:
        """
        Returns a subscriber callback as an async function.

        Args:
            subscriber_path: The path to the @subscriber-decorated callback.
            loop: The event loop to run the callback on.
        """

        subscriber_method = self.module._get_subscriber_method(subscriber_path)

        if inspect.iscoroutinefunction(subscriber_method):
            return subscriber_method

        async def subscriber_callback(message: Message) -> None:
            if subscriber_path in self.original_stream_types:
                object.__setattr__(
                    message,
                    "__original_message_type__",
                    self.original_stream_types[subscriber_path],
                )
            if loop.is_closed():
                logger.warn(
                    f"{message.__class__.__name__} dropped while graph shutting down"
                )
                return
            loop.call_soon(self.module._get_subscriber_method(subscriber_path), message)
            return

        return subscriber_callback

    def wrap_transformer_callback(
        self, transformer_path: str, loop: Any
    ) -> Callable[[Message], Awaitable[None]]:
        """
        Returns a transformer callback as an async function.

        Args:
            transformer_path:
                The path to the callback with both @subscriber and @publisher
                decorators.
            loop: The event loop to run the callback on.
        """

        async def transformer_callback(message: Message) -> None:
            if transformer_path in self.original_stream_types:
                object.__setattr__(
                    message,
                    "__original_message_type__",
                    self.original_stream_types[transformer_path],
                )
            await self.run_publisher_method(
                functools.partial(
                    self.module._get_transformer_method(transformer_path), message
                )
            )

        return transformer_callback

    def wrap_all_callbacks(
        self, callbacks: List[Callable[[Message], Awaitable[None]]], loop: Any
    ) -> SubscriberType:
        """
        Given a list of callbacks, returns a callback that wraps all of them by
        scheduling all of them on the event loop when a message is received.

        Args:
            callbacks: The callbacks to wrap.
            loop: The event loop to schedule the callbacks on.
        """
        import asyncio

        def callback(message: Message) -> None:
            if loop.is_closed():
                logger.warn(
                    f"{message.__class__.__name__} dropped while graph shutting down"
                )
                return
            for callback in callbacks:
                asyncio.ensure_future(callback(message), loop=loop)

        return callback

    def handle_exception(self, loop: Any, context: Dict[str, Any]) -> None:
        try:
            if "exception" in context:
                exception = context["exception"]
            else:
                exception = Exception(f"{context}")
            raise exception  # Re-raise the exception so the runner can see it
        except Exception:
            self.runner._handle_exception()


class _MonitorThread(threading.Thread):
    def __init__(self, runner: LocalRunner) -> None:
        super().__init__()
        self.runner = runner

    def run(self) -> None:
        if self.runner._options.bootstrap_info is None:
            return

        while True:
            if not self.runner._running:
                logger.debug(f"{self.runner._module}:monitor thread stopping")
                return

            try:
                if (
                    self.runner._options.bootstrap_info.process_manager_state.get_overall().value
                    >= ProcessPhase.STOPPING.value
                ):
                    logger.debug(
                        f"{self.runner._module}:stopping due to graph shutdown"
                    )
                    self.runner._running = False
                    return
            except (EOFError, ConnectionError, OSError, BrokenPipeError):
                logger.warning(f"{self.runner._module}:lost process manager, stopping")
                self.runner._running = False
            time.sleep(0.1)
