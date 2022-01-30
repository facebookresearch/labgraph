#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup

setup(
    name="graphviz_support",
    version="1.0.0",
    description="LabGraph Monitor Improvement - Graphviz for LabGraph graphs",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "labgraph==1.0.2",
        "numpy==1.16.4",
        "graphviz==0.19.1",
        "matplotlib==3.1.1",
    ],
)
