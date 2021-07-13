#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import dataclasses
import importlib
import inspect
import multiprocessing as mp
import pickle
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Optional, Type

import yappi

from .._cthulhu.cthulhu import Consumer, Producer, register_stream
from ..graphs.graph import Graph
from ..graphs.module import Module
from ..graphs.parent_graph_info import ParentGraphInfo
from ..loggers.logger import Logger, LoggerConfig
from ..util.logger import get_logger
from .cthulhu import create_module_streams
from .exceptions import ExceptionMessage, NormalTermination
from .process_manager import ProcessInfo, ProcessManager
from .profiling import should_profile, write_profiling_results
from .runner import Runner, RunnerOptions
from .util import get_module_class


logger = get_logger(__name__)

BARRIER_TIMEOUT = 60
SHUTDOWN_PERIOD = 5
EXCEPTION_POLL_TIME = 1

EXCEPTION_STREAM_SUFFIX = "_EXCEPTION"

LOGGER_KEY = "__LOGGER__"


class ParallelRunner(Runner):
    def __init__(self, graph: Graph, options: Optional[RunnerOptions] = None) -> None:
        self._graph = graph
        self._options = options or RunnerOptions()

        # TODO: Validate process groups
        self._modules = tuple(self._graph.process_modules())
        self._logger: Optional[Logger] = None
        self._exception: Optional[BaseException] = None

        self._temp_files: List[str] = []

    def run(self) -> None:
        """
        Starts the LabGraph graph. Returns when the graph has terminated.
        """
        self._graph.setup()
        self._create_logger()
        create_module_streams(self._graph)
        self._start_processes()

    def _create_logger(self) -> None:
        streams_by_logging_id = self._graph._get_streams_by_logging_id()
        if len(streams_by_logging_id) == 0:
            return
        logger = self._options.logger_type(
            config=self._options.logger_config.replace(
                streams_by_logging_id=streams_by_logging_id
            )
        )
        self._modules = self._modules + (logger,)

    def _start_processes(self) -> None:
        processes = []
        for module in self._modules:
            assert isinstance(module, Module)
            python_module = self._get_class_module(module.__class__)
            module_class_name = module.__class__.__name__
            get_module_class(python_module, module_class_name)  # Validate class

            process_args = ["--module", f"{python_module}.{module_class_name}"]

            # Write config and state to disk for subprocess to use
            if module._config is not None:
                with tempfile.NamedTemporaryFile("wb", delete=False) as config_file:
                    pickle.dump(
                        (
                            self._get_class_qualname(module._config.__class__),
                            module._config.asdict(),
                        ),
                        config_file,
                    )
                self._temp_files.append(config_file.name)
                process_args += ["--config-file-path", config_file.name]

            if module.state is not None:
                with tempfile.NamedTemporaryFile("wb", delete=False) as state_file:
                    pickle.dump(
                        (
                            self._get_class_qualname(module.state.__class__),
                            dataclasses.asdict(module.state),
                        ),
                        state_file,
                    )
                self._temp_files.append(state_file.name)
                process_args += ["--state-file-path", state_file.name]

            # Write stream information to disk
            streams_by_topic_path = {}
            for stream in self._graph.__streams__.values():
                for topic_path in stream.topic_paths:
                    streams_by_topic_path[topic_path] = stream.id
            with tempfile.NamedTemporaryFile("wb", delete=False) as streams_file:
                pickle.dump(streams_by_topic_path, streams_file)
                self._temp_files.append(streams_file.name)
                process_args += ["--streams-file-path", streams_file.name]

            # Write runner options to disk
            with tempfile.NamedTemporaryFile("wb", delete=False) as options_file:
                pickle.dump(self._options, options_file)
                self._temp_files.append(options_file.name)
                process_args += ["--options-file-path", options_file.name]

            if module is self._graph:
                module_path = ""
            elif isinstance(module, Logger):
                module_path = LOGGER_KEY
            else:
                module_path = self._graph._get_module_path(module)
                process_args += ["--stream-namespace", module_path]
            processes.append(
                ProcessInfo(
                    name=module_path or module.__class__.__name__,
                    module=__name__.replace("parallel_runner", "entry"),
                    args=tuple(process_args),
                )
            )

        self._process_manager = ProcessManager(processes=processes)
        self._process_manager.run()

    def _get_class_qualname(self, cls: type) -> str:
        return f"{self._get_class_module(cls)}.{cls.__name__}"

    def _get_class_module(self, cls: type) -> str:
        python_module = cls.__module__
        if python_module != "__main__":
            return python_module

        # Getting the real module name for __main__ can be annoyingly complicated...
        try:
            entry_point: Optional[str] = None

            # Try to get the module name from the file path
            cls_file = inspect.getfile(cls)
            cls_path = Path(cls_file)
            path_components = cls_path.with_name(cls_path.stem).parts

            if all(not component.endswith(".pex") for component in path_components):
                while len(path_components) > 0:
                    try:
                        entry_point = ".".join(path_components)
                        importlib.import_module(entry_point)
                        break
                    except (ImportError, TypeError):
                        entry_point = None
                    finally:
                        path_components = path_components[1:]

            # Try to get the module name from the PEX
            if entry_point is None:

                if not sys.argv[0].endswith(".pex"):
                    raise RuntimeError()
                from _pex.pex_info import PexInfo  # type: ignore

                pex_info = PexInfo.from_pex(sys.argv[0])
                entry_point = pex_info.entry_point

            # Fail if all methods failed to find an entry point
            if entry_point is None:
                raise RuntimeError()

            assert isinstance(entry_point, str)
            entry_module = importlib.import_module(entry_point)
            if hasattr(entry_module, cls.__name__):
                return entry_point
            else:
                raise RuntimeError()
        except (ImportError, RuntimeError):
            raise RuntimeError(
                f"Putting {cls.__name__} in the main scope is preventing its use with "
                f"df.{self.__class__.__name__}. Please consider either a) creating "
                "another module to use as the main module or b) using __main__.py "
                "instead.\nhttps://docs.python.org/3.6/library/__main__.html"
            )


def run(graph_type: Type[Graph]) -> None:
    """
    Entry point for running LabGraph graphs. Call `run` with a LabGraph graph type to
    run a new graph of that type.
    """
    config_type = graph_type.__config_type__
    config = config_type.fromargs()
    graph = graph_type()
    graph.configure(config)
    runner = ParallelRunner(graph=graph)
    runner.run()
