#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import re
import os
import labgraph as lg
import argparse as ap
import pose_vis.extensions

from pose_vis.dynamic_graph import DynamicGraph
from pose_vis.pose_vis_config import PoseVisMode, PoseVisConfiguration
from pose_vis.streams.camera_stream import CameraStream, CameraStreamConfig
from pose_vis.streams.graph_metadata import GraphMetaDataProvider, GraphMetaDataProviderConfig
from pose_vis.streams.image_stream import ImageStream, ImageStreamConfig
from pose_vis.streams.messages import GraphMetaData
from pose_vis.streams.replay_stream import ReplayStream, ReplayStreamConfig
from pose_vis.display import Display, DisplayConfig
from pose_vis.extension import PoseVisExtension
from pathlib import Path
from labgraph.loggers.hdf5.reader import HDF5Reader

logger = logging.getLogger(__name__)

# This is hard-coded to however many inputs the Display node has
MAX_STREAMS = 4

parser = ap.ArgumentParser()
parser.add_argument("--device-ids", type = int, nargs = "*", help = "which device ids to stream", action = "store", required = False)
parser.add_argument("--replay", type = str, help = "replay a log file (default: none)", action = "store", required = False)
parser.add_argument("--target-display-framerate", type = int, nargs = "?", const = 60, default = 60, help = "specify update rate for video stream presentation; seperate from stream framerate (default: 60)", action = "store", required = False)
parser.add_argument("--device-resolutions", type = str, nargs = "*", help = "specify resolution/framerate per device; format is <device_id or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)", action = "store", required = False)
parser.add_argument("--log-images", help = "enable image logging (default: false)", action = "store_true", required = False)
parser.add_argument("--log-poses", help = "enable pose data logging (default: false)", action = "store_true", required = False)
parser.add_argument("--log-dir", type = str, nargs = "?", const = "../logs", default = "../logs", help = "set log directory (default: ../logs)", action = "store", required = False)
parser.add_argument("--log-name", type = str, help = "set log name (default: random)", action = "store", required = False)

class PoseVis(DynamicGraph):
    """
    Create an instance of DynamicGraph. It is built with `PoseVisRunner`
    """
    pass

