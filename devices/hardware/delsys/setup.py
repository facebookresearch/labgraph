#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="labgraph_delsys",
    version="1.0.0",
    description="Node for Delsys EMG sensor system in labgraph",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "labgraph>=1.0.2",
        "pythonnet",
    ],
)
