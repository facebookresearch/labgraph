# Windows GStreamer Guide

In this guide we will install GStreamer and build OpenCV with GStreamer support. This guide uses Windows 11 21H2 and assumes x64 archiecture but it should work on other Windows versions as well.

## Install GStreamer

Download and install the [latest development and runtime versions](https://gstreamer.freedesktop.org/download/) of GStreamer.

## Install CMake

Download and install the **3.24.3** release of [CMake](https://cmake.org/download/). (**Important:** OpenCV 4.6.0 is not compatible with CMake 3.25.0)

## Install Visual Studio 2019 Build Tools

Download and install [Visual Studio 2019 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019).

## Build OpenCV

Create a virtual environment for use with PoseVis:

    cd %HOMEPATH% && python -m venv .venv && call .venv\Scripts\activate

We'll be building and installing OpenCV and OpenCV Contrib 4.6.0. Clone the branches:

    git clone -b 4.6.0 --single-branch https://github.com/opencv/opencv.git && git clone -b 4.6.0 --single-branch https://github.com/opencv/opencv_contrib.git

Create a build directory for OpenCV and `cd` into it:

    md opencv\build && cd opencv\build

Set some environment variables for Python support: this looks confusing but all it does is define `PYTHON_INCLUDE_PATH`, `PYTHON_PACKAGES_PATH`, and `PYTHON_LIB_PATH` in the current environment

    FOR /F "tokens=* USEBACKQ" %v IN (`python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())"`) do (SET PYTHON_INCLUDE_PATH=%v) && FOR /F "tokens=* USEBACKQ" %v IN (`python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`) do (SET PYTHON_PACKAGES_PATH=%v) && FOR /F "tokens=* USEBACKQ" %v IN (`python -c "import os; import sys; import sysconfig; pyver = sysconfig.get_config_var('py_version_nodot'); print(os.path.join(sys.path[3].replace('lib', 'libs'), f'python{pyver}.lib'))"`) do (SET PYTHON_LIB_PATH=%v)

Add GStreamer to the `PATH` variable:

    set PATH=%PATH%;%GSTREAMER_1_0_ROOT_MSVC_X86_64%bin && set PATH=%PATH%;%GSTREAMER_1_0_ROOT_MSVC_X86_64%lib && set PATH=%PATH%;%GSTREAMER_1_0_ROOT_MSVC_X86_64%

Install Numpy:

    python -m pip install numpy

Run CMake with the following config:

    cmake -G "Visual Studio 16 2019" -A x64 ../ -D CMAKE_CONFIGURATION_TYPES=Release -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules -D WITH_GSTREAMER=ON -D BUILD_EXAMPLES=OFF -D INSTALL_C_EXAMPLES=OFF -D INSTALL_PYTHON_EXAMPLES=OFF -D BUILD_opencv_python2=OFF -D PYTHON3_INCLUDE_DIR=%PYTHON_INCLUDE_PATH% -D PYTHON3_PACKAGES_PATH=%PYTHON_PACKAGES_PATH% -D PYTHON_LIBRARY=%PYTHON_LIB_PATH% -D BUILD_opencv_python3=ON -D WITH_VTK=OFF

Check GStreamer and Python3 status:

    ...

    --   Video I/O:                        
    --     GStreamer:                   YES (1.20.4)

    ...

    --   Python 3:
    --     Interpreter:                 C:/Users/das/.venv/Scripts/python.exe (ver 3.10.8)
    --     Libraries:                   C:/Python310/libs/python310.lib (ver 3.10.8)
    --     numpy:                       C:/Users/das/.venv/lib/site-packages/numpy/core/include (ver 1.23.5)
    --     install path:                C:/Users/das/.venv/Lib/site-packages/cv2/python-3.10

    ...

If the configuration is correct, build and install OpenCV:

    cmake --build ./ --target INSTALL --config Release

## Install MediaPipe

Install MediaPipe from PyPi:

    python -m pip install mediapipe

## Install LabGraph and Test

Install LabGraph from PyPi:

    python -m pip install labgraph==2.0.0

`cd` into your LabGraph installation, assuming you've installed it in your home directory:

    cd %HOMEPATH%\labgraph\devices\webcam

Make sure PoseVis with GStreamer integration works:

    python -m pose_vis.pose_vis --sources "videotestsrc ! video/x-raw, width=1280, height=720, framerate=30/1, format=BGR ! appsink"

If all is well, you're now finished. Check [Using PoseVis](readme.md#using-posevis) for more usage examples. Enjoy using PoseVis!