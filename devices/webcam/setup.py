#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup

setup(
    name = "pose_vis",
    version = "1.0.0",
    description = "Pose visualization with LabGraph and MediaPipe",
    packages = find_packages(),
    python_requires = ">=3.8",
    install_requires = [
        # On Windows, LabGraph 2.0.1 gives a ModuleNotFound error relating to 'buck_ext'
        # However, on Linux, LabGraph 2.0.0 gives this error
        # If installing on Linux change LabGraph's version to 2.0.1
        "labgraph==2.0.0",
        "opencv-python>=4.6.0",
        "mediapipe>=0.8.11"])