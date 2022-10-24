# PoseVis

PoseVis is a multi-camera streaming and visualization framework built upon LabGraph. PoseVis was built with modularity in mind and can be extended to many downstream applications relatively easily through its extension system and logging support.

[Usage preview](https://i.imgur.com/FMYIy9r.mp4)

## Concepts

### Overview

PoseVis supports up to 4 video streams producing the `VideoFrame` message. There are a few differnt stream providers: `CameraStream` for device streaming, `ReplayStream` for log replaying, and `ImageStream` which reads images from a given directory.

These streams are initialized by a corresponding `PoseVisRunner` class that takes care of graph initialization. The `PoseVis` graph is based off of the `DynamicGraph` class, which allows us to build a graph based on run-time parameters.

Each stream provider enables and runs `PoseVisExtension` objects on their respective outputs and steams a `ExtensionResults` message, which is a dictionary containing each extension's name, and the data it produced. Extensions can be enabled or disabled by the user.

`CameraStreamRunner` and `ReplayStreamRunner` initialize a `Display` node that aggregates all streams and displays the overlayed frames for real-time feedback. `ImageStreamRunner` initializes a `TerminationHandler` node that shuts the graph down when processing is finished.

If logging is enabled, a `GraphMetaData` message is logged containing the stream count. Each stream's `VideoFrame` and `ExtensionResults` messages are logged under seperate groups.

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

You can download the log generated in this example [here](https://drive.google.com/file/d/1cHRDBZ4MHOtYnL5K4VNRLouZmu9Ux0s4/view?usp=sharing).