# TODO: the run function has gotten kind of monolithic
# It could be broken up into individual classes instead of an enum switch
class PoseVisRunner():
    """
    Builds the PoseVis graph and runs it based on the provided configuration

    Attributes:
        `config`: `PoseVisConfiguration` must be set when instantiating this class
    """
    config: PoseVisConfiguration

    def __init__(self, config: PoseVisConfiguration):
        self.config = config
    
    def run(self) -> None:
        logger.info(" building graph")

        for i in range(len(self.config.enabled_extensions)):
            ext: PoseVisExtension = self.config.enabled_extensions[i]
            logger.info(f" enabling extension: {ext.__class__.__name__}")
            ext.set_enabled(i, self.config)

        # Check if provided log path is a full directory or relative
        if not self.config.log_directory.startswith("/") or not re.match(r'[a-zA-Z]:', self.config.log_directory):
            self.config.log_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.config.log_directory)
        self.config.log_directory = self.config.log_directory.removesuffix("/").removesuffix("\\")
        Path(self.config.log_directory).mkdir(parents = True, exist_ok = True)

        if self.config.mode == PoseVisMode.DEVICE_STREAMING:
            num_devices = len(self.config.device_ids)
            logger.info(f" creating {num_devices} stream(s) with device ids {self.config.device_ids} and resolutions {self.config.device_resolutions}")

            PoseVis.add_node("METADATA", GraphMetaDataProvider, config = GraphMetaDataProviderConfig(num_streams = num_devices))

            for i in range(num_devices):
                stream_name = f"STREAM{i}"
                input_name = f"INPUT{i}"

                device_id = self.config.device_ids[i]
                device_resolution = self.config.device_resolutions[device_id] if device_id in self.config.device_resolutions else self.config.device_resolutions[-1]
                PoseVis.add_node(stream_name, CameraStream, [stream_name, "OUTPUT_FRAMES", "DISPLAY", input_name],
                    CameraStreamConfig(stream_id = i,
                    device_id = device_id,
                    device_resolution = device_resolution,
                    extensions = self.config.enabled_extensions))
                
                if self.config.log_images or self.config.log_poses:
                    PoseVis.add_logger_connection(("metadata", "METADATA", "OUTPUT"))

                    camera_log_name = f"image_stream_{i}"
                    extension_log_name = f"extension_stream_{i}"
                    if self.config.log_images:
                        PoseVis.add_logger_connection((camera_log_name, stream_name, "OUTPUT_FRAMES"))
                        logger.info(f" enabling image logging for stream {i} with the following path: {camera_log_name}")
                    if self.config.log_poses:
                        PoseVis.add_logger_connection((extension_log_name, stream_name, "OUTPUT_EXTENSIONS"))
                        logger.info(f" enabling pose data logging for stream {i} with the following path: {extension_log_name}")
                
                logger.info(f" created stream {i} with device id {device_id} and resolution {device_resolution}")
            
            PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(target_framerate = self.config.display_framerate, num_streams = num_devices))

        elif self.config.mode == PoseVisMode.IMAGE_STREAMING:
            if not self.config.image_streaming_directory.startswith("/") or not re.match(r'[a-zA-Z]:', self.config.image_streaming_directory):
                self.config.image_streaming_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.config.image_streaming_directory)
            self.config.image_streaming_directory = self.config.image_streaming_directory.removesuffix("/").removesuffix("\\")
            
            PoseVis.add_node("METADATA", GraphMetaDataProvider, config = GraphMetaDataProviderConfig(num_streams = 1))

            logger.info(" creating image stream")
            PoseVis.add_node("STREAM0", ImageStream,
                config = ImageStreamConfig(stream_id = i,
                directory = self.config.image_streaming_directory,
                target_framerate = self.config.image_streaming_framerate,
                extensions = self.config.enabled_extensions))
            
            if self.config.log_images or self.config.log_poses:
                PoseVis.add_logger_connection(("metadata", "METADATA", "OUTPUT"))

                camera_log_name = f"image_stream_{i}"
                extension_log_name = f"extension_stream_{i}"
                if self.config.log_images:
                    PoseVis.add_logger_connection((camera_log_name, "STREAM0", "OUTPUT_FRAMES"))
                    logger.info(f" enabling image logging for stream {i} with the following path: {camera_log_name}")
                if self.config.log_poses:
                    PoseVis.add_logger_connection((extension_log_name, "STREAM0", "OUTPUT_EXTENSIONS"))
                    logger.info(f" enabling pose data logging for stream {i} with the following path: {extension_log_name}")
        elif self.config.mode == PoseVisMode.LOG_REPLAY:
            log_types = {"metadata": GraphMetaData}
            reader = HDF5Reader(self.config.replay_path, log_types)
            logger.info(f" reading log metadata: {self.config.replay_path}")
            num_streams = reader.logs["metadata"][0].num_streams
            
            for i in range(num_streams):
                stream_name = f"STREAM{i}"
                input_name = f"INPUT{i}"

                PoseVis.add_node(stream_name, ReplayStream, [stream_name, "OUTPUT_FRAMES", "DISPLAY", input_name],
                ReplayStreamConfig(stream_id = i,
                    extensions = self.config.enabled_extensions,
                    log_path = self.config.replay_path))
                logger.info(f" created log replay stream {i}")
                
                if self.config.log_images or self.config.log_poses:
                    camera_log_name = f"image_stream_{i}"
                    extension_log_name = f"extension_stream_{i}"
                    if self.config.log_images:
                        PoseVis.add_logger_connection((camera_log_name, stream_name, "OUTPUT_FRAMES"))
                        logger.info(f" enabling image logging for stream {i} with the following path: {camera_log_name}")
                    if self.config.log_poses:
                        PoseVis.add_logger_connection((extension_log_name, stream_name, "OUTPUT_EXTENSIONS"))
                        logger.info(f" enabling pose data logging for stream {i} with the following path: {extension_log_name}")
            
            PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(target_framerate = self.config.display_framerate, num_streams = num_streams))

        logger_config: lg.LoggerConfig
        if self.config.log_name:
            logger_config = lg.LoggerConfig(output_directory = self.config.log_directory, recording_name = self.config.log_name)
        else:
            logger_config = lg.LoggerConfig(output_directory = self.config.log_directory)

        logger.info(" running graph")
        graph = PoseVis()
        runner_options = lg.RunnerOptions(logger_config = logger_config)
        runner = lg.ParallelRunner(graph = graph, options = runner_options)
        runner.run()

