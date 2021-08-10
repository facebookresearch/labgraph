#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="labgraph_viz",
    version="1.0.0",
    description="Some useful visualizations for labgraph",
    packages=find_packages(),
    python_requires=">=3.6, <3.7",
    install_requires=[
        "dataclasses==0.6",
        "labgraph>=1.0.2",
        "matplotlib==3.1.1",
        "numpy==1.16.4",
        "PyQt5-sip==12.8.1",
        "pyqtgraph==0.11.1",
    ],
)
