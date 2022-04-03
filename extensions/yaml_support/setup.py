#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup

setup(
    name="yaml_support",
    version="1.0.0",
    description="A LabgraphUnits-YAML parser",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "labgraph>=1.0.2",
        "numpy>=1.21",
        "PyYAML==6.0",
        "StrEnum==0.4.7",
        "typed_ast>=1.4.3",
        "websockets"
    ],
)
