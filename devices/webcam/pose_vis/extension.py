import labgraph as lg

from abc import ABC, abstractmethod
from dataclasses import dataclass
from argparse import ArgumentParser, Namespace
from typing import List, Any, Tuple

@dataclass
class PoseVisConfiguration():
    num_devices: int
    num_extensions: int
    args: Namespace

@dataclass
class ResultData():
    frame_index: int
    data: Any

class ExtensionResult(lg.Message):
    extension_id: int
    update_time_ms: int
    result_frames: List[lg.NumpyDynamicType]
    result_data: List[ResultData]

class PoseVisExtension(ABC):

    @abstractmethod
    def register_args(self, parser: ArgumentParser):
        pass

    @abstractmethod
    def check_enabled(self, args: Namespace) -> bool:
        pass

    @abstractmethod
    def configure_node(self, extension_id: int, config: PoseVisConfiguration) -> Tuple[type, lg.Config, lg.Topic, lg.Topic]:
        pass