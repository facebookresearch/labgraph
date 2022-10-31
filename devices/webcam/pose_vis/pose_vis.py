#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

# Windows-specific performance tuning
import os

if os.name == "nt":
    # Improve device capture startup time on Windows
    # https://github.com/opencv/opencv/issues/17687
    os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import cProfile
import pstats
import logging
import argparse as ap
import pose_vis.extensions

from pose_vis.extension import PoseVisExtension
from pose_vis.utils import absolute_path
from pose_vis.runner import PoseVisConfig
from pose_vis.runners.source_runner import SourceStreamRunner, SourceStreamRunnerConfig
from pose_vis.runners.replay_runner import ReplayStreamRunner, ReplayStreamRunnerConfig

logger = logging.getLogger(__name__)

parser = ap.ArgumentParser()
parser.add_argument("--sources", type = str, nargs = "*", help = "which sources to stream (url, device id, video, or image directory)", action = "store", required = False)
parser.add_argument("--resolutions", type = str, nargs = "*", help = "specify resolution/framerate per stream; format is <stream index or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)", action = "store", required = False)
parser.add_argument("--replay", type = str, help = "replay a log file (default: none)", action = "store", required = False)
parser.add_argument("--display-framerate", type = int, nargs = "?", const = 60, default = 60, help = "specify update rate for video stream presentation; seperate from stream framerate (default: 60)", action = "store", required = False)
parser.add_argument("--stats-history-size", type = int, nargs = "?", const = 50, default = 50, help = "how many frames to base performance metrics on, 0 to disable (default: 50)", action = "store", required = False)
parser.add_argument("--logging", help = "enable logging (default: false)", action = "store_true", required = False)
default_dir = f"webcam{os.sep}logs"
parser.add_argument("--log-dir", type = str, nargs = "?", const = default_dir, default = default_dir, help = f"set log directory (default: {default_dir})", action = "store", required = False)
parser.add_argument("--log-name", type = str, help = "set log name (default: random)", action = "store", required = False)
parser.add_argument("--profile", help = "enable profiling with cProfile *source streaming only (default: false)", action = "store_true", required = False)

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

    if args.sources is None and args.replay is None:
        raise ValueError("Please specify sources to stream or a log to replay")

    enabled_extensions = []
    # Check if an extension is enabled via its argument
    for ext in extensions:
        if ext.check_enabled(args):
            enabled_extensions.append(ext)

    config = PoseVisConfig(extensions = enabled_extensions,
        log_directory = args.log_dir,
        log_name = args.log_name,
        enable_logging = args.logging,
        display_framerate = args.display_framerate,
        stats_history_size = args.stats_history_size)

    if args.replay is None:
        # Initiate camera streaming
        sources = []
        for arg in args.sources:
            if arg.isdigit():
                sources.append(int(arg))
            else:
                sources.append(absolute_path(arg))

        # Convert 'ID:WxHxFPS' strings into List[Tuple[int, int, int]]
        default_res = None
        resolutions = [None] * len(sources)
        if args.resolutions:
            for i in range(len(args.resolutions)):
                colon_split = args.resolutions[i].split(":")
                x_split = colon_split[1].split("x")
                stream_id = -1 if colon_split[0] == "*" else int(colon_split[0])
                resolution = (int(x_split[0]), int(x_split[1]), int(x_split[2]))
                if stream_id > -1:
                    resolutions[stream_id] = resolution
                else:
                    default_res = resolution
        if default_res is None:
            default_res = (1280, 720, 30)
        for i in range(len(resolutions)):
            if resolutions[i] is None:
                resolutions[i] = default_res

        # Build and run the graph
        runner_config = SourceStreamRunnerConfig(
            sources = sources,
            resolutions = resolutions)
        runner = SourceStreamRunner(config, runner_config)
        runner.build()

        if args.profile:
            with cProfile.Profile() as pr:
                runner.run()
            stats = pstats.Stats(pr)
            stats.dump_stats(filename = "pose_vis.prof")
            logger.info(" saved 'pose_vis.prof' in the current working directory")
        else:
            runner.run()
    else:
        # Initiate log replay
        # Build and run the graph
        runner_config = ReplayStreamRunnerConfig(args.replay)
        runner = ReplayStreamRunner(config, runner_config)
        runner.build()
        runner.run()