# PoseVis

PoseVis is a multi-camera streaming and visualization framework built upon LabGraph. PoseVis was built with modularity in mind and can be extended to many downstream applications relatively easily through its extension system and logging support.

[Usage preview](https://i.imgur.com/FMYIy9r.mp4)

## Concepts

### Overview

PoseVis 

PoseVis streams any number of webcams, video files, or image directories and their generated extension data via the `CaptureResult` message (`pose_vis/streams/messages.py`). Included extensions are MediaPipe hand pose, face mesh, body pose, and holistic solutions for real-time pose tracking within LabGraph.

The stream is initialized by a corresponding `PoseVisRunner` class that takes care of graph initialization. The `PoseVis` graph is based off of the `DynamicGraph` class, which allows us to build a graph based on run-time parameters. You can connect `CaptureResult` subscribers to the `STREAM/OUTPUT` producer in the `PoseVis` graph (`pose_vis/pose_vis_graph.py`)

Each video source is handled in its own process within the `CaptureHandler` class. When a frame needs to be requested, the source processes are notified, grab a new frame, perform processing provided by enabled extensions, and put the result into a shared memory buffer. Once each source is finished, `CaptureHandler` compiles the `CaptureResult` message and publishes it. This keeps performance reasonable, and streams synchronized in time.

You may optionally enable a `Display` node that displays overlayed frames and performance statistics for real-time feedback.

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
python -m pose_vis.pose_vis --help
```

<details>
  <summary>Help Output</summary>
    
    usage: pose_vis.py [-h] [--sources [SOURCES ...]] [--resolutions [RESOLUTIONS ...]] [--replay REPLAY] [--display-framerate [DISPLAY_FRAMERATE]] [--stats-history-size [STATS_HISTORY_SIZE]] [--logging] [--log-dir [LOG_DIR]]
                    [--log-name LOG_NAME] [--profile] [--hands] [--face_detection] [--face_mesh]

    options:
    -h, --help            show this help message and exit
    --sources [SOURCES ...]
                            which sources to stream (url, device id, video, or image directory)
    --resolutions [RESOLUTIONS ...]
                            specify resolution/framerate per stream; format is <stream index or * for all>:<W>x<H>x<FPS> (default *:1280x720x30)
    --replay REPLAY       replay a log file (default: none)
    --display-framerate [DISPLAY_FRAMERATE]
                            specify update rate for video stream presentation; seperate from stream framerate (default: 60)
    --stats-history-size [STATS_HISTORY_SIZE]
                            how many frames to base performance metrics on, 0 to disable (default: 50)
    --logging             enable logging (default: false)
    --log-dir [LOG_DIR]   set log directory (default: webcam\logs)
    --log-name LOG_NAME   set log name (default: random)
    --profile             enable profiling with cProfile *source streaming only (default: false)
    --hands               enable the hand tracking extension
    --face_detection      enable the face detection extension
    --face_mesh           enable face mesh extension
    
</details>

<details>
  <summary>Console Usage Examples</summary>

Run device 0 with hand tracking:

    python -m pose_vis.pose_vis --sources 0 --hands

Enable HDF5 logging:

    python -m pose_vis.pose_vis --sources 0 --hands --logging --log-name example

Replay the log:

    python -m pose_vis.pose_vis --replay example

Specify resolutions:

    python -m pose_vis.pose_vis --sources 0 1 --resolutions 0:1280x720x30 1:1920x1080x30 --hands

</details>

### As a Module

See [this Jupyter Notebook example](https://github.com/Dasfaust/labgraph/blob/hand_tracking/devices/webcam/logging_example.ipynb) for PoseVis usage as a module.

## Reading Logs (HDF5)

For an example of logging output, check `logging_example.ipynb` [(link)](https://github.com/Dasfaust/labgraph/blob/hand_tracking/devices/webcam/logging_example.ipynb).

You can download the log generated in this example [here](https://drive.google.com/file/d/1cHRDBZ4MHOtYnL5K4VNRLouZmu9Ux0s4/view?usp=sharing).

## Data Quality

PoseVis performance can be tracked via the example in `benchmark.ipynb` [(link)](https://github.com/Dasfaust/labgraph/blob/hand_tracking/devices/webcam/benchmark.ipynb). This example runs a headless graph, captures process timings into a JSON file, and examines the output to produce metrics such as dropped frames, latency, desync between sources, and jitter.

Data quality may also be observed in real time by running PoseVis on the command line:

```
python -m pose_vis.pose_vis --sources 0 --display-framrate 60 --stats-history-size 50
```
