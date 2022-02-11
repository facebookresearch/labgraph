#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="labgraph_viz",
    version="1.0.0",
    description="Some useful visualizations for labgraph",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "dataclasses",
        "labgraph",
        "matplotlib",
        "numpy",
        "PyQt5",
        "pyqtgraph",
    ],
)
