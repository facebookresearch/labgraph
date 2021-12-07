#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from buck_ext import BuckExtension, buck_build_ext
from setuptools import find_packages, setup

LIBRARY_EXTENSIONS = [
    BuckExtension(
        name="cthulhubindings",
        target="//:cthulhubindings#default,shared",
    ),
    BuckExtension(
        name="labgraph_cpp",
        target="//:labgraph_cpp_bindings#default,shared",
    ),
    BuckExtension(
        name="MyCPPNodes",
        target="//:MyCPPNodes#default,shared",
    ),
]


setup(
    name="labgraph",
    version="2.0.0",
    description="Research-friendly framework for in-lab experiments",
    long_description="LabGraph is a Python framework for rapidly prototyping experimental " +
                "systems for real-time streaming applications. " +
                "It is particularly well-suited to real-time neuroscience, " +
                "physiology and psychology experiments.",
    url="https://github.com/facebookresearch/labgraph",
    license="MIT",
    keywords="python streaming framework, reality lab, neuroscience, physiology, psychology",
    packages=find_packages(),
    package_data={"labgraph": ["tests/mypy.ini"]},
    python_requires=">=3.6",
    ext_modules=LIBRARY_EXTENSIONS,
    cmdclass={"build_ext": buck_build_ext},
    install_requires=[
        "appdirs>=1.4.4",
        "click>=7.1.2",
        "h5py>=3.3.0",
        "matplotlib>=3.1.2",
        "mypy>=0.910",
        "numpy>=1.19.5",
        "psutil>=5.6.7",
        "pytest>=3.10.1",
        "pytest_mock>=2.0.0",
        "pyzmq>=19.0.2",
        "typeguard>=2.10.0",
        "typing_extensions>=3.7.4",
        "websockets>=8.1",
        "yappi>=1.2.5",
    ],
)
