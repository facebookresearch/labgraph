#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup

setup(
    name = "hand_tracking_utility",
    version = "1.0.0",
    description = "Example hand tracking estimation visualizaion using LabGraph and Mediapipe",
    packages = find_packages(),
    python_requires = ">=3.6",
    install_requires = [
        "labgraph==2.0.0",
        "opencv-python>=4.6.0",
        "mediapipe>=0.8.11"])