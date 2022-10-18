#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import re
import os
import labgraph as lg
import argparse as ap
import pose_vis.extensions

from pathlib import Path
from pose_vis.dynamic_nodes import DynamicGraph
from pose_vis.camera_stream import CameraStream, CameraStreamConfig
from pose_vis.display import Display, DisplayConfig
from pose_vis.extension import PoseVisExtension, PoseVisConfiguration
from typing import List, Tuple, DefaultDict

# This is hard-coded to however many inputs the Display node has
MAX_STREAMS = 4

parser = ap.ArgumentParser()
parser.add_argument("--device-ids", type = int, nargs = "*", help = "which device ids to stream", action = "store", required = True)
parser.add_argument("--target-display-framerate", type = int, nargs = "?", const = 60, default = 60, help = "specify update rate for video stream presentation; seperate from stream framerate (default: 60)", action = "store", required = False)
parser.add_argument("--device-resolutions", type = str, nargs = "*", help = "specify resolution/framerate per device; format is <device_id or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)", action = "store", required = False)
parser.add_argument("--log-images", help = "enable image logging (default: false)", action = "store_true", required = False)
parser.add_argument("--log-poses", help = "enable pose data logging (default: false)", action = "store_true", required = False)
parser.add_argument("--log-dir", type = str, nargs = "?", const = "../logs", default = "../logs", help = "set log directory (default: ../logs)", action = "store", required = False)
parser.add_argument("--log-name", type = str, help = "set log name (default: random)", action = "store", required = False)

extensions: List[PoseVisExtension] = []

class PoseVis(DynamicGraph):
    pass

if __name__ == "__main__":
    for cls in PoseVisExtension.__subclasses__():
        extensions.append(cls())

    print("PoseVis: building graph")

    ext: PoseVisExtension
    for ext in extensions:
        ext.register_args(parser)

    args = parser.parse_args()

    enabled_extensions: List[PoseVisExtension] = []
    for ext in extensions:
        if ext.check_enabled(args):
            print(f"PoseVis: enabling extension: {ext.__class__.__name__}")
            enabled_extensions.append(ext)
    num_extensions = len(enabled_extensions)

    num_devices = len(args.device_ids)
    if num_devices > MAX_STREAMS:
        num_devices = MAX_STREAMS
        print(f"PoseVis: warning: too many streams, initializing only the first {MAX_STREAMS} provided streams")
    
    config = PoseVisConfiguration(num_devices = num_devices, num_extensions = num_extensions, args = args)
    for i in range(num_extensions):
        ext.set_enabled(i, config)

    device_resolutions: DefaultDict[int, Tuple[int, int, int]] = {}
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

    print(f"PoseVis: creating {num_devices} stream(s) with device ids {args.device_ids} and resolutions {device_resolutions}")

    for i in range(num_devices):
        stream_name = f"STREAM{i}"
        input_name = f"INPUT{i}"
        device_id = args.device_ids[i]
        device_resolution = device_resolutions[device_id] if device_id in device_resolutions else device_resolutions[-1]
        PoseVis.add_node(stream_name, CameraStream, [stream_name, "OUTPUT_FRAMES", "DISPLAY", input_name],
            CameraStreamConfig(stream_id = i,
            device_id = device_id,
            device_resolution = device_resolution,
            extensions = enabled_extensions))
        if args.log_images or args.log_poses:
            camera_log_name = f"camera_stream_{i}"
            extension_log_name = f"extension_stream_{i}"
            if args.log_images:
                PoseVis.add_logger_connection((camera_log_name, stream_name, "OUTPUT_FRAMES"))
                print(f"PoseVis: enabling image logging for stream {i} with the following path: {camera_log_name}")
            if args.log_poses:
                PoseVis.add_logger_connection((extension_log_name, stream_name, "OUTPUT_EXTENSIONS"))
                print(f"PoseVis: enabling pose data logging for stream {i} with the following path: {extension_log_name}")
        print(f"PoseVis: created stream {i} with device id {args.device_ids[i]} and resolution {device_resolution}")
    
    PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(target_framerate = args.target_display_framerate, num_streams = num_devices))

    log_path = ""
    # Check if provided log path is a full directory or relative
    if args.log_dir.startswith("/") or re.match(r'[a-zA-Z]:', args.log_dir):
        log_path = args.log_dir
    else:
        log_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), args.log_dir)
    log_path = log_path.removesuffix("/").removesuffix("\\")
    Path(log_path).mkdir(parents = True, exist_ok = True)

    logger_config: lg.LoggerConfig
    if args.log_name:
        logger_config = lg.LoggerConfig(output_directory = log_path, recording_name = args.log_name)
    else:
        logger_config = lg.LoggerConfig(output_directory = log_path)

    print("PoseVis: running graph")
    graph = PoseVis()
    runner_options = lg.RunnerOptions(logger_config = logger_config)
    runner = lg.ParallelRunner(graph = graph, options = runner_options)
    runner.run()