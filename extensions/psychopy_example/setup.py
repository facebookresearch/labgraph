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
        # psychopy does not enforce versions, causing conflicts with labgraph deps.
        # Forcing specific versions at install time should help mitigate this issue.
        "cython",
        "scipy==1.5.4",
        "pandas==0.25.1",
        "xarray==0.16.2",
        "moviepy==1.0.1",
        "pyglet==1.5.16",
        # Actual dependencies for this package
        "importlib-resources~=5.2",
        "labgraph~=1.0.1",
        "psychopy~=3.2.4",
    ],
)
