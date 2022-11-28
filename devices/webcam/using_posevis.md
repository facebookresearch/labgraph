# Using PoseVis

## Runners and Extensions

PoseVis has utility classes called "runners" that handle graph setup and configuration. `SourceStreamRunner` runs both online and offline sources, including GStreamer sources if supported. `ReplayStreamRunner` will replay HDF5 log files, and `BenchmarkRunner` runs configured benchmarks to generate a JSON file with frame timings.

Each runner requires a general PoseVis configuration class plus its own config. In this example, we'll configure `SourceStreamRunner` and connect to its topics with an example node.

```python
from pose_vis.runner import PoseVisConfig
from pose_vis.extensions.hands import HandsExtension
from pose_vis.runners.source_runner import SourceStreamRunnerConfig

config = PoseVisConfig(
    # Which extensions to enable. Extension types can be found in pose_vis/extensions
    extensions=[HandsExtension()],
    # Directory for saving logs (if enabled). This can be relative to the current working directory or a full path
    log_directory="./logs",
    # Name for the HDF5 log file. Specifying None creates a random name
    log_name=None,
    # Enables or disables logging to HDF5
    enable_logging=False,
    # How quickly to update the stream display windows. Specifying 0 disables this node. The display node calls cv2.imshow() for each stream and updates window titles appropriately
    display_framerate=0,
    # How many frames to keep track of for displaying performance characteristics. This is built in to the display node, so it's disabled when display_framerate is 0
    stats_history_size=0)

runner_config = SourceStreamRunnerConfig(
    # Sources dictate which streams to provide. The list can contain ints, which will stream a device via MSMF on Windows, and V4L2 on Linux
    # If provided a string that points to a file, PoseVis will consider it to be a video and attempt to load that and play it at the configured resolution and framerate
    # If provided a directory, PoseVis will look for images and stream those one-by-one at the configured framerate. See SUPPORTED_IMG_EXTENSIONS in pose_vis/streams/utils/capture_worker.py for a list of supported image formats
    # For both video and image directory sources, PoseVis will automatically terminate the graph when the source is finished playing
    # If provided a GStreamer string, PoseVis will use the GStreamer backend via OpenCV
    # Learn more about how PoseVis handles streams at readme.md#installation
    sources=[0],
    # Resolutions are represented via a list of tuples containing 3 ints, being width, height, and framerate. This must be specified per-stream, so the list should always be the same length as the sources list
    # For integer, GStreamer, and video file sources, width and height must be specified. If the input source does not match the specified resolution, it will be resized. For image directories, width and height are ignored and the image size is used
    # Each stream spawns a subprocess. PoseVis will attempt to keep streams synchronized in time by requesting new frames from each source at the same time and waiting until all sources present a frame before continuing. Because of this, it always run streams at the lowest configured framerate
    resolutions=[(1280, 720, 30)]
)
```

## LabGraph Topics

PoseVis's graph publishes a single topic containing the result every source stream and its extension results via the `CaptureResult` message:

```python
# pose_vis/streams/messages.py

@dataclass
class Capture():
    """
    Represents a single video frame

    Attributes:
        `frame`: `np.ndarray` video frame matrix, shape is (H, W, 3), RGB color space, short datatype
        `stream_id`: `int` source index for this capture
        `frame_index`: `int` total frames since startup
        `system_timestamp`: `float` `time.perf_counter()` value for when this frame was created
        `proc_delta_time`: `float` time in seconds this frame took to produce
        `proc_runtime`: `float` total runtime for this source
        `proc_fps`: `int` frames per second at the time this frame was produced
        `proc_target_fps`: `int` target frames per second for this source
    """
    frame: np.ndarray
    stream_id: int
    frame_index: int
    system_timestamp: float
    proc_delta_time: float
    proc_runtime: float
    proc_fps: int
    proc_target_fps: int

class CaptureResult(lg.Message):
    """
    Represents the current frame from every capture source

    Attributes:
        `captures`: `List[Capture]` `Capture`s by source index
        `extensions`: `List[Dict[str, Any]]` extension data by source index
    """
    captures: List[Capture]
    extensions: List[Dict[str, Any]]
```

Extension data varies by extension, but all extensions publish their respective MediaPipe results. Multiple extensions can be enabled at the same time, and each result is listed under the extension class name in the dictionary, so in our case we'd have a `HandsExtension` entry that contains the hand screen and world keypoints, plus handedness datastructure.

```python
message: CaptureResult ...
print(message.extensions[0]["HandsExtension"]["multi_hand_landmarks"])
```

## Running the Graph and Subscribing to Topics

Building on our earlier code, we can now subscribe to PoseVis's topic and run the graph. We'll just define a simple node to print the extension results and add it to the graph:


```python
import labgraph as lg
from pose_vis.pose_vis_graph import PoseVis
from pose_vis.streams.messages import CaptureResult
from pose_vis.runners.source_runner import SourceStreamRunner

# Define a simple node for subscribing to the CaptureResult topic
class ExampleSubscriber(lg.Node):
    INPUT = lg.Topic(CaptureResult)

    @lg.subscriber(INPUT)
    def on_message(self, message: CaptureResult) -> None:
        print(message.extensions)

# Create the SourceStreamRunner object with our config
runner = SourceStreamRunner(config, runner_config)
# Build the PoseVis graph
runner.build()

# Add our example node to the PoseVis graph
# This function adds a node with the name EXAMPLE_SUBSCRIBER and type ExampleSubscriber
# We then specify it should be connected to the STREAM's OUTPUT topic. All runners create a STREAM node with CaptureResult being in the OUTPUT topic slot
# We can also specify a lg.Config object to use, in this case we don't have one
PoseVis.add_node(name="EXAMPLE_SUBSCRIBER", _type=ExampleSubscriber, connection=["STREAM", "OUTPUT", "EXAMPLE_SUBSCRIBER", "INPUT"], config=None)

# Finally, we can run the graph
runner.run()
```

