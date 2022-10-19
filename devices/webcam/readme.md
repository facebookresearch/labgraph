# PoseVis

PoseVis is a multi-camera streaming and visualization framework built upon LabGraph. PoseVis was built with modularity in mind and can be extended to many downstream applications relatively easily through its extension system and logging support.

![Usage preview](https://raw.githubusercontent.com/Dasfaust/labgraph/hand_tracking/devices/webcam/images/preview.gif)

## Concepts

### Overview

PoseVis supports up to 4 video streams producing the `ProcessedVideoFrame` message. There are a few differnt stream providers: `CameraStream` for device streaming, `ReplayStream` for log replaying, and `ImageStream` which reads images from a given directory.

These streams are initialized by a corresponding `PoseVisRunner` class that takes care of graph initialization. The `PoseVis` graph is based off of the `DynamicGraph` class, which allows us to build a graph based on run-time parameters.

Each stream provider enables and runs `PoseVisExtension` objects on their respective outputs and steams a `CombinedExtensionResult` message, which is a dictionary containing each extension's name, and the data it produced. Extensions can be enabled or disabled by the user. `ProcessedVideoFrame` has the original image, and an overlayed image containing any processing done by extensions (i.e a pose overlay).

`CameraStreamRunner` and `ReplayStreamRunner` initialize a `Display` node that aggregates all streams and displays the overlayed image for real-time feedback. `ImageStreamRunner` initializes a `TerminationHandler` node that shuts the graph down when processing is finished.

If logging is enabled, a `GraphMetaData` message is logged containing the stream count. Each stream's `ProcessedVideoFrame` and `CombinedExtensionResult` messages are logged under seperate groups.

## Usage

Requires Python 3.8 or later

Make sure to install:

```
cd devices/webcam
python setup.py install
```

### Command Line

Check usage details:

```
(.venv) python -m pose_vis.pose_vis --help               
usage: pose_vis.py [-h] [--device-ids [DEVICE_IDS ...]] [--replay REPLAY] [--replay-overlays] [--target-display-framerate [TARGET_DISPLAY_FRAMERATE]] [--device-resolutions [DEVICE_RESOLUTIONS ...]]
                   [--log-images] [--log-poses] [--log-dir [LOG_DIR]] [--log-name LOG_NAME] [--hands] [--face]

optional arguments:
  -h, --help            show this help message and exit
  --device-ids [DEVICE_IDS ...]
                        which device ids to stream
  --replay REPLAY       replay a log file (default: none)
  --replay-overlays     show previously generated overlays during replay (default: false)
  --target-display-framerate [TARGET_DISPLAY_FRAMERATE]
                        specify update rate for video stream presentation; seperate from stream framerate (default: 60)
  --device-resolutions [DEVICE_RESOLUTIONS ...]
                        specify resolution/framerate per device; format is <device_id or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)
  --log-images          enable image logging (default: false)
  --log-poses           enable pose data logging (default: false)
  --log-dir [LOG_DIR]   set log directory (default: webcam/logs)
  --log-name LOG_NAME   set log name (default: random)
  --hands               enable the hand tracking extension
  --face                enable the face detection extention
```

Streaming a single device: stream device 0 with no extensions or logging

`python -m pose_vis.pose_vis --device-ids 0`

Streaming multiple devices: stream devices 0 and 1 with no extensions or logging

`python -m pose_vis.pose_vis --device-ids 0 1`

Specifying resolution and framerate:

The format for specifying resolution is `<device id>:<width>x<height>x<framerate>`

You can also set the default resolution and framerate by using `*` in place of `<device id>`

`python -m pose_vis.pose_vis --device-ids 0 1 --device-resolutions 1:640x480x30`

Enabling extensions: this enables the hand tracking extension

`python -m pose_vis.pose_vis --device-ids 0 1 --device-resolutions 1:640x480x30 --hands`

Enabling logging: this enables both image and pose data logging

`python -m pose_vis.pose_vis --device-ids 0 1 --device-resolutions 1:640x480x30 --hands --log-images --log-poses`

Replaying logs: this will replay a log and stream the generated pose data (if present)

`python -m pose_vis.pose_vis --replay webcam/logs/test_log.h5`

You can also enable extensions and logging to generate a new log with new extension data based on the images in the log being replayed:

`python -m pose_vis.pose_vis --replay webcam/logs/test_log.h5 --hands --log-images --log-poses`

### As a Module

See [this Jupyter Notebook example](https://github.com/Dasfaust/labgraph/blob/hand_tracking/devices/webcam/logging_example.ipynb) for PoseVis usage as a module.

## Reading Logs (HDF5)

For an example of logging output, check [this Jupyter Notebook example](https://github.com/Dasfaust/labgraph/blob/hand_tracking/devices/webcam/logging_example.ipynb).

## To-do

### Testing

A testing solution needs to be implemented, this is a regression from the previous proposal for this pull request.

### VRS Support

VRS support for logging needs to be added.

### Other MediaPipe Solutions

Hand tracking is currently included, with other solutions on the way. MediaPipe Python supports hand tracking, pose tracking, and face mesh tracking. These solutions can be combined into the [holistic](https://google.github.io/mediapipe/solutions/holistic.html) graph. The plan is to implement them seperately along with the holistic solution for modularity.

Other MediaPipe solutions will require C++ interop.

## Other Thoughts

### MediaPipe Performance

Currently, the hand tracking (and subsequent other) MediaPipe extensions run their neural networks on the CPU. A significant performance uplift could be achieved by running GPU-enabled MediaPipe graphs. It seems that MediaPipe's Python wrapper does not have GPU capabilities: see [this issue](https://github.com/google/mediapipe/issues/3106). We could use C++ interop to achieve this.

### n-Stream Support

Pose Vis is hard coded to support 4 streams simultaneously. This limitation could be avoided with a method to change node metadata (inputs and outputs) before graph startup. This idea has proven tricky to implement due to the multi-process nature of LabGraph, but it should be possible.

### Multi-media Support

CV2 can be used to import a wide variety of media including videos and gifs. We could create more stream types to support this.