if __name__ == "__main__":
    """
    Run the graph via command line arguments
    """

    # Get a list of every available extension
    extensions = []
    for cls in PoseVisExtension.__subclasses__():
        extensions.append(cls())

    # Let extensions register arguments
    ext: PoseVisExtension
    for ext in extensions:
        ext.register_args(parser)

    args = parser.parse_args()

    if args.device_ids is None and args.replay is None:
        raise ValueError("Please specify either device IDs to stream or a log to replay")

    enabled_extensions = []
    # Check if an extension is enabled via its argument
    for ext in extensions:
        if ext.check_enabled(args):
            enabled_extensions.append(ext)

    if args.replay is None:
        device_resolutions = {}

        # Make sure we don't register too many streams
        num_devices = len(args.device_ids)
        if num_devices > MAX_STREAMS:
            num_devices = MAX_STREAMS
            logger.warning(f" too many streams, initializing only the first {MAX_STREAMS} provided streams")
            args.device_ids = args.device_ids[0:4]

        # Convert 'ID:WxHxFPS' string into a dictionary with a tuple entry: {ID: (W, H, FPS)}
        # Default values are placed in the -1 slot
        if args.device_resolutions:
            for i in range(len(args.device_resolutions)):
                colon_split = args.device_resolutions[i].split(":")
                x_split = colon_split[1].split("x")
                device_id = -1 if colon_split[0] == "*" else int(colon_split[0])
                device_resolution = (int(x_split[0]), int(x_split[1]), int(x_split[2]))
                device_resolutions[device_id] = device_resolution
        if -1 not in device_resolutions:
            device_resolutions[-1] = (1280, 720, 30)
        
        # Build and run the graph
        config = PoseVisConfiguration(mode = PoseVisMode.DEVICE_STREAMING,
            enabled_extensions = enabled_extensions,
            device_ids = args.device_ids,
            device_resolutions = device_resolutions,
            display_framerate = args.target_display_framerate,
            log_directory = args.log_dir,
            log_name = args.log_name,
            log_images = args.log_images,
            log_poses = args.log_images,
            image_streaming_directory = "",
            image_streaming_framerate = 0,
            replay_path = "")
        PoseVisRunner(config).run()
    else:
        # Initiate log replay

        # If the log path is relative join it with the working directory
        if not args.replay.startswith("/") or not re.match(r'[a-zA-Z]:', args.replay):
            args.replay = os.path.join(os.path.dirname(os.path.realpath(__file__)), args.replay)

        # Build and run the graph
        config = PoseVisConfiguration(mode = PoseVisMode.LOG_REPLAY,
            enabled_extensions = enabled_extensions,
            device_ids = [],
            device_resolutions = {},
            display_framerate = args.target_display_framerate,
            replay_path = args.replay,
            log_directory = args.log_dir,
            log_name = args.log_name,
            log_images = args.log_images,
            log_poses = args.log_images,
            image_streaming_directory = "",
            image_streaming_framerate = 0)
        PoseVisRunner(config).run()
            