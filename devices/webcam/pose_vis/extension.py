#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import numpy as np
import labgraph as lg

from pose_vis.video_stream import StreamMetaData
from abc import ABC, abstractmethod
from dataclasses import dataclass
from argparse import ArgumentParser, Namespace
from typing import Tuple, List, Union, Dict

@dataclass
class PoseVisConfiguration():
    """
    Utility dataclass for Pose Vis information

    Attributes:
        `num_devices`: `int`, the number of input streams being initialized
        `num_extensions`: `int`, the number of extensions each stream will run
        `args`: `Namespace` the variable produced by `ArgumentParer.parse_args()` during graph startup
    """
    num_devices: int
    num_extensions: int
    args: Namespace

@dataclass
class ExtensionResult():
    """
    Produced by `PoseVisExtension`

    Attributes:
        `data`: `Union[List, Dict, Tuple]`
    """
    data: Union[List, Dict, Tuple]

class CombinedExtensionResult(lg.Message):
    """
    All extension results combined into a dictionary and serialized to JSON
    
    Attributes:
    `results`: `str`

    Example output:
    ```
    {
        "HandsExtension":[
            [
                [
                    0.40868595242500305,
                    0.834717333316803,
                    -1.2446137986898975e-07
                ],
                ...
            ]
        ]
    }
    ```
    """
    results: str

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
        `config`: `PoseVisConfiguration`
    
    Methods:
        `set_enabled(self, extension_id: int, config: PoseVisConfiguration) -> None`
    """
    extension_id: int
    config: PoseVisConfiguration

    def set_enabled(self, extension_id: int, config: PoseVisConfiguration) -> None:
        """
        Called if this extension passes the `check_enabled` method
        """
        self.extension_id = extension_id
        self.config = config
