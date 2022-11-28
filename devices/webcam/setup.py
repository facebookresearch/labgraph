#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import os
from setuptools import find_packages, setup

# Use LabGraph 2.0.0 on Windows due to a package installation error
install_requires = ["labgraph==2.0.0"] if os.name == "nt" else ["labgraph>=2.0.1"]
# More information on MediaPipe installation can be found here: https://google.github.io/mediapipe/getting_started/install.html
install_requires.extend(["opencv-python>=4.6.0", "mediapipe>=0.8.11"])

setup(
    name = "pose_vis",
    version = "1.0.0",
    description = "Pose visualization with LabGraph and MediaPipe",
    packages = find_packages(),
    python_requires = ">=3.8",
    install_requires = install_requires)