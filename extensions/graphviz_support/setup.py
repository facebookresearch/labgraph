#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="graphviz_support",
    version="1.0.0",
    description="Graphviz Extension For LabGraph",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "labgraph>=1.0.2",
        "graphviz==0.19.1",
    ],
)
