from abc import ABC
import numpy as np

from pose_vis.video_stream import ProcessedVideoFrame
from pose_vis.extension import ExtensionResult
from abc import ABC, abstractmethod

class LoggingFormatBase(ABC):

    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def log_image(self, message: ProcessedVideoFrame) -> None:
        pass

    @abstractmethod
    def log_poses(self, message: ExtensionResult) -> None:
        pass
