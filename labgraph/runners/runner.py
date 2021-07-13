#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Type

from ..graphs.module import Module
from ..graphs.parent_graph_info import ParentGraphInfo
from ..graphs.stream import Stream
from ..graphs.topic import PATH_DELIMITER, Topic
from ..loggers.hdf5.logger import HDF5Logger
from ..loggers.logger import Logger, LoggerConfig
from ..messages.message import Message
from ..messages.types import BytesType
from ..util.error import LabGraphError
from ..util.logger import get_logger
from .aligner import Aligner
from .process_manager import ProcessManagerState


@dataclass
class BootstrapInfo:
    process_name: str
    process_manager_state: ProcessManagerState
    stream_ids_by_topic_path: Dict[str, str]
    stream_namespace: Optional[str] = None


@dataclass
class RunnerOptions:
    """
    Options that can be provided to a `Runner`.

    Args:
        aligner:
            An `Aligner` object that describes an alignment algorithm to use on all
            streams.
        logger_type: The Python class for the logger type to use.
        logger_config: Configuration to provide the logger.
    """

    aligner: Optional[Aligner] = None
    bootstrap_info: Optional[BootstrapInfo] = None
    logger_type: Type[Logger] = HDF5Logger
    logger_config: LoggerConfig = field(default_factory=LoggerConfig)


class Runner(ABC):
    @abstractmethod
    def __init__(self, module: Module, options: Optional[RunnerOptions] = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()
