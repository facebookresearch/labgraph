#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import argparse as ap
import pose_vis.extensions

from pose_vis.extension import PoseVisExtension
from pose_vis.runner import PoseVisConfig
from pose_vis.runners.camera_runner import CameraStreamRunner, CameraStreamRunnerConfig
from pose_vis.runners.replay_runner import ReplayStreamRunner, ReplayStreamRunnerConfig

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
parser.add_argument("--log-dir", type = str, nargs = "?", const = "webcam/logs", default = "webcam/logs", help = "set log directory (default: webcam/logs)", action = "store", required = False)
parser.add_argument("--log-name", type = str, help = "set log name (default: random)", action = "store", required = False)

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

    config = PoseVisConfig(extensions = enabled_extensions,
        log_directory = args.log_dir,
        log_name = args.log_name,
        log_images = args.log_images,
        log_poses = args.log_images)

    if args.replay is None:
        # Initiate camera streaming
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
        runner_config = CameraStreamRunnerConfig(device_ids = args.device_ids,
            device_resolutions = device_resolutions,
            display_framerate = args.target_display_framerate)
        runner = CameraStreamRunner(config, runner_config)
        runner.build()
        runner.run()
    else:
        # Initiate log replay
        # Build and run the graph
        runner_config = ReplayStreamRunnerConfig(path = args.replay,
            display_framerate = args.target_display_framerate)
        runner = ReplayStreamRunner(config, runner_config)
        runner.build()
        runner.run()
            