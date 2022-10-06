# Webcam Node and Real-time Hand Tracking Utility

## Webcam Stream Node
Provides stream of VideoFrame messages which contain a numpy array of an image from any connected webcam device. Uses CV2 to capture the video feed.

### Usage
Configuration:

    WebcamStreamConfig
        sample_rate: int
How many times per second to sample the device

        device_number: int

CV2 configuration, see [the documentation](https://docs.opencv.org/3.4/d8/dfe/classcv_1_1VideoCapture.html#a5d5f5dacb77bbebdcbfb341e3d4355c1) for more details

        device_resolution: np.ndarray

Expects a (2) shaped numpy array containing the dimensions of the desired output image

Topics:

    VideoFrame
        frame: np.ndarray

A (W, H, 3) shaped numpy array of the current video frame

        timestamp: float

The unix timestamp at which the frame was captured

## Hand Tracking Utility
Creates a graph that utilizes a [MediaPipe](https://google.github.io/mediapipe/) node to provide real-time hand pose estimation. It captures video data from a webcam using the included node, or optionally a log file, and presents a visual representation of the estimated hand poses, optionally logging the image data. Hand pose data may be optionally logged as well.

### Structure
The nodes of the graph are organized in this structure:

    WebcamStream -> PoseEstimation -> [Logging, Display]

### Usage

Run setup.py

    cd devices/webcam
    python setup.py install

Run Hand Tracking Utility

    python hand_tracking_utility.py

Press Esc to exit.

Hand Tracking Utility's functionality is flexible, see the command line arguments for details:

```
> python hand_tracking_utility.py --help

usage: hand_tracking_utility.py [-h] [-li] [-lp] [-lf {hdf5}] [-ld LOG_DIR] [-ln LOG_NAME] [-rp] [-dn DEVICE_NUMBER] [-sr SAMPLE_RATE] [-dr DEVICE_RESOLUTION DEVICE_RESOLUTION] [-ri] [-rr RESCALE_RESOLUTION RESCALE_RESOLUTION]

optional arguments:
  -h, --help            show this help message and exit
  -li, --log-images     add image data to logs
  -lp, --log-poses      add pose estimation data to logs
  -lf {hdf5}, --log-format {hdf5}
                        sepcify logging format. Supports hdf5, default is hdf5
  -ld LOG_DIR, --log-dir LOG_DIR
                        sepcify log directory, default is ./logs
  -ln LOG_NAME, --log-name LOG_NAME
                        sepcify log filename, default is hand_tracking_utility
  -rp, --replay         replay a log file
  -dn DEVICE_NUMBER, --device-number DEVICE_NUMBER
                        specify device number to capture from, default is 0
  -sr SAMPLE_RATE, --sample-rate SAMPLE_RATE
                        specify sample rate from device in Hz, default is 30
  -dr DEVICE_RESOLUTION DEVICE_RESOLUTION, --device-resolution DEVICE_RESOLUTION DEVICE_RESOLUTION
                        specify resolution for capture device, default is 854x480
  -ri, --rescale-image  enable rescaling display window from input size
  -rr RESCALE_RESOLUTION RESCALE_RESOLUTION, --rescale_resolution RESCALE_RESOLUTION RESCALE_RESOLUTION
                        specify resolution to rescale display stream to, default is 1280x720
```

### HDF5 Logging and Replaying
#### Logging
For example,

    python hand_tracking_utility.py -li

enables image logging in the HDF5 format. Images are laid out by their sequence number (n) like so:

    images/n/image

Images are numpy (W, H, 3) shaped arrays.

    python hand_tracking_utility.py -li -lp

Will log the pose estimation along with the image. You can log pose data by itself, if you wish. Pose data is laid out like this:

    images/n/hand_landmarks/h

where h is the hand index. The data is a (21, 3) shaped numpy array. See [MediaPipe's documentation](https://google.github.io/mediapipe/solutions/hands.html) for details on landmark identification. Each index in the array, the landmark id, has a set of normalized coordinates in the X, Y, and Z plane as an array, in that order.

Logs use the specified file name (or default) and are given an index "_n" based on how many files are in the log directory.

#### Replaying

An example of replaying a log file using the default arguments:

    python hand_tracking_utility.py -rp -ln hand_tracking_utility_0

Use the other arguments to specify the log directory, sample rate, etc. You could also optionally log the generated pose data to the same file with the -lp argument.