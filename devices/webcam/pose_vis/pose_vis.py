import labgraph as lg
import argparse as ap
import pose_vis.extensions

from pose_vis.dynamic_nodes import DynamicGraph
from pose_vis.camera_stream import SynchronizedCameraStream, SynchronizedCameraStreamConfig
from pose_vis.display import Display, DisplayConfig
from pose_vis.stream_combiner import VideoStreamCombiner, VideoStreamConbinerConfig
from pose_vis.extension import PoseVisExtension, PoseVisConfiguration
from typing import List, Tuple, DefaultDict

parser = ap.ArgumentParser()
parser.add_argument("--device-ids", type = int, nargs = "*", help = "which device ids to stream", action = "store", required = True)
parser.add_argument("--sample-rate", type = int, nargs = "?", const = 30, default = 30, help = "sample rate to poll all devices at (default 30)", action = "store", required = False)
parser.add_argument("--device-resolutions", type = str, nargs = "*", help = "specify resolution per device; format is <device_id or * for all>:<W>x<H> (default *:1280x720)", action = "store", required = False)
parser.add_argument("--synchronized", help = "allow strams", action = "store_false", required = False)

extensions: List[PoseVisExtension] = []

class PoseVis(DynamicGraph):
    pass

if __name__ == "__main__":
    for cls in PoseVisExtension.__subclasses__():
        extensions.append(cls())

    ext: PoseVisExtension
    for ext in extensions:
        ext.register_args(parser)

    args = parser.parse_args()

    device_resolutions: DefaultDict[int, Tuple[int, int]] = {}
    if args.device_resolutions:
        for i in range(len(args.device_resolutions)):
            colon_split = args.device_resolutions[i].split(":")
            x_split = colon_split[1].split("x")
            device_id = -1 if colon_split[0] == "*" else int(colon_split[0])
            device_resolution = (int(x_split[0]), int(x_split[1]))
            device_resolutions[device_id] = device_resolution
    if -1 not in device_resolutions:
        device_resolutions[-1] = (1280, 720)

    num_devices = len(args.device_ids)
    for i in range(num_devices):
        stream_name = f"STREAM{i}"
        input_name = f"INPUT{i}"
        device_id = args.device_ids[i]
        PoseVis.add_node(stream_name, SynchronizedCameraStream, [stream_name, "OUTPUT", "COMBINER", input_name],
            SynchronizedCameraStreamConfig(stream_id = i,
            device_id = device_id,
            device_resolution = device_resolutions[device_id] if device_id in device_resolutions else device_resolutions[-1]))
        PoseVis.add_connection(["DISPLAY", "OUTPUT", stream_name, "INPUT"])

    enabled_extensions: List[PoseVisExtension] = []
    for ext in extensions:
        if ext.check_enabled(args):
            enabled_extensions.append(ext)
    num_extensions = len(enabled_extensions)

    PoseVis.add_node("COMBINER", VideoStreamCombiner, ["COMBINER", "OUTPUT", "DISPLAY", "INPUT"], VideoStreamConbinerConfig(num_devices = num_devices, sample_rate = args.sample_rate))
    PoseVis.add_node("DISPLAY", Display, config = DisplayConfig(num_extensions = num_extensions, sample_rate = args.sample_rate, synchronized = args.synchronized))
    
    configuration = PoseVisConfiguration(num_devices = num_devices, num_extensions = num_extensions, args = args)
    for i in range(num_extensions):
        node_info = enabled_extensions[i].configure_node(i, configuration)
        ext_name = f"EXTENSION{i}"
        PoseVis.add_node(ext_name, node_info[0], ["COMBINER", "OUTPUT", ext_name, node_info[2].name], node_info[1])
        PoseVis.add_connection(["DISPLAY", f"EXTENSION_INPUT{i}", ext_name, node_info[3].name])

    graph = PoseVis()
    runner = lg.ParallelRunner(graph = graph)
    runner.run()