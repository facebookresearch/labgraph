# Linux GStreamer Guide

In this guide we will install GStreamer and build OpenCV with GStreamer support. This guide uses a fresh install of Ubuntu 20.04.

## Build OpenCV

Create a virtual environment for use with PoseVis:

    sudo apt install python3.8-venv -y && python3 -m venv .venv && source .venv/bin/activate

Install Numpy:

    python -m pip install numpy

Install GStreamer:

    sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-gl gstreamer1.0-gtk3 -y

Install required OpenCV libraries:

    sudo apt install cmake libgtk-3-dev python3-dev -y

We'll be building and installing OpenCV and OpenCV Contrib 4.6.0. Clone the branches:

    sudo apt install git && git clone -b 4.6.0 --single-branch https://github.com/opencv/opencv.git && git clone -b 4.6.0 --single-branch https://github.com/opencv/opencv_contrib.git

Create a build directory for OpenCV and `cd` into it:

    mkdir opencv/build && cd opencv/build

Run CMake with the following config:

    cmake ../ \
    -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
    -D PYTHON_DEFAULT_EXECUTABLE=$(which python3) \
    -D BUILD_EXAMPLES=OFF \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D BUILD_opencv_python2=OFF \
    -D PYTHON3_INCLUDE_DIR=$(python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
    -D PYTHON3_PACKAGES_PATH=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
    -D PYTHON_LIBRARY=$(python -c "from distutils.sysconfig import get_config_var; from os.path import dirname, join; print(join(dirname(get_config_var('LIBPC')), get_config_var('LDLIBRARY')))") \
    -D BUILD_opencv_python3=ON

Check GTK, V4L2, GStreamer, and Python3 status:

    --   GUI:                           GTK3
    --     GTK+:                        YES (ver 3.24.33)

    ...

    --   Video I/O:
    --     GStreamer:                   YES (1.20.3)
    --     v4l/v4l2:                    YES (linux/videodev2.h)
    
    ...

    --   Python 3:
    --     Interpreter:                 /home/cody/.venv/bin/python3 (ver 3.8.15)
    --     Libraries:                   /usr/lib/x86_64-linux-gnu/libpython3.8.so (ver 3.8.15)
    --     numpy:                       /home/cody/.venv/lib/python3.8/site-packages/numpy/core/include (ver 1.23.4)
    --     install path:                /home/cody/.venv/lib/python3.8/site-packages/cv2/python-3.8

If everything looks good, build and install:

    make -j$(nproc) && sudo make install

Fix CV2 Python package permissions: **replace *[user]* with your username**

    export CV2_PATH=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")/cv2 \
    sudo chown -R [user] CV2_PATH \
    sudo chgrp -R [user] CV2_PATH \
    sudo chmod -R 775 CV2_PATH

## Install MediaPipe

Install MediaPipe from PyPi:

    python -m pip install mediapipe

## Install LabGraph and Test

Install LabGraph from PyPi:

    python -m pip install labgraph

`cd` into your LabGraph installation, assuming you've installed it in your home directory:

    cd ~/labgraph/devices/webcam

Make sure PoseVis with GStreamer integration works:

    python -m pose_vis.pose_vis --sources "videotestsrc ! video/x-raw, width=1280, height=720, framerate=30/1, format=BGR ! appsink"

If all is well, you're now finished. Check [Using PoseVis](readme.md#using-posevis) for more usage examples. Enjoy using PoseVis!

