# Pose Vis

Pose Vis is a real-time multi-camera streaming and visualization framework built upon LabGraph. Pose Vis was built with modularity in mind and can be extended to many downstream applications relatively easily through its extension system and logs.

## Concepts

### Overview

The `PoseVis` graph is initialized with up to 4 video streams, provided by `CameraStream`. Each `CameraStream` instance initializes enabled extensions (`PoseVisExtension` class). Image data is processed within each `CameraStream` process, and then sent to the `Display` node, for real-time visual feedback.

We initially intended to initialize extensions as their own nodes (and therefore processes) but ran into issues synchronizing the entire graph at an acceptable framerate.

### Streams

Note that video data streams and LabGraph stream terms are used here interchangably.

`CameraStream` has two output streams: `ProcessedVideoFrame` and `CombinedExtensionResult`

```python
@dataclass
class StreamMetaData:
    """
    Utility dataclass for information of a particular stream input

    Attributes:
        `target_framerate`: `int`, the target framerate of this source
        `actual_franerare`: `int`, the actual framerate of this source
        `device_id`: `int`, the device identifier, e.g. `/dev/video{n} on Linux`. `-1` for non-device based streams
        `stream_id`: `int`, the contiguous index of this stream
    """
    target_framerate: int
    actual_framerate: int
    device_id: int
    stream_id: int

class ProcessedVideoFrame(lg.Message):
    """
    Each `np.ndarray` instance is a (H, W, 3) shaped array containing `np.uint8` datatype that represents an image
    Image formats are in the Blue Green Red color space

    Attributes:
        `original`: `np.ndarray` the original input frame
        `overlayed`: `np.ndarray` the original frame combined with overlays produced by each extension
        `frame_index`: `int`, frame counter since startup
        `metadata`: `StreamMetaData`
    """
    original: np.ndarray
    overlayed: np.ndarray
    frame_index: int
    metadata: StreamMetaData
```

### Extensions



### Display

`Display`'s job is simple, to aggregate all input streams and present the processed video frames in an organized manor, with some performance telemetry. Only one instance extists per graph.

### Logging

## Usage

## To-do

### Testing

A testing solution needs to be implemented, this is a regression from the previous proposal for this pull request.

### Other MediaPipe Solutions

Hand tracking is currently included, with other solutions on the way. MediaPipe Python supports hand tracking, pose tracking, and face mesh tracking. These solutions can be combined into the [holistic](https://google.github.io/mediapipe/solutions/holistic.html) graph. The plan is to implement them seperately along with the holistic solution for modularity.

Other MediaPipe solutions will require C++ interop.

### Jupyter Notebook Integration

We intend to provide, at the very least, an example for loading and displaying logged data inside of a Jupyter Notebook.

## Other Thoughts

### MediaPipe Performance

Currently, the hand tracking (and subsequent other) MediaPipe extensions run their neural networks on the CPU. A significant performance uplift could be achieved by running GPU-enabled MediaPipe graphs. It seems that MediaPipe's python wrapper does not have GPU capabilities: see [this issue](https://github.com/google/mediapipe/issues/3106). We could create our own wrappers around a C++ MediaPipe implementation using LabGraph's interop to achieve this.

### n-Stream Support

Pose Vis is hard coded to support 4 streams simultaneously. This limitation could be avoided with a method to change node metadata (inputs and outputs) before graph startup. This idea has proven tricky to implement due to the multi-process nature of LabGraph, but it should be possible.