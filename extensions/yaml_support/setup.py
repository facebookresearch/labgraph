#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup

setup(
    name="yaml_support",
    version="1.0.0",
    description="A LabgraphUnits-YAML parser",
    packages=find_packages(),
    python_requires=">=3.6, <3.7",
    install_requires=[
        "typed-ast==1.4.3",
        "PyYAML==6.0",
        "numpy==1.16.4",
    ],
)
