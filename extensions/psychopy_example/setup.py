#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="psychopy_example",
    version="1.0.0",
    description="A psychopy experiment example for labgraph",
    packages=find_packages(),
    package_data = {
        "": ["images/*.png"]
    },
    python_requires=">=3.6, <3.7",
    install_requires=[
        "labgraph~=1.0",
        "psychopy~=3.2.4",
    ],
)
