# PoseVis

PoseVis is a LabGraph extension that streams any number of video sources and generates pose landmark data from [MediaPipe](https://google.github.io/mediapipe/) for each stream independently. MediaPipe [Hands](https://google.github.io/mediapipe/solutions/hands.html), [Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html), [Pose](https://google.github.io/mediapipe/solutions/pose.html), and [Holistic](https://google.github.io/mediapipe/solutions/holistic.html) solutions are supported. PoseVis supports data logging and replaying via the [HDF5](https://www.hdfgroup.org/solutions/hdf5/) format. See [Using PoseVis](#using-posevis) for details.

[Usage preview](https://i.imgur.com/FMYIy9r.mp4)

PoseVis can also support other image processing tasks through its extension system. Take a look at the [hands extension](pose_vis/extensions/hands.py) for an example.

# Installation

PoseVis uses [OpenCV](https://opencv.org/) to handle video streams. Out of the box, PoseVis streams camera, video file, and image directory sources from the `MSMF` backend in Windows, and `V4L2` backend in Linux, with the MJPEG format ([see OpenCV backends here](https://docs.opencv.org/3.4/d0/da7/videoio_overview.html)). This configuration should be supported by most [UVC](https://en.wikipedia.org/wiki/USB_video_device_class) devices. Further source stream customization can be achieved by installing [GStreamer](https://gstreamer.freedesktop.org/); steps are detailed below.

## PoseVis General Setup

Requires Python 3.8 or later. Assuming an installation in your user directory, run `setup.py` to install required packages from PyPi:

Linux:

    cd ~/labgraph/webcam
	python3 setup.py install

Windows:

    cd %HOMEPATH%/labgraph/webcam
    python setup.py install

See [Using PoseVis](#using-posevis) for usage details.

## GStreamer Support (Optional)

[GStreamer](https://gstreamer.freedesktop.org/) is a multimedia framework that allows you to create your own media pipelines with a simple string input. If you need more flexibility than a simple MJPEG stream, you can install GStreamer using the steps below.

### Example GStreamer Configurations

PoseVis expects color formats from GStreamer to be in the `BGR` color space, and OpenCV requires the use of [appsink](https://gstreamer.freedesktop.org/documentation/app/appsink.html?gi-language=c).

Creating a test source: this configuration creates the [videotestsrc](https://gstreamer.freedesktop.org/documentation/videotestsrc/index.html?gi-language=c) element and configures a 720p @ 30Hz stream in BGR.

    python -m pose_vis.pose_vis --sources "videotestsrc ! video/x-raw, width=1280, height=720, framerate=30/1, format=BGR ! appsink"

Creating a device source in Linux: this configuration captures an MJPEG stream at 720p @ 30Hz from a [V4L2 device](https://gstreamer.freedesktop.org/documentation/video4linux2/v4l2src.html?gi-language=c) and [converts](https://gstreamer.freedesktop.org/documentation/videoconvertscale/videoconvert.html?gi-language=c) the image format into raw BGR.

    python -m pose_vis.pose_vis --sources "v4l2src device=/dev/video0 ! image/jpeg, width=1280, height=720, framerate=30/1 ! jpegparse ! jpegdec ! videoconvert ! video/x-raw, format=BGR ! appsink"

You can also specify [per-camera configurations](https://gstreamer.freedesktop.org/documentation/video4linux2/v4l2src.html?gi-language=c#v4l2src:extra-controls):

    ... --sources "v4l2src device=/dev/video0 extra-controls='c, exposure_auto=1' ...

### Windows GStreamer Support

Follow the [Windows GStreamer guide](windows_gstreamer.md).

### Linux GStreamer Support

Follow the [Linux GStreamer guide](linux_gstreamer.md).

## Performance

Performance is crucial for real time applications. Check the [benchmark notebook](benchmark.ipynb) example for performance metrics, including details of the system used for benchmarking. You can also run the notebook on your system to get an idea of how PoseVis will perform.

## Using PoseVis

### Test PoseVis via Command Line

Check usage details:

	python -m pose_vis.pose_vis --help

### Using PoseVis in Your Project

Check the [usage guide](using_posevis.md) for an in-depth overview of the concepts used in PoseVis and how to hook into its LabGraph topics.

### PoseVis Usage Examples

#### GestureVis

GestureVis uses data from the MediaPipe hand and body pose extensions to guess the current gesture based on a list of known gestures and draws the appropriate annotations onto the video stream, both online and offline. Check out the hands version [here](pose_vis/gesture/hand/readme.md).

#### Logging Example

The [logging example](logging_example.ipynb) notebook shows a simple way to use HDF5 logging with PoseVis.
