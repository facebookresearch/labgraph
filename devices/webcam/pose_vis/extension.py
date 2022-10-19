#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import numpy as np
import labgraph as lg

from pose_vis.streams.messages import StreamMetaData
from abc import ABC, abstractmethod
from dataclasses import dataclass
from argparse import ArgumentParser, Namespace
from typing import Tuple, Any

@dataclass
class ExtensionResult():
    """
    Produced by `PoseVisExtension`

    Attributes:
        `data`: `Any`
    """
    data: Any

class PoseVisExtensionBase(ABC):
    """
    Abstract base class for `PoseVisExtension`

    Abstract methods:
        `register_args(self, parser: ArgumentParser) -> None`

        `check_enabled(self, args: Namespace) -> bool`

        `setup(self) -> None`

        `process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]`
        
        `cleanup(self) -> None`
    """
    @abstractmethod
    def register_args(self, parser: ArgumentParser) -> None:
        """
        Called before graph initialization and argument parsing
        
        Use this to register an argument that will allow this extension to be enabled or disabled
        """
        pass

    @abstractmethod
    def check_enabled(self, args: Namespace) -> bool:
        """
        Check the `ArgumentParser.parse_args()` result to determine if this extension should be enabled
        """
        pass

    @abstractmethod
    def setup(self) -> None:
        """
        Called on video stream setup
        """
        pass

    @abstractmethod
    def process_frame(self, frame: np.ndarray, metadata: StreamMetaData) -> Tuple[np.ndarray, ExtensionResult]:
        """
        Called once per frame inside of a video stream node

        Output should be a `Tuple` with an overlay image and the data used to produce that overlay
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Called on graph shutdown
        """
        pass

class PoseVisExtension(PoseVisExtensionBase):
    """
    An extension of the base class that Pose Vis uses to automatically initialize the following variables:

    Attributes:
        `extension_id`: `int`, a contiguous identifier for each enabled extension
    
    Methods:
        `set_enabled(self, extension_id: int) -> None`
    """
    extension_id: int

    def set_enabled(self, extension_id: int) -> None:
        """
        Called if this extension passes the `check_enabled` method
        """
        self.extension_id = extension_id
