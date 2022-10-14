import labgraph as lg
import numpy as np

from pose_vis.logging import LoggingFormatBase
from pose_vis.video_stream import ProcessedVideoFrame
from pose_vis.extension import ExtensionResult
from typing import Optional

class LoggerConfig(lg.Config):
    log_images: bool
    log_poses: bool
    log_format: str

class LoggerState(lg.State):
    logger: Optional[LoggingFormatBase]

class Logger(lg.Node):
    INPUT_FRAMES = lg.Topic(ProcessedVideoFrame)
    INPUT_POSES = lg.Topic(ExtensionResult)
    config: LoggerConfig
    state: LoggerState

    def setup(self) -> None:
        if self.config.log_format == "hdf5":
            pass
        else:
            pass