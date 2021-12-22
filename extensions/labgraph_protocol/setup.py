#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from setuptools import find_packages, setup


setup(
    name="labgraph_protocol",
    version="1.0.0",
    description="Framework for creating experiment protocols in labgraph",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "dataclasses==0.6",
        "labgraph>=2.0.0",
        "PyQt5-sip==4.19.18",
        "PyQt5==5.13.0",
    ],
    include_package_data=True,
)